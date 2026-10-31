"""Exercise the real Qt background workflow without a display."""
import csv
import os
import time
import importlib.util
import joblib
import numpy as np
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton

from analysis_scripts import popin_ml
from analysis_scripts.popin_ml import DEFAULT_DATA, DEFAULT_MODEL
from analysis_scripts.popin_locator import analyze_file
from matplotlib.backend_bases import MouseEvent

# Load the actual tab without importing unrelated segmentation/controller code
# eagerly pulled in by views/__init__.py.
view_path = Path(__file__).resolve().parents[1] / "src/app/views/popin_locator_view.py"
spec = importlib.util.spec_from_file_location("popin_locator_view_test", view_path)
view_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view_module)
PopInLocatorView = view_module.PopInLocatorView


def wait_for_worker(app, window):
    deadline = time.monotonic() + 15
    while window.model_busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert not window.model_busy, "Background operation did not finish"


@pytest.fixture
def gui():
    app = QApplication.instance() or QApplication([])
    window = PopInLocatorView()
    yield app, window
    wait_for_worker(app, window)
    window.close()


@pytest.mark.skipif(not DEFAULT_MODEL.exists(), reason="Train a model before the GUI integration test")
def test_load_run_and_cancel(gui, monkeypatch):
    app, window = gui
    path = DEFAULT_DATA / "SiC-4H-OFF" / "SiC-4H 0000.txt"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    assert not window._run_model_button.isEnabled()
    assert [button.text() for button in window.findChildren(QPushButton)] == [
        "Select File", "Run Detection", "Train Shape Model", "Run Model", "Save Detection Results", "Save to CSV"]
    window._select_file_button.click()
    wait_for_worker(app, window)
    assert window._run_model_button.isEnabled()
    window._run_model_button.click()
    assert not window._run_button.isEnabled()
    assert not window._create_model_button.isEnabled()
    wait_for_worker(app, window)
    assert "Prediction complete" in window._model_label.text()
    assert "Method: Machine learning" in window._results_text.toPlainText()
    assert window._figure.axes[0].collections
    assert not window._figure.axes[0].texts
    model_ax = window._figure.axes[0]
    assert len(model_ax.lines) == 1
    model_curve = model_ax.lines[0].get_xydata().copy()
    expected_loading = popin_ml.loading(popin_ml.load_curve(path))
    np.testing.assert_allclose(model_curve, expected_loading[:, :2])
    model_limits = (model_ax.get_xlim(), model_ax.get_ylim())
    model_title = model_ax.get_title()
    window._run_button.click()
    assert "Method: Threshold algorithm" in window._results_text.toPlainText()
    assert window._figure.axes[0].lines
    algorithm_ax = window._figure.axes[0]
    np.testing.assert_allclose(algorithm_ax.lines[0].get_xydata(), model_curve)
    np.testing.assert_allclose((algorithm_ax.get_xlim(), algorithm_ax.get_ylim()), model_limits)
    assert algorithm_ax.get_title() == model_title
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: ("", ""))
    window._select_file_button.click()
    assert window._selected_file == path


def test_invalid_file_reports_error(gui, monkeypatch, tmp_path):
    app, window = gui
    path = tmp_path / "empty.txt"
    path.write_text("")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window._select_file_button.click()
    # Selection is shared by both methods; each validates on execution.
    window._model = popin_ml.load_model()
    window._update_buttons()
    window._run_model_button.click()
    wait_for_worker(app, window)
    assert "Expected tab-separated" in window._results_text.toPlainText()
    assert not window._figure.axes[0].lines
    window._run_button.click()
    assert "empty" in window._results_text.toPlainText()


def test_algorithm_available_without_model(gui, monkeypatch):
    app, window = gui
    window._model = None
    path = DEFAULT_DATA / "SiC-4H-OFF" / "SiC-4H 0000.txt"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window._select_file_button.click()
    assert window._run_button.isEnabled()
    assert not window._run_model_button.isEnabled()
    assert window._create_model_button.isEnabled()
    window._run_button.click()
    assert "Method: Threshold algorithm" in window._results_text.toPlainText()


