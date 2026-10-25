from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd


MULTIPLIER = 8
BASELINE_START = 50
MIN_POINTS = 70
MIN_BASELINE_POINTS = 20
FLAT_SLOPE_FRACTION = 0.2


class InvalidDataError(Exception):
    """Raised when a file contains invalid experimental data."""


def validate_file(file_path: Union[str, Path]) -> Path:
    file = Path(file_path)

    if not file.is_file():
        raise InvalidDataError("The selected file does not exist.")

    if file.suffix.lower() != ".txt":
        raise InvalidDataError("Invalid file type. Please select a .txt file.")

    if file.stat().st_size == 0:
        raise InvalidDataError("The selected file is empty.")

    return file


def load_data(file_path: Union[str, Path]) -> pd.DataFrame:
    file = validate_file(file_path)
    header_line = None

    with file.open("r", encoding="utf-8-sig", errors="replace") as data_file:
        for line_number, line in enumerate(data_file):
            if line_number >= 100:
                break

            columns = [column.strip().lower() for column in line.strip().split("\t")]

            if (
                len(columns) == 5
                and "depth" in columns[0]
                and "load" in columns[1]
                and "time" in columns[2]
                and ("disp" in columns[3] or "depth" in columns[3])
                and ("force" in columns[4] or "load" in columns[4])
            ):
                header_line = line_number
                break

    if header_line is None:
        raise InvalidDataError(
            "Incorrect file format. Expected five columns: "
            "Depth, Load, Time, Displacement, Force."
        )

    df = pd.read_csv(
        file,
        sep="\t",
        skiprows=header_line,
        encoding="utf-8-sig",
        encoding_errors="replace",
        on_bad_lines="error",
    )

    if len(df.columns) != 5:
        raise InvalidDataError("The file must contain exactly five data columns.")

    if df.empty:
        raise InvalidDataError("The file contains no experimental measurements.")

    df.columns = ["Depth_nm", "Load_uN", "Time_s", "Dis_V", "Force_V"]

    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df.isna().any().any():
        raise InvalidDataError(
            "The file contains missing or nonnumeric measurements."
        )

    if not np.isfinite(df.to_numpy(dtype=float)).all():
        raise InvalidDataError("The file contains infinite measurements.")

    if len(df) < MIN_POINTS:
        raise InvalidDataError(
            f"Insufficient data points. Found {len(df)}, but at least "
            f"{MIN_POINTS} are required."
        )

    time_difference = df["Time_s"].diff().iloc[1:]
    if not (time_difference > 0).all():
        raise InvalidDataError("Time measurements must be strictly increasing.")

    if df["Load_uN"].max() <= df["Load_uN"].min():
        raise InvalidDataError("Invalid load measurements. Load values do not vary.")

    if df["Depth_nm"].max() <= df["Depth_nm"].min():
        raise InvalidDataError("Invalid depth measurements. Depth values do not vary.")

    return df.reset_index(drop=True)


def get_loading_section(df: pd.DataFrame) -> pd.DataFrame:
    max_load_index = int(df["Load_uN"].idxmax())
    loading = df.iloc[: max_load_index + 1].copy()

    minimum_loading_points = BASELINE_START + MIN_BASELINE_POINTS
    if len(loading) < minimum_loading_points:
        raise InvalidDataError(
            "Insufficient data in the loading section. "
            f"At least {minimum_loading_points} loading measurements are required."
        )

    if loading["Depth_nm"].max() <= loading["Depth_nm"].min():
        raise InvalidDataError("The loading section contains no depth variation.")

    return loading


def calculate_derivatives(loading: pd.DataFrame) -> pd.DataFrame:
    loading = loading.copy()
    loading["dDepth_nm"] = loading["Depth_nm"].diff()
    loading["dLoad_uN"] = loading["Load_uN"].diff()

    valid_load_change = loading["dLoad_uN"].where(loading["dLoad_uN"] > 0, np.nan)
    loading["dDepth_dLoad"] = loading["dDepth_nm"] / valid_load_change

    return loading


