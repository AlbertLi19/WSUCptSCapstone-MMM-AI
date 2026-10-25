"""Threshold detector regressions using curves with known event locations."""

import numpy as np
import pandas as pd
import pytest

from analysis_scripts.popin_locator import (
    InvalidDataError,
    analyze_file,
    calculate_derivatives,
    calculate_threshold,
    find_first_popin,
    find_flat_load_regions,
    get_loading_section,
    get_popin_candidates,
    load_data,
    validate_file,
)


def test_reads_instrument_header_bom_and_uppercase_extension(write_popin_curve):
    path = write_popin_curve(name="curve.TXT")
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    frame = load_data(path)
    assert list(frame.columns) == ["Depth_nm", "Load_uN", "Time_s", "Dis_V", "Force_V"]
    assert frame.shape == (120, 5)
    assert list(frame.index) == list(range(120))
    np.testing.assert_allclose(frame.iloc[60], [60, 120, 0.6, 0, 0])


@pytest.mark.parametrize("kind, message", [
    ("missing", "does not exist"),
    ("directory", "does not exist"),
    ("extension", "Invalid file type"),
    ("empty", "empty"),
])
def test_file_validation(tmp_path, kind, message):
    path = tmp_path / ("curve.csv" if kind == "extension" else "curve.txt")
    if kind == "directory":
        path.mkdir()
    elif kind != "missing":
        path.write_text("" if kind == "empty" else "some data")
    with pytest.raises(InvalidDataError, match=message):
        validate_file(path)


@pytest.mark.parametrize("value, message", [
    ("invalid", "nonnumeric"), ("", "missing"), ("nan", "missing"),
    ("inf", "infinite"), ("-inf", "infinite"),
])
@pytest.mark.parametrize("column", [0, 1, 2, 3, 4])
def test_invalid_measurements_in_any_column(write_popin_curve, value, message, column):
    path = write_popin_curve()
    lines = path.read_text().splitlines()
    row = lines[62].split("\t")
    row[column] = value
    lines[62] = "\t".join(row)
    path.write_text("\n".join(lines))
    with pytest.raises(InvalidDataError, match=message):
        load_data(path)


@pytest.mark.parametrize("contents, message", [
    ("Depth,Load,Time,Displacement,Force\n1,2,3,4,5", "Incorrect file format"),
    ("Depth\tLoad\tTime\tDisplacement\tForce\n", "no experimental measurements"),
    ("Depth\tLoad\tTime\tDisplacement\n1\t2\t3\t4", "Incorrect file format"),
])
def test_invalid_headers_and_missing_data(tmp_path, contents, message):
    path = tmp_path / "bad.txt"
    path.write_text(contents)
    with pytest.raises(InvalidDataError, match=message):
        load_data(path)


def test_minimum_measurement_boundary(write_popin_curve):
    with pytest.raises(InvalidDataError, match="at least 70"):
        analyze_file(write_popin_curve(points=69))
    assert len(analyze_file(write_popin_curve(points=70))["loading"]) == 70


@pytest.mark.parametrize("change", [0, -0.01])
def test_nonincreasing_time_rejected(write_popin_curve, change):
    times = np.arange(120) / 100
    times[60] = times[59] + change
    with pytest.raises(InvalidDataError, match="strictly increasing"):
        load_data(write_popin_curve(time=times))


@pytest.mark.parametrize("column, message", [("Depth (nm)", "depth"), ("Load (uN)", "load")])
def test_constant_measurement_axis_rejected(write_popin_curve, column, message):
    path = write_popin_curve()
    frame = pd.read_csv(path, sep="\t", skiprows=1)
    frame[column] = 1
    frame.to_csv(path, sep="\t", index=False)
    with pytest.raises(InvalidDataError, match=message):
        load_data(path)


def test_loading_includes_first_maximum_and_excludes_unloading(write_popin_curve):
    loads = np.r_[np.arange(90), np.arange(89, 59, -1)]
    result = analyze_file(write_popin_curve(load=loads, jumps=[(100, 50)]))
    assert len(result["data"]) == 120
    assert len(result["loading"]) == 90
    assert result["loading"].iloc[-1]["Load_uN"] == 89
    assert result["pop_index"] is None
    assert result["candidate_count"] == 0


def test_short_loading_section_rejected(write_popin_curve):
    loads = np.r_[np.arange(69), np.arange(67, 16, -1)]
    with pytest.raises(InvalidDataError, match="70 loading measurements"):
        analyze_file(write_popin_curve(load=loads))


def test_loading_without_depth_variation_rejected(write_popin_curve):
    frame = load_data(write_popin_curve())
    frame.loc[:89, "Depth_nm"] = 0
    frame.loc[90:, "Load_uN"] = 0
    with pytest.raises(InvalidDataError, match="no depth variation"):
        get_loading_section(frame)


@pytest.mark.parametrize("jumps, expected", [
    ([], []), ([(80, 20)], [80]), ([(80, 20), (100, 50)], [80, 100]),
    ([(49, 20)], []), ([(50, 20)], [50]), ([(119, 20)], [119]),
    ([(80, -20)], []),
])
def test_known_events_and_search_boundaries(write_popin_curve, jumps, expected):
    path = write_popin_curve(jumps=jumps)
    result = analyze_file(path)
    assert result["file_path"] == path
    assert result["threshold"] == pytest.approx(1)
    assert result["candidate_count"] == len(expected)
    assert result["pop_index"] == (expected[0] if expected else None)
    assert list(get_popin_candidates(result["loading"], result["threshold"]).index) == expected
    assert find_first_popin(result["loading"], result["threshold"]) == result["pop_index"]