def test_create_model_worker_updates_controls(gui, monkeypatch, write_popin_curve):
    app, window = gui
    editable_curve(window, write_popin_curve)
    assert window._save_results_button.isEnabled()
    bundle = popin_ml.load_model()
    window._model = None
    monkeypatch.setattr(popin_ml, "train", lambda: bundle["report"])
    monkeypatch.setattr(popin_ml, "load_model", lambda: bundle)
    window._create_model_button.click()
    assert window.model_busy
    assert not window._select_file_button.isEnabled()
    wait_for_worker(app, window)
    assert window._model is bundle
    assert "Shape model trained" in window._results_text.toPlainText()
    assert not window._save_results_button.isEnabled()
    assert window._create_model_button.isEnabled()
    assert not window._run_model_button.isEnabled()  # Still needs a selected file.


def test_training_failure_restores_controls(gui, monkeypatch):
    app, window = gui
    def fail():
        raise popin_ml.DataError("Missing training workbook")
    monkeypatch.setattr(popin_ml, "train", fail)
    window._create_model_button.click()
    wait_for_worker(app, window)
    assert "Missing training workbook" in window._results_text.toPlainText()
    assert window._select_file_button.isEnabled()
    assert window._create_model_button.isEnabled()


def test_reopened_tab_automatically_loads_saved_model(gui, monkeypatch, tmp_path):
    app, window = gui
    bundle = popin_ml.load_model()
    bundle["report"]["persistence_test"] = "saved model"
    saved = tmp_path / "model.joblib"
    joblib.dump(bundle, saved)
    monkeypatch.setattr(popin_ml, "DEFAULT_MODEL", saved)
    reopened = PopInLocatorView()
    try:
        assert reopened._model["report"]["persistence_test"] == "saved model"
        assert "model ready" in reopened._model_label.text()
    finally:
        reopened.close()


@pytest.mark.parametrize("plateau", [False, True])
def test_threshold_results_and_plot_for_known_curve(gui, monkeypatch, write_popin_curve, plateau):
    app, window = gui
    increments = np.full(120, 2.)
    if plateau:
        increments[80:85] = 0.1
    path = write_popin_curve(load=np.cumsum(increments), jumps=[(80, 20)] if plateau else [])
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window._select_file_button.click()
    window._run_button.click()
    text = window._results_text.toPlainText()
    assert "Method: Threshold algorithm" in text
    assert f"Candidate regions: {int(plateau)}" in text
    axis = window._figure.axes[0]
    if not plateau:
        assert len(axis.lines) == 1
        assert "No pop-in candidates exceeded the threshold" in text
        assert not axis.collections
    else:
        assert "Start data point: 79" in text
        assert "End data point: 84" in text
        assert "Depth span: 25.000 nm" in text
        assert "Load change: 0.500 uN" in text
        assert "dy/dx (Δload/Δdepth): 0.020000 uN/nm" in text
        np.testing.assert_allclose(axis.lines[1].get_xydata(), [[79, 160]] + [[i + 20, 160 + (i - 79) * 0.1] for i in range(80, 85)])
        np.testing.assert_allclose(axis.collections[0].get_offsets(), [[79, 160]])
        np.testing.assert_allclose(axis.collections[1].get_offsets(), [[104, 160.5]])


def test_algorithm_counts_all_candidates_and_displays_only_first_region(gui, write_popin_curve):
    _, window = gui
    window._selected_file = write_popin_curve(jumps=[(80, 20), (100, 50)])
    window._run_detection()
    text = window._results_text.toPlainText()
    assert "Pop-in candidates: 2" in text
    assert "Candidate regions: 1" in text
    assert "Pop-in data points: 80" in text
    assert "Candidate region 2" not in text
    assert len(window._region_artists) == 1
    axis = window._figure.axes[0]
    np.testing.assert_allclose(axis.lines[1].get_xydata(), [[79, 158], [100, 160]])
    assert len(axis.collections) == 2


