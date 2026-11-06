import sys
from pathlib import Path

from utility import app_paths


def test_frozen_data_stays_beside_executable(tmp_path, monkeypatch):
    monkeypatch.delenv('SEGMENTATION_APP_DATA', raising=False)
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'install/SegmentationApp.exe'))
    monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path / 'install/_internal'), raising=False)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'profile'))
    monkeypatch.chdir(tmp_path)
    assert app_paths.app_data_root() == tmp_path / 'install/app_data'
    assert app_paths.app_data_path('Databases', 'settings.db') == str(
        tmp_path / 'install/app_data/Databases/settings.db')


def test_source_working_data_has_its_own_directory(monkeypatch):
    monkeypatch.delenv('SEGMENTATION_APP_DATA', raising=False)
    monkeypatch.delattr(sys, 'frozen', raising=False)
    assert app_paths.app_data_root() == Path(__file__).resolve().parents[1] / 'app_data'


def test_caches_are_portable_and_explicit_settings_are_preserved(tmp_path, monkeypatch):
    monkeypatch.delenv('SEGMENTATION_APP_DATA', raising=False)
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'SegmentationApp.exe'))
    monkeypatch.delenv('HF_HOME', raising=False)
    monkeypatch.delenv('MPLCONFIGDIR', raising=False)
    monkeypatch.setenv('TORCH_HOME', str(tmp_path / 'custom-torch'))
    app_paths.configure_portable_caches()
    import os
    assert Path(os.environ['HF_HOME']) == tmp_path / 'app_data/cache/huggingface'
    assert Path(os.environ['MPLCONFIGDIR']) == tmp_path / 'app_data/cache/matplotlib'
    assert Path(os.environ['TORCH_HOME']) == tmp_path / 'custom-torch'


def test_isolated_smoke_storage_override(tmp_path, monkeypatch):
    monkeypatch.setenv('SEGMENTATION_APP_DATA', str(tmp_path))
    assert app_paths.app_data_root() == tmp_path


def test_csv_is_saved_in_portable_app_data(tmp_path, monkeypatch):
    monkeypatch.delenv('SEGMENTATION_APP_DATA', raising=False)
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'SegmentationApp.exe'))
    monkeypatch.chdir(tmp_path)
    assert app_paths.popin_locations_csv_path() == tmp_path / 'app_data/popin_locations.csv'


def test_source_csv_retains_project_location(monkeypatch):
    monkeypatch.delattr(sys, 'frozen', raising=False)
    assert app_paths.popin_locations_csv_path() == Path(__file__).resolve().parents[1] / 'popin_locations.csv'
