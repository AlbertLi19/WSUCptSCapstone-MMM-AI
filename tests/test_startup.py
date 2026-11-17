import os
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QEvent, QObject, pyqtSignal
from PyQt5.QtTest import QTest

from views import main_view


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_core_tabs_load_at_startup_and_are_reused(app, monkeypatch):
    created = []

    class View(QWidget):
        timeout_updated = pyqtSignal(int)
        model_busy = False

        def __init__(self, parent, *args):
            super().__init__(parent)
            created.append(self)

    def module(name):
        return SimpleNamespace(**{spec[2]: View for spec in main_view.MainView.TAB_SPECS})

    monkeypatch.setattr(main_view, 'import_module', module)
    monkeypatch.setattr(main_view, 'MainController', lambda parent: object())
    window = main_view.MainView()
    assert set(window._loaded_tabs) == {0, 2, 3, 4, 5}
    assert not window.model_busy
    assert len(created) == 5
    window._tab_widget.setCurrentIndex(2)
    app.processEvents()
    popin = window._popin_locator_view
    popin.model_busy = True
    assert window.model_busy
    window._tab_widget.setCurrentIndex(0)
    window._tab_widget.setCurrentIndex(2)
    assert window._tab_widget.currentWidget() is popin.parentWidget()
    assert len(created) == 5
    window.close()



def test_launcher_starts_app_without_constructing_an_updater(monkeypatch):
    import sys
    import launcher

    def reject_updater(*args, **kwargs):
        raise AssertionError('Startup must not construct an updater')

    monkeypatch.setitem(sys.modules, 'auto_updater', SimpleNamespace(AutoUpdater=reject_updater))
    monkeypatch.setitem(sys.modules, 'github_updater', SimpleNamespace(GitHubUpdater=reject_updater))
    monkeypatch.setattr(sys, 'argv', ['SegmentationApp.exe', '--auto-update'])
    monkeypatch.setattr(launcher, 'preload_torch_native_libs', lambda: None)
    calls = []
    monkeypatch.setitem(sys.modules, 'main', SimpleNamespace(main=lambda: calls.append('started')))
    launcher.main()
    assert calls == ['started']


def test_analysis_loads_on_first_selection_and_is_reused(app, monkeypatch):
    created = []
    painted_titles = []

    class PaintWatcher(QObject):
        def eventFilter(self, obj, event):
            if event.type() == QEvent.Paint:
                painted_titles.append(obj.tabText(1))
            return False

    class View(QWidget):
        model_busy = False
        timeout_updated = pyqtSignal(int)

        def __init__(self, parent, *args):
            super().__init__(parent)

    def module(name):
        if name == 'views.analysis_view':
            assert 'Analysis (loading…)' in painted_titles
        created.append(name)
        return SimpleNamespace(**{spec[2]: View for spec in main_view.MainView.TAB_SPECS})

    monkeypatch.setattr(main_view, 'import_module', module)
    monkeypatch.setattr(main_view, 'MainController', lambda parent: object())
    # Isolate timeout signal wiring from unrelated PDF dependencies.
    import sys
    monkeypatch.setitem(sys.modules, 'analysis_scripts.pdf_generator',
                        SimpleNamespace(pull_timeout=lambda value: None))
    window = main_view.MainView()
    tabs = window._tab_widget
    page = tabs.widget(1)
    assert 'views.analysis_view' not in created
    app.processEvents()
    assert 1 not in window._loaded_tabs  # A hidden window does not start Analysis.
    window.show()
    app.processEvents()
    watcher = PaintWatcher()
    tabs.tabBar().installEventFilter(watcher)
    assert 1 not in window._loaded_tabs
    assert 'views.analysis_view' not in created
    assert tabs.tabText(1) == 'Analysis'
    assert tabs.currentIndex() == 0
    assert window._main_layout.count() == 1
    tabs.setCurrentIndex(5)
    app.processEvents()
    assert 'views.analysis_view' not in created
    # A selection cancelled before the callback runs does not load Analysis.
    tabs.setCurrentIndex(1)
    assert tabs.tabText(1) == 'Analysis (loading…)'
    tabs.setCurrentIndex(0)
    QTest.qWait(150)
    assert tabs.tabText(1) == 'Analysis'
    assert 'views.analysis_view' not in created

    QTest.mouseClick(tabs.tabBar(), main_view.Qt.LeftButton,
                     pos=tabs.tabBar().tabRect(1).center())
    assert tabs.tabText(1) == 'Analysis (loading…)'
    assert 'Loading Analysis' in page.findChild(main_view.QLabel).text()
    app.processEvents()
    QTest.qWait(30)
    assert 1 not in window._loaded_tabs
    assert tabs.tabText(1) == 'Analysis (loading…)'
    assert 'Analysis (loading…)' in painted_titles
    QTest.qWait(120)
    assert set(window._loaded_tabs) == set(range(6))
    assert tabs.currentIndex() == 1
    assert tabs.widget(1) is page
    assert tabs.tabText(1) == 'Analysis'
    analysis = window._loaded_tabs[1]
    tabs.setCurrentIndex(0)
    tabs.setCurrentIndex(1)
    app.processEvents()
    assert window._loaded_tabs[1] is analysis
    assert created.count('views.analysis_view') == 1
    window.hide()
    window.show()
    app.processEvents()
    assert created.count('views.analysis_view') == 1
    window.close()