def test_algorithm_points_are_marked_without_labels_and_survive_drag(gui, write_popin_curve):
    _, window = gui
    result = editable_curve(window, write_popin_curve)
    axis = window._figure.axes[0]
    assert not axis.texts
    for line in axis.lines:
        assert line.get_marker() == "o"
        assert line.get_markersize() >= 4
    np.testing.assert_allclose(axis.lines[0].get_xydata(), result["loading"][["Depth_nm", "Load_uN"]])
    plot_mouse(window, "button_press_event", 78, 158, button=1)
    plot_mouse(window, "motion_notify_event", 77, 156, button=1)
    plot_mouse(window, "button_release_event", 77, 156, button=1)
    assert result["flat_regions"][0]["start_index"] == 77
    assert axis.lines[1].get_marker() == "o"
    assert not axis.texts


def test_slope_percentage_control_applies_on_detection_and_is_reported(gui, write_popin_curve):
    _, window = gui
    increments = np.full(120, 2.)
    increments[75:85] = 0.6
    window._selected_file = write_popin_curve(load=np.cumsum(increments), jumps=[(80, 20)])
    assert window._slope_percentage.value() == 20
    window._run_detection()
    assert "Start data point: 79" in window._results_text.toPlainText()
    window._slope_percentage.setValue(50)
    window._run_detection()
    text = window._results_text.toPlainText()
    assert "Endpoint extension: at most 50% of median positive loading slope" in text
    assert "Start data point: 74" in text
    assert "End data point: 84" in text
    # Changing the input alone must not change the percentage saved with results.
    window._slope_percentage.setValue(30)
    window._display_results(window._threshold_result)
    assert "at most 50%" in window._results_text.toPlainText()


def test_selecting_new_file_and_error_clear_previous_results(gui, monkeypatch, write_popin_curve, tmp_path):
    app, window = gui
    loads = np.cumsum(np.r_[np.full(80, 2.), np.zeros(5), np.full(35, 2.)])
    path = write_popin_curve(load=loads, jumps=[(79, 20)])
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window._select_file_button.click()
    window._run_button.click()
    assert window._figure.axes[0].collections
    path = tmp_path / "empty.txt"
    path.write_text("")
    window._select_file_button.click()
    assert "Ready." in window._results_text.toPlainText()
    assert "First pop-in" not in window._results_text.toPlainText()
    assert not window._figure.axes[0].lines
    assert not window._figure.axes[0].collections
    window._run_button.click()
    assert "Data error" in window._results_text.toPlainText()
    assert "empty" in window._results_text.toPlainText()
    assert not window._figure.axes[0].collections
    assert window._run_button.isEnabled()
    # A valid file still works after the error.
    path = write_popin_curve(name="recovered.txt")
    window._select_file_button.click()
    window._run_button.click()
    assert "No pop-in candidates exceeded the threshold" in window._results_text.toPlainText()


def test_prediction_failure_recovers_and_empty_predictions_clear_markers(gui, monkeypatch, write_popin_curve):
    app, window = gui
    loads = np.cumsum(np.r_[np.full(80, 2.), np.zeros(5), np.full(35, 2.)])
    path = write_popin_curve(load=loads, jumps=[(79, 20)])
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
    window._model = object()  # Exercise worker/UI behavior independently of model artifacts.
    window._select_file_button.click()
    window._run_button.click()
    assert window._figure.axes[0].collections

    def fail(*args):
        raise popin_ml.DataError("Prediction failed for test curve")

    monkeypatch.setattr(popin_ml, "predict", fail)
    window._run_model_button.click()
    wait_for_worker(app, window)
    assert "Prediction failed for test curve" in window._results_text.toPlainText()
    assert not window._figure.axes[0].lines
    assert not window._figure.axes[0].collections
    assert all(button.isEnabled() for button in (
        window._select_file_button, window._run_button, window._create_model_button, window._run_model_button))
    assert not window._save_results_button.isEnabled()
    monkeypatch.setattr(popin_ml, "predict", lambda *args: [])
    window._run_model_button.click()
    wait_for_worker(app, window)
    assert "Pop-in candidates: 0" in window._results_text.toPlainText()
    assert "No pop-in candidates exceed the learned threshold" in window._results_text.toPlainText()
    assert len(window._figure.axes[0].lines) == 1
    assert not window._figure.axes[0].collections


