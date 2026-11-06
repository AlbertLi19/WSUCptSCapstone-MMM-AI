"""Main-app tab wrapper for indentation crack measurement."""
from pathlib import Path
import sys

# On Windows, importing PyQt before PyTorch can break c10.dll initialization.
# Load the crack package (and torch) before any Qt imports in this module.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.crack_measurement.gui import CrackMeasurementWidget  # noqa: E402

from PyQt5.QtWidgets import QVBoxLayout, QWidget  # noqa: E402


class CrackMeasurementView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.panel = CrackMeasurementWidget(self)
        layout.addWidget(self.panel)
