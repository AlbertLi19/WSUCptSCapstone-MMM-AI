import sys

from src.crack_measurement import paths


def test_frozen_outputs_survive_reextraction(tmp_path, monkeypatch):
    bundle = tmp_path / '_MEI_first'
    profile = tmp_path / 'profile'
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(bundle), raising=False)
    monkeypatch.setenv('LOCALAPPDATA', str(profile))
    bundled_model = bundle / 'models/crack_unet.pt'
    bundled_model.parent.mkdir(parents=True)
    bundled_model.touch()
    assert paths.default_checkpoint() == bundled_model
    trained = paths.training_checkpoint()
    assert trained == profile / 'SegmentationApp/models/crack_unet.pt'
    assert paths.reviewed_measurements_dir().is_relative_to(profile)
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


def test_frozen_profile_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.delenv('LOCALAPPDATA', raising=False)
    monkeypatch.setattr(paths.Path, 'home', lambda: tmp_path)
    assert paths.output_root() == tmp_path / 'SegmentationApp'
