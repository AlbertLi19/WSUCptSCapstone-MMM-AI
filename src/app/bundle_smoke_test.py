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

    def cracks():
        import numpy as np
        import torch
        from src.crack_measurement.model import load_grayscale, predict, read_records
        from src.crack_measurement.dataset import load_calibration
        from src.crack_measurement.paths import resource_root

        root = resource_root()
        records = read_records(root / 'data/Indentation_Image_Labels/per_image',
                               root / 'data/Indentation Images')
        if len(records) != 88 or len(load_calibration(root / 'Length.csv')) != 88:
            raise RuntimeError('The bundled crack training dataset or calibration is incomplete')
        # Verify the aggregate annotation file too; the training dialog accepts both forms.
        aggregate = read_records(root / 'data/Indentation_Image_Labels/Labels.json',
                                 root / 'data/Indentation Images')
        if {record[0].name for record in aggregate} != {record[0].name for record in records}:
            raise RuntimeError('Bundled crack annotation files disagree')
        # Include both BMP and microscope TIFF decoding without a source checkout.
        for suffix in ('.bmp', '.tif'):
            path = next(record[0] for record in records if record[0].suffix.lower() == suffix)
            if load_grayscale(path).ndim != 2:
                raise RuntimeError(f'Cannot decode bundled training image: {path}')
        previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        try:
            for name in ('crack_unet.pt', 'crack_encoder_resnet18.pt', 'crack_micronet_resnet50.pt'):
                maps = predict(np.zeros((64, 80), dtype=np.uint8), root / 'models' / name)
                if maps.shape != (2, 64, 80) or not np.isfinite(maps).all():
                    raise RuntimeError(f'Bundled crack checkpoint failed inference: {name}')
        finally:
            torch.set_num_threads(previous_threads)

    check("bundled crack checkpoints, CPU inference and training dataset", cracks)

    def crack_outputs():
        from src.crack_measurement.corrections import correction_record, save_correction
        from src.crack_measurement.paths import (
            resource_root, training_checkpoint, reviewed_measurements_dir,
        )

        checkpoint = training_checkpoint()
        export = reviewed_measurements_dir() / 'smoke-test.json'
        for destination in (checkpoint, export):
            if getattr(sys, 'frozen', False) and destination.is_relative_to(resource_root()):
                raise RuntimeError('Crack output would be saved inside the bundled resources')
            destination.parent.mkdir(parents=True, exist_ok=True)
        # Exercise reviewed JSON serialization in the isolated user profile.
        record = correction_record('smoke-test.png', [
            {'start_xy': [1, 2], 'end_xy': [8, 2], 'role': 'crack_chord'},
        ], 10, str(checkpoint), image_size=(80, 64), scale_method='drawn_line')
        try:
            save_correction(export, record)
            if not json.loads(export.read_text(encoding='utf-8'))['reviewed']:
                raise RuntimeError('Crack measurement export did not retain review status')
        finally:
            export.unlink(missing_ok=True)

    check("portable crack output directories and reviewed JSON export", crack_outputs)

    def gui():
        from PyQt5.QtWidgets import QApplication
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        from main import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        try:
            window.show()
            app.processEvents()
            tabs = window.main_view._tab_widget
            for index in range(tabs.count()):
                tabs.setCurrentIndex(index)
                app.processEvents()
                if index not in window.main_view._loaded_tabs:
                    raise RuntimeError(f"Tab {index} failed to initialize")
            if window.main_view._popin_locator_view._model is None:
                raise RuntimeError("The Pop-in Locator could not load its bundled model")
            crack_view = window.main_view._crack_measurement_view
            window.main_view._tab_widget.setCurrentIndex(3)
            app.processEvents()
            if not crack_view.panel.checkpoint.is_file():
                raise RuntimeError('The Crack Measurement tab could not find its default checkpoint')
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
