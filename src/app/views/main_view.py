"""Main tab shell. Feature modules and widgets load on first selection."""
from importlib import import_module
import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QMessageBox

from controllers import MainController


class MainView(QWidget):
    request_segmentation = pyqtSignal(list)
    # Module names are also hidden imports in the Windows packaging spec.
    TAB_SPECS = (
        ("Segmentation", "segmentation_view", "SegmentationView", True),
        ("Analysis", "analysis_view", "AnalysisView", True),
        ("Pop-in Locator", "popin_locator_view", "PopInLocatorView", False),
        ("Crack Measurement", "crack_measurement_view", "CrackMeasurementView", False),
        ("Comparison", "comparison_view", "ComparisonView", True),
        ("About", "about_view", "AboutView", False),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timeout_value = 30
        self._controller = MainController(self)
        self._image_settings = None
        self._loaded_tabs = {}
        self._main_layout = QVBoxLayout(self)
        self._tab_widget = QTabWidget()
        self._main_layout.addWidget(self._tab_widget)
        for label, _, _, _ in self.TAB_SPECS:
            self._tab_widget.addTab(QWidget(), label)
        self._tab_widget.currentChanged.connect(self._open_tab)
        self._open_tab(0)

    @property
    def model_busy(self):
        view = self._loaded_tabs.get(2)
        return view is not None and view.model_busy

    def _open_tab(self, index):
        if index < 0 or index in self._loaded_tabs:
            return
        label, module, name, needs_controller = self.TAB_SPECS[index]
        try:
            view_class = getattr(import_module("views." + module), name)
            view = (view_class(self, self._controller) if needs_controller
                    else view_class(self))
            if index == 1:
                from analysis_scripts.pdf_generator import pull_timeout
                view.timeout_updated.connect(pull_timeout)
        except Exception as exc:
            if "--smoke-test" in sys.argv:
                raise
            QMessageBox.warning(self, "Could not open tab", f"{label}: {exc}")
            return  # Keep the placeholder so a later visit can retry.
        self._loaded_tabs[index] = view
        setattr(self, "_" + module, view)
        placeholder = self._tab_widget.widget(index)
        self._tab_widget.blockSignals(True)
        try:
            self._tab_widget.removeTab(index)
            self._tab_widget.insertTab(index, view, label)
            self._tab_widget.setCurrentIndex(index)
        finally:
            self._tab_widget.blockSignals(False)
        placeholder.deleteLater()