def test_unreadable_saved_model_keeps_threshold_detection_available(gui, monkeypatch, write_popin_curve):
    app, window = gui
    path = write_popin_curve()
    monkeypatch.setattr(popin_ml, "DEFAULT_MODEL", path)  # Existing file, invalid model.

    def fail():
        raise popin_ml.DataError("Unsupported model")

    monkeypatch.setattr(popin_ml, "load_model", fail)
    reopened = PopInLocatorView()
    try:
        assert "Saved model could not be loaded" in reopened._model_label.text()
        assert reopened._create_model_button.isEnabled()
        monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), ""))
        reopened._select_file_button.click()
        assert not reopened._run_model_button.isEnabled()
        reopened._run_button.click()
        assert "Method: Threshold algorithm" in reopened._results_text.toPlainText()
    finally:
        reopened.close()


def plot_mouse(window, name, depth, load, **kwargs):
    axis = window._figure.axes[0]
    x, y = axis.transData.transform((depth, load))
    event = MouseEvent(name, window._canvas, x, y, **kwargs)
    window._canvas.callbacks.process(name, event)


def editable_curve(window, write_popin_curve):
    loads = np.cumsum(np.r_[np.full(80, 2.), np.zeros(5), np.full(35, 2.)])
    result = analyze_file(write_popin_curve(load=loads, jumps=[(79, 20)]))
    window._display_results(result)
    window._draw_result_plot(result)
    window._canvas.draw()
    return result


def test_scroll_zoom_and_toolbar_home(gui, write_popin_curve):
    _, window = gui
    editable_curve(window, write_popin_curve)
    axis = window._figure.axes[0]
    original = (axis.get_xlim(), axis.get_ylim())
    plot_mouse(window, "scroll_event", 80, 160, button="up", step=1)
    assert np.ptp(axis.get_xlim()) == pytest.approx(np.ptp(original[0]) / 1.2)
    assert np.ptp(axis.get_ylim()) == pytest.approx(np.ptp(original[1]) / 1.2)
    plot_mouse(window, "scroll_event", 80, 160, button="down", step=-1)
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), original)
    plot_mouse(window, "scroll_event", 80, 160, button="up", step=2)
    window._toolbar.home()
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), original)


def test_rerun_preserves_view_and_back_forward_home_history(gui, write_popin_curve):
    _, window = gui
    result = editable_curve(window, write_popin_curve)
    window._selected_file = result["file_path"]
    axis = window._figure.axes[0]
    original = (axis.get_xlim(), axis.get_ylim())
    plot_mouse(window, "scroll_event", 80, 160, button="up", step=1)
    first_zoom = (axis.get_xlim(), axis.get_ylim())
    plot_mouse(window, "scroll_event", 80, 160, button="up", step=2)
    second_zoom = (axis.get_xlim(), axis.get_ylim())
    window._toolbar.back()
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), first_zoom)
    window._slope_percentage.setValue(50)
    window._run_detection()
    assert window._figure.axes[0] is axis
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), first_zoom)
    assert "at most 50%" in window._results_text.toPlainText()
    assert len(axis.lines) == 2  # No duplicate curves or endpoint markers.
    assert len(axis.collections) == 2
    window._toolbar.forward()
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), second_zoom)
    window._toolbar.back()
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), first_zoom)
    window._toolbar.home()
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), original)


def test_new_file_resets_view_and_navigation_history(gui, write_popin_curve):
    _, window = gui
    editable_curve(window, write_popin_curve)
    previous_axis = window._figure.axes[0]
    plot_mouse(window, "scroll_event", 80, 160, button="up", step=2)
    window._selected_file = write_popin_curve(name="other.txt", load=np.arange(120) * 200)
    window._run_detection()
    axis = window._figure.axes[0]
    assert axis is not previous_axis
    limits = (axis.get_xlim(), axis.get_ylim())
    assert axis.get_ylim()[1] > 20000
    window._toolbar.back()
    window._toolbar.forward()
    window._toolbar.home()
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), limits)


