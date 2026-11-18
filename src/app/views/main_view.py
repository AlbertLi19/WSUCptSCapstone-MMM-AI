"""Main tab shell with Analysis deferred until first selection."""
from importlib import import_module
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QMessageBox, QLabel

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
        self._pending_tabs = set()
        self._main_layout = QVBoxLayout(self)
        self._tab_widget = QTabWidget()
        self._main_layout.addWidget(self._tab_widget)
        for label, _, _, _ in self.TAB_SPECS:
            page = QWidget()
            layout = QVBoxLayout(page)
            message = QLabel(f"Loading {label}…")
            message.setAlignment(Qt.AlignCenter)
            layout.addWidget(message)
            self._tab_widget.addTab(page, label)
        self._tab_widget.currentChanged.connect(self._open_tab)
        for index in range(len(self.TAB_SPECS)):
            if index != 1:
                self._load_tab(index)

    def _set_analysis_loading(self, loading):
        self._tab_widget.setTabText(1, "Analysis (loading…)" if loading else "Analysis")

    @property
    def model_busy(self):
        view = self._loaded_tabs.get(2)
        return view is not None and view.model_busy

    def _open_tab(self, index):
        if index < 0 or index in self._loaded_tabs or index in self._pending_tabs:
            return
        self._pending_tabs.add(index)
        if index == 1:
            self._set_analysis_loading(True)
        # A zero-delay timer can run before Windows presents the updated tab bar.
        # Leave a brief event-loop interval for the loading state to appear first.
        delay_ms = 100 if index == 1 else 0
        QTimer.singleShot(delay_ms, lambda: self._load_selected_tab(index))

    def _load_selected_tab(self, index):
        self._pending_tabs.discard(index)
        if self._tab_widget.currentIndex() == index:
            self._tab_widget.currentWidget().repaint()
            # Paint the title before synchronous tab construction blocks the event loop.
            self._tab_widget.tabBar().repaint()
            self._load_tab(index)
        elif index == 1:
            self._set_analysis_loading(False)

    def _load_tab(self, index):
        if index in self._loaded_tabs:
            return
        label, module, name, needs_controller = self.TAB_SPECS[index]
        if index == 1:
            self._set_analysis_loading(True)
            self.window().repaint()
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
        finally:
            if index == 1:
                self._set_analysis_loading(False)
        self._loaded_tabs[index] = view
        self._tab_widget.setTabText(index, label)
        setattr(self, "_" + module, view)
        # Preserve the page and tab bar entries throughout mouse/key selection.
        # Removing the current tab from currentChanged can disrupt that selection.
        page = self._tab_widget.widget(index)
        layout = page.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        layout.addWidget(view)
