"""Offline checks run inside the packaged application before a release."""

import argparse
import json
from pathlib import Path
import sys
import traceback


def run_checks(check):
    def packaging():
        import pkg_resources
        import backports.tarfile
        from importlib.metadata import version

        for name in ("numpy", "scipy", "torch", "torchvision", "transformers"):
            version(name)

    check("packaging imports and metadata", packaging)

    def sam():
        import torch
        from torchvision.ops import nms
        from transformers import pipeline, SamImageProcessor, SamImageProcessorFast, SamModel, SamProcessor
        from transformers.pipelines.mask_generation import MaskGenerationPipeline

        # Exercise the native torchvision extension, not only the Python imports.
        indices = nms(torch.tensor([[0., 0., 2., 2.]]), torch.tensor([0.9]), 0.5)
        if indices.tolist() != [0]:
            raise RuntimeError("torchvision NMS returned an unexpected result")
        # No model downloads or network requests during a packaging check.
        SamImageProcessor()
        SamImageProcessorFast()

    check("PyTorch DLLs and lazy SAM imports", sam)

    def model():
        import numpy as np
        from analysis_scripts.popin_ml import BUNDLED_MODEL, load_model, predict

        bundle = load_model(BUNDLED_MODEL)
        i = np.arange(120, dtype=float)
        predict(np.column_stack([i, i * 2, i / 100]), bundle)

    check("bundled pop-in model and scikit-learn imports", model)

    def gui():
        from PyQt5.QtWidgets import QApplication
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        from main import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        try:
            window.show()
            app.processEvents()
            if window.main_view._popin_locator_view._model is None:
                raise RuntimeError("The Pop-in Locator could not load its bundled model")
        finally:
            window.close()
            controller = window.main_view._controller
            controller._segmentation_thread.quit()
            if not controller._segmentation_thread.wait(5000):
                raise RuntimeError("The GUI worker thread did not shut down")
            app.processEvents()

    check("main window, Qt plugins, plotting and bundled resources", gui)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--smoke-test-report", type=Path, required=True)
    args = parser.parse_args(argv)
    report = args.smoke_test_report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    result = {"status": "running", "frozen": bool(getattr(sys, "frozen", False)), "checks": []}

    def save():
        report.write_text(json.dumps(result, indent=2), encoding="utf-8")

    def check(name, operation):
        result["current_check"] = name
        save()
        operation()
        result["checks"].append(name)

    try:
        run_checks(check)
    except Exception:
        result.update(status="failed", traceback=traceback.format_exc())
        save()
        return 1
    result.update(status="passed", current_check=None)
    save()
    return 0


if __name__ == "__main__":
    sys.exit(main())