def test_drag_both_endpoints_snaps_and_updates_before_release(gui, write_popin_curve):
    _, window = gui
    result = editable_curve(window, write_popin_curve)
    axis = window._figure.axes[0]
    plot_mouse(window, "scroll_event", 80, 160, button="up", step=1)
    limits = (axis.get_xlim(), axis.get_ylim())
    # Move to a position off the line; snap to the nearest measured point.
    plot_mouse(window, "button_press_event", 78, 158, button=1)
    plot_mouse(window, "motion_notify_event", 77, 156.2, button=1)
    region = result["flat_regions"][0]
    assert region["start_index"] == 77
    assert region["start_time_s"] == pytest.approx(0.77)
    assert "Start data point: 77" in window._results_text.toPlainText()
    assert "manually adjusted" in window._results_text.toPlainText()
    np.testing.assert_allclose(axis.collections[0].get_offsets(), [[77, 156]])
    plot_mouse(window, "button_release_event", 77, 156, button=1)
    plot_mouse(window, "button_press_event", 104, 160, button=1)
    plot_mouse(window, "motion_notify_event", 107, 166, button=1)
    assert region["end_index"] == 87
    assert not axis.texts
    assert "End data point: 87" in window._results_text.toPlainText()
    assert "Depth span: 30.000 nm" in window._results_text.toPlainText()
    assert "Load change: 10.000 uN" in window._results_text.toPlainText()
    assert "dy/dx (Δload/Δdepth): 0.333333 uN/nm" in window._results_text.toPlainText()
    np.testing.assert_allclose(axis.collections[1].get_offsets(), [[107, 166]])
    np.testing.assert_allclose(axis.lines[1].get_xydata(), result["loading"].loc[77:87, ["Depth_nm", "Load_uN"]])
    np.testing.assert_allclose((axis.get_xlim(), axis.get_ylim()), limits)
    plot_mouse(window, "button_release_event", 107, 166, button=1)
    plot_mouse(window, "motion_notify_event", 90, 172)
    assert region["end_index"] == 87


def test_endpoint_order_pan_mode_and_clearing_edit_state(gui, write_popin_curve):
    _, window = gui
    result = editable_curve(window, write_popin_curve)
    window._toolbar.pan()
    plot_mouse(window, "button_press_event", 78, 158, button=1)
    assert window._drag_endpoint is None

    plot_mouse(window, "button_release_event", 78, 158, button=1)
    window._toolbar.pan()
    plot_mouse(window, "button_press_event", 78, 158, button=1)
    plot_mouse(window, "motion_notify_event", 90, 172, button=1)
    assert result["flat_regions"][0]["start_index"] < result["flat_regions"][0]["end_index"]
    window._draw_empty_plot("New file")
    assert window._drag_endpoint is None
    assert window._threshold_result is None
    assert not window._region_artists
    # Model plots have zoom controls but no editable threshold endpoints.
    curve = result["loading"]
    window._draw_popin_plot(result["file_path"], curve["Depth_nm"], curve["Load_uN"], [])
    plot_mouse(window, "button_press_event", 78, 158, button=1)
    assert window._drag_endpoint is None


def test_toolbar_has_only_navigation_and_figure_save(gui):
    _, window = gui
    actions = {action.text() for action in window._toolbar.actions() if action.text()}
    assert actions == {"Home", "Back", "Forward", "Pan", "Zoom", "Save"}
    assert "configure_subplots" not in window._toolbar._actions
    assert "edit_parameters" not in window._toolbar._actions


def test_xy_cursor_uses_two_decimals_and_ticks_use_plain_notation(gui, write_popin_curve):
    _, window = gui
    editable_curve(window, write_popin_curve)
    axis = window._figure.axes[0]
    for value, expected in ((10000., "10000.00"), (0., "0.00"), (12.5, "12.50"),
                            (10000.12345678, "10000.12"),
                            (0.12345678, "0.12"), (-1234.56789, "-1234.57")):
        assert axis.format_xdata(value) == expected
        assert axis.format_ydata(value) == expected
        assert expected in axis.format_coord(80, value)
        assert expected in axis.format_coord(value, 160)
    axis.set_xlim(9999, 10001)
    axis.set_ylim(9999, 10001)
    window._canvas.draw()
    assert not axis.yaxis.get_offset_text().get_text()
    assert not axis.xaxis.get_offset_text().get_text()
    assert all("e" not in tick.get_text().lower() for tick in axis.get_yticklabels())
    assert all("e" not in tick.get_text().lower() for tick in axis.get_xticklabels())


