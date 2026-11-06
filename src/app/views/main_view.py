"""Main tab shell. Feature modules and widgets load on first selection."""
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
        self._analysis_loading_label = QLabel("Analysis is loading…")
        self._analysis_loading_label.setAlignment(Qt.AlignCenter)
        self._analysis_loading_label.hide()
        self._main_layout.addWidget(self._analysis_loading_label)
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
        self._analysis_timer = QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.timeout.connect(self._load_analysis)
        for index in range(len(self.TAB_SPECS)):
            if index != 1:
                self._load_tab(index)

    def showEvent(self, event):
        super().showEvent(event)
        if 1 not in self._loaded_tabs and 1 not in self._pending_tabs:
            self._pending_tabs.add(1)
            self._set_analysis_loading(True)
            self._analysis_timer.start(0)

    def _load_analysis(self):
        self._pending_tabs.discard(1)
        if not self.isVisible():
            self._set_analysis_loading(False)
            return
        # Paint the main window and loading state before building Analysis.
        # Qt widgets must still be constructed on the GUI thread.
        self.window().repaint()
        self._load_tab(1)

    def _set_analysis_loading(self, loading):
        self._analysis_loading_label.setVisible(loading)
        self._tab_widget.setTabText(1, "Analysis (loading…)" if loading else "Analysis")

    @property
    def model_busy(self):
        view = self._loaded_tabs.get(2)
        return view is not None and view.model_busy

    def _open_tab(self, index):
        if index < 0 or index in self._loaded_tabs or index in self._pending_tabs:
            return
        self._pending_tabs.add(index)
        # Let Qt finish selecting the existing page before constructing its UI.
        QTimer.singleShot(0, lambda: self._load_selected_tab(index))

    def _load_selected_tab(self, index):
        self._pending_tabs.discard(index)
        if self._tab_widget.currentIndex() == index:
            self._tab_widget.currentWidget().repaint()
            self._load_tab(index)

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
