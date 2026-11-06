import os
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import pyqtSignal

from views import main_view


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_tabs_load_once_and_busy_check_does_not_load_popin(app, monkeypatch):
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
    assert set(window._loaded_tabs) == {0}
    assert not window.model_busy
    assert len(created) == 1
    window._tab_widget.setCurrentIndex(2)
    popin = window._popin_locator_view
    popin.model_busy = True
    assert window.model_busy
    window._tab_widget.setCurrentIndex(0)
    window._tab_widget.setCurrentIndex(2)
    assert window._tab_widget.currentWidget() is popin
    assert len(created) == 2
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