def test_save_current_detection_results_including_drag_edits(gui, monkeypatch, write_popin_curve, tmp_path):
    _, window = gui
    assert not window._save_results_button.isEnabled()
    editable_curve(window, write_popin_curve)
    assert window._save_results_button.isEnabled()
    plot_mouse(window, "button_press_event", 78, 158, button=1)
    plot_mouse(window, "motion_notify_event", 77, 156, button=1)
    plot_mouse(window, "button_release_event", 77, 156, button=1)
    destination = tmp_path / "saved_results"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(destination), "Text Files (*.txt)"))
    window._save_results_button.click()
    saved = destination.with_suffix(".txt").read_text(encoding="utf-8")
    assert saved == window._results_text.toPlainText() + "\n"
    assert "Start data point: 77" in saved
    assert "manually adjusted" in saved
    assert "Saved results to" in window._save_results_status.text()
    window._draw_empty_plot("New file")
    assert not window._save_results_button.isEnabled()
    assert not window._save_results_status.text()


def test_save_cancel_and_failure_preserve_results(gui, monkeypatch, write_popin_curve, tmp_path):
    _, window = gui
    editable_curve(window, write_popin_curve)
    text = window._results_text.toPlainText()
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    window._save_results_button.click()
    assert not window._save_results_status.text()
    # A nonexistent parent gives a deterministic write failure.
    destination = tmp_path / "missing" / "results.txt"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(destination), ""))
    errors = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: errors.append(args[2]))
    window._save_results_button.click()
    assert errors and "Could not save detection results" in errors[0]
    assert window._results_text.toPlainText() == text
    assert window._save_results_button.isEnabled()


def test_save_model_results_and_model_points_have_no_labels(gui, monkeypatch, write_popin_curve, tmp_path):
    _, window = gui
    result = editable_curve(window, write_popin_curve)
    curve = popin_ml.load_curve(result["file_path"])
    events = [{"index": 80, "depth_nm": 100., "load_uN": 160., "time_s": 0.8, "score": 0.9}]
    window._display_model_results((result["file_path"], curve, events))
    assert not window._figure.axes[0].texts
    destination = tmp_path / "model.txt"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(destination), ""))
    window._save_results_button.click()
    assert "Method: Machine learning" in destination.read_text()


def test_csv_confirms_save_and_overwrites_current_adjusted_endpoints(gui, monkeypatch, write_popin_curve, tmp_path):
    _, window = gui
    confirmations = []
    def confirm(*args):
        confirmations.append(args[2])
        return QMessageBox.Yes
    monkeypatch.setattr(QMessageBox, "question", confirm)
    destination = tmp_path / "popin_locations.csv"
    window._locations_csv_path = destination
    assert not window._save_csv_button.isEnabled()
    result = editable_curve(window, write_popin_curve)
    assert window._save_csv_button.isEnabled()
    window._save_csv_button.click()
    with destination.open(newline="", encoding="utf-8") as saved:
        first_rows = list(csv.reader(saved))
    np.testing.assert_allclose(list(map(float, first_rows[1][1:])), [158, 78, 0.78, 160, 104, 0.84])
    plot_mouse(window, "button_press_event", 78, 158, button=1)
    plot_mouse(window, "motion_notify_event", 77, 156, button=1)
    plot_mouse(window, "button_release_event", 77, 156, button=1)
    plot_mouse(window, "button_press_event", 104, 160, button=1)
    plot_mouse(window, "motion_notify_event", 107, 166, button=1)
    plot_mouse(window, "button_release_event", 107, 166, button=1)
    window._save_csv_button.click()
    with destination.open(newline="", encoding="utf-8") as saved:
        rows = list(csv.reader(saved))
    assert rows[0] == list(view_module.POPIN_CSV_COLUMNS)
    assert len(rows) == 2
    assert all(len(row) == 7 for row in rows)
    assert rows[1][0] == result["file_path"].name
    np.testing.assert_allclose(list(map(float, rows[1][1:])), [156, 77, 0.77, 166, 107, 0.87])
    assert len(confirmations) == 2
    assert "already exists" not in confirmations[0]
    assert "already exists" in confirmations[1]
    assert "overwrite the pop-in data for that file" in confirmations[1]
    assert "Updated pop-in location" in window._save_results_status.text()
    window._draw_empty_plot("New file")
    assert not window._save_csv_button.isEnabled()
    window._save_popin_csv()
    with destination.open(newline="", encoding="utf-8") as saved:
        assert len(list(csv.reader(saved))) == 2