def test_depth_jumps_require_positive_load_change(write_popin_curve):
    loads = np.arange(120, dtype=float) * 2
    loads[80] = loads[79]  # Plateau at one jump.
    loads[90] = loads[89] - 1  # Falling load at another.
    result = analyze_file(write_popin_curve(load=loads, jumps=[(80, 20), (90, 20), (100, 20)]))
    assert result["candidate_count"] == 1
    assert result["pop_index"] == 100
    assert np.isnan(result["loading"].loc[[80, 90], "dDepth_dLoad"]).all()


def test_derivatives_preserve_input_and_measure_physical_changes(write_popin_curve):
    frame = load_data(write_popin_curve(jumps=[(80, 20)]))
    original = frame.copy(deep=True)
    derivatives = calculate_derivatives(frame)
    pd.testing.assert_frame_equal(frame, original)
    assert np.isnan(derivatives.loc[0, "dDepth_nm"])
    assert derivatives.loc[80, "dDepth_nm"] == 21
    assert derivatives.loc[80, "dLoad_uN"] == 2
    assert derivatives.loc[80, "dDepth_dLoad"] == 10.5


def test_robust_threshold_resists_one_large_outlier():
    baseline = np.tile([1., 2., 3., 4., 5.], 9)
    baseline[-1] = 1000
    frame = pd.DataFrame({"dDepth_nm": np.r_[np.full(50, 9999.), baseline]})
    assert calculate_threshold(frame) == pytest.approx(3 + 8 * 1.4826)


def test_threshold_requires_enough_finite_baseline_points():
    with pytest.raises(InvalidDataError, match="Insufficient data"):
        calculate_threshold(pd.DataFrame({"dDepth_nm": np.ones(69)}))
    with np.errstate(invalid="ignore"), pytest.raises(InvalidDataError, match="valid pop-in threshold"):
        calculate_threshold(pd.DataFrame({"dDepth_nm": np.r_[np.zeros(50), np.full(20, np.inf)]}))


def test_flat_load_without_popin_candidate_is_ignored(write_popin_curve):
    increments = np.full(120, 2.)
    increments[80:85] = 0
    result = analyze_file(write_popin_curve(load=np.cumsum(increments)))
    assert result["candidate_count"] == 0
    assert result["flat_regions"] == []


def test_only_candidate_plateau_is_refined(write_popin_curve):
    increments = np.full(120, 2.)
    increments[75:85] = 0.1
    increments[100:110] = 0  # Unrelated flat region must not become an event.
    result = analyze_file(write_popin_curve(load=np.cumsum(increments), jumps=[(80, 20)]))
    assert result["candidate_count"] == 1
    assert result["flat_slope_threshold"] == pytest.approx(0.4)
    region, = result["flat_regions"]
    assert region["candidate_indices"] == [80]
    assert (region["start_index"], region["end_index"]) == (74, 84)
    assert region["start_depth_nm"] == 74
    assert region["end_depth_nm"] == 104
    assert region["start_time_s"] == pytest.approx(0.74)
    assert region["end_time_s"] == pytest.approx(0.84)


@pytest.mark.parametrize("jumps, expected", [
    ([(80, 20)], [(79, 80)]),
    ([(80, 20), (100, 50)], [(79, 80)]),
    ([(50, 20), (119, 20)], [(49, 50)]),
])
def test_isolated_popin_keeps_candidate_interval(write_popin_curve, jumps, expected):
    result = analyze_file(write_popin_curve(jumps=jumps))
    assert [(r["start_index"], r["end_index"]) for r in result["flat_regions"]] == expected


def test_candidates_on_same_plateau_share_region(write_popin_curve):
    increments = np.full(120, 2.)
    increments[80:85] = 0.1
    result = analyze_file(write_popin_curve(load=np.cumsum(increments), jumps=[(81, 20), (83, 20)]))
    region, = result["flat_regions"]
    assert result["candidate_count"] == 2
    assert result["pop_index"] == 81
    assert region["candidate_indices"] == [81]
    assert (region["start_index"], region["end_index"]) == (79, 84)


def test_flat_region_flushes_at_end_and_splits_on_depth_reversal(write_popin_curve):
    frame = load_data(write_popin_curve())
    frame.loc[110:, "Load_uN"] = frame.loc[109, "Load_uN"]
    frame.loc[114, "Depth_nm"] = frame.loc[113, "Depth_nm"] - 1
    regions, _ = find_flat_load_regions(frame, frame.loc[[111, 116]])
    assert [(r["start_index"], r["end_index"]) for r in regions] == [(109, 113), (114, 119)]


def test_flat_regions_are_invariant_to_axis_units(write_popin_curve):
    increments = np.full(120, 2.)
    increments[80:85] = 0.1
    frame = load_data(write_popin_curve(load=np.cumsum(increments)))
    frame["Load_uN"] *= 1000
    frame["Depth_nm"] *= 0.001
    regions, threshold = find_flat_load_regions(frame, frame.loc[[82]])
    assert [(r["start_index"], r["end_index"]) for r in regions] == [(79, 84)]
    assert threshold == pytest.approx(400000)