def calculate_threshold(loading: pd.DataFrame) -> float:
    baseline_data = loading.iloc[BASELINE_START:]["dDepth_nm"].dropna()

    if len(baseline_data) < MIN_BASELINE_POINTS:
        raise InvalidDataError("Insufficient data to calculate the pop-in threshold.")

    baseline_array = baseline_data.to_numpy(dtype=float)
    median_change = float(np.median(baseline_array))
    mad = float(np.median(np.abs(baseline_array - median_change)))
    robust_std = float(1.4826 * mad)
    threshold = float(median_change + MULTIPLIER * robust_std)

    if not np.isfinite(threshold):
        raise InvalidDataError("Unable to calculate a valid pop-in threshold.")

    return threshold


def get_popin_candidates(loading: pd.DataFrame, threshold: float) -> pd.DataFrame:
    search_data = loading.iloc[BASELINE_START:]
    return search_data[
        (search_data["dDepth_nm"] > threshold) & (search_data["dLoad_uN"] > 0)
    ]


def find_first_popin(loading: pd.DataFrame, threshold: float) -> Optional[int]:
    candidates = get_popin_candidates(loading, threshold)
    if candidates.empty:
        return None

    return int(candidates.index[0])


def find_flat_load_regions(loading: pd.DataFrame, candidates: pd.DataFrame) -> tuple[list[dict], float]:
    """Refine threshold candidates by extending over adjacent flat-load steps.

    Each candidate starts with its preceding measurement and the candidate
    measurement. Extend left/right only while depth increases and the absolute
    load/depth slope is at most 20% of the median positive loading slope.
    An isolated candidate retains its original two-measurement interval.
    Candidates sharing the same flat interval are grouped together.
    """
    depth_change = loading["Depth_nm"].diff().to_numpy(dtype=float)
    load_change = loading["Load_uN"].diff().to_numpy(dtype=float)
    slopes = np.full(len(loading), np.nan)
    np.divide(load_change, depth_change, out=slopes, where=depth_change > 0)
    baseline = slopes[BASELINE_START:]
    positive = baseline[np.isfinite(baseline) & (baseline > 0)]
    if len(positive) == 0:
        if candidates.empty:
            return [], 0.0
        raise InvalidDataError("Unable to estimate a positive loading slope for flat-load detection.")
    slope_threshold = float(np.median(positive) * FLAT_SLOPE_FRACTION)
    flat = np.isfinite(slopes) & (np.abs(slopes) <= slope_threshold)
    flat[:BASELINE_START] = False

    regions = {}
    for candidate_index in candidates.index:
        seed = int(loading.index.get_loc(candidate_index))
        start, end = seed - 1, seed
        while start >= BASELINE_START and flat[start]:
            start -= 1
        while end + 1 < len(loading) and flat[end + 1]:
            end += 1
        key = (start, end)
        if key in regions:
            regions[key]["candidate_indices"].append(int(candidate_index))
            continue
        first, last = loading.iloc[start], loading.iloc[end]
        regions[key] = {
            "candidate_indices": [int(candidate_index)],
            "start_index": int(loading.index[start]),
            "end_index": int(loading.index[end]),
            "start_depth_nm": float(first["Depth_nm"]),
            "end_depth_nm": float(last["Depth_nm"]),
            "start_load_uN": float(first["Load_uN"]),
            "end_load_uN": float(last["Load_uN"]),
            "start_time_s": float(first["Time_s"]),
            "end_time_s": float(last["Time_s"]),
        }
    return list(regions.values()), slope_threshold


def analyze_file(file_path: Union[str, Path]) -> dict:
    file = validate_file(file_path)
    df = load_data(file)
    loading = calculate_derivatives(get_loading_section(df))
    threshold = calculate_threshold(loading)
    candidates = get_popin_candidates(loading, threshold)
    regions, flat_slope_threshold = find_flat_load_regions(loading, candidates.head(1))

    pop_index = None
    if not candidates.empty:
        pop_index = int(candidates.index[0])

    return {
        "file_path": file,
        "data": df,
        "loading": loading,
        "flat_regions": regions,
        "flat_slope_threshold": flat_slope_threshold,
        "threshold": threshold,
        "candidate_count": len(candidates),
        "pop_index": pop_index,
    }