def test_csv_unavailable_without_endpoints_or_during_model_work(gui, write_popin_curve):
    _, window = gui
    window._selected_file = write_popin_curve()
    window._run_detection()
    assert not window._save_csv_button.isEnabled()
    result = editable_curve(window, write_popin_curve)
    window._model_thread = object()
    try:
        window._update_buttons()
        assert not window._save_csv_button.isEnabled()
    finally:
        window._model_thread = None
    curve = popin_ml.load_curve(result["file_path"])
    window._display_model_results((result["file_path"], curve, []))
    assert not window._save_csv_button.isEnabled()


@pytest.mark.parametrize("existing", [False, True])
def test_csv_cancel_leaves_file_unchanged(gui, monkeypatch, write_popin_curve, tmp_path, existing):
    _, window = gui
    result = editable_curve(window, write_popin_curve)
    destination = tmp_path / "popin_locations.csv"
    window._locations_csv_path = destination
    if existing:
        with destination.open("w", newline="", encoding="utf-8") as saved:
            csv.writer(saved).writerows([view_module.POPIN_CSV_COLUMNS,
                                        [result["file_path"].name, 1, 2, 3, 4, 5, 6]])
    before = destination.read_bytes() if existing else None
    confirmations = []
    def cancel(*args):
        confirmations.append(args)
        return QMessageBox.No
    monkeypatch.setattr(QMessageBox, "question", cancel)
    window._save_csv_button.click()
    assert len(confirmations) == 1
    assert confirmations[0][-1] == QMessageBox.No
    assert (destination.read_bytes() if destination.exists() else None) == before
    assert not window._save_results_status.text()


def test_csv_overwrite_removes_old_duplicates_and_preserves_other_files(gui, monkeypatch, write_popin_curve, tmp_path):
    _, window = gui
    result = editable_curve(window, write_popin_curve)
    destination = tmp_path / "popin_locations.csv"
    window._locations_csv_path = destination
    filename = result["file_path"].name
    other = ["other.txt", "10", "20", "30", "40", "50", "60"]
    with destination.open("w", newline="", encoding="utf-8") as saved:
        csv.writer(saved).writerows([view_module.POPIN_CSV_COLUMNS,
                                    [filename, 1, 2, 3, 4, 5, 6], other,
                                    [filename, 7, 8, 9, 10, 11, 12]])
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    window._save_csv_button.click()
    with destination.open(newline="", encoding="utf-8") as saved:
        rows = list(csv.reader(saved))
    assert len(rows) == 3
    assert rows[1][0] == filename
    np.testing.assert_allclose(list(map(float, rows[1][1:])), [158, 78, 0.78, 160, 104, 0.84])
    assert rows[2] == other
    # Saving a new filename appends a row and keeps both previous files.
    result["file_path"] = tmp_path / "new.txt"
    window._save_csv_button.click()
    with destination.open(newline="", encoding="utf-8") as saved:
        appended = list(csv.reader(saved))
    assert appended[:3] == rows
    assert appended[3][0] == "new.txt"


def test_csv_write_failure_preserves_adjusted_results(gui, monkeypatch, write_popin_curve, tmp_path):
    _, window = gui
    editable_curve(window, write_popin_curve)
    window._locations_csv_path = tmp_path / "missing" / "popin_locations.csv"
    errors = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: errors.append(args[2]))
    text = window._results_text.toPlainText()
    window._save_csv_button.click()
    assert errors and "Could not save pop-in locations" in errors[0]
    assert window._results_text.toPlainText() == text
    assert window._save_csv_button.isEnabled()


def test_save_buttons_share_original_row_equally(gui):
    app, window = gui
    window.resize(1200, 750)
    window.show()
    app.processEvents()
    text_button, csv_button = window._save_results_button, window._save_csv_button
    assert abs(text_button.width() - csv_button.width()) <= 1
    assert text_button.height() == csv_button.height()
    assert text_button.y() == csv_button.y()
    assert text_button.x() + text_button.width() < csv_button.x()
