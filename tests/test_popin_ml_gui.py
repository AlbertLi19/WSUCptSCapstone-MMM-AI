"""Exercise the real Qt background workflow without a display."""
import os
import time
import importlib.util
import joblib
import numpy as np
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication, QFileDialog, QPushButton

from analysis_scripts import popin_ml
from analysis_scripts.popin_ml import DEFAULT_DATA, DEFAULT_MODEL

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
        "Select File", "Run Detection", "Train Shape Model", "Run Model"]
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


def test_create_model_worker_updates_controls(gui, monkeypatch):
    app, window = gui
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
