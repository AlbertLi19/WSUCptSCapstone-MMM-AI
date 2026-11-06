import sys

from src.crack_measurement import paths


def test_frozen_outputs_are_portable_and_separate_from_bundled_resources(tmp_path, monkeypatch):
    bundle = tmp_path / '_MEI_first'
    profile = tmp_path / 'profile'
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(bundle), raising=False)
    monkeypatch.setenv('LOCALAPPDATA', str(profile))
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'SegmentationApp.exe'))
    bundled_model = bundle / 'models/crack_unet.pt'
    bundled_model.parent.mkdir(parents=True)
    bundled_model.touch()
    assert paths.default_checkpoint() == bundled_model
    trained = paths.training_checkpoint()
    assert trained == tmp_path / 'app_data/models/crack_unet.pt'
    assert paths.reviewed_measurements_dir().is_relative_to(tmp_path / 'app_data')
    trained.parent.mkdir(parents=True)
    trained.write_bytes(b'user-trained checkpoint')
    assert paths.default_checkpoint() == trained

    # A later EXE launch extracts into a different directory.
    monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path / '_MEI_second'))
    assert paths.default_checkpoint().read_bytes() == b'user-trained checkpoint'
    assert paths.training_checkpoint() == trained
    assert not paths.reviewed_measurements_dir().is_relative_to(paths.resource_root())


def test_source_paths_remain_in_repository(monkeypatch):
    monkeypatch.delattr(sys, 'frozen', raising=False)
    assert paths.output_root() == paths.resource_root()
    assert paths.training_checkpoint() == paths.resource_root() / 'models/crack_unet.pt'


def test_frozen_paths_do_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'install/SegmentationApp.exe'))
    monkeypatch.chdir(tmp_path)
    assert paths.output_root() == tmp_path / 'install/app_data'
