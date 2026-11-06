import os
from pathlib import Path
import sys


def app_data_root():
    override = os.environ.get('SEGMENTATION_APP_DATA')
    if override:
        return Path(override).expanduser().resolve()
    base = (Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False)
            else Path(__file__).resolve().parents[3])
    return base / 'app_data'


def app_data_path(*parts):
    return str(app_data_root().joinpath(*parts))


def popin_locations_csv_path():
    root = (app_data_root() if getattr(sys, 'frozen', False)
            else Path(__file__).resolve().parents[3])
    return root / 'popin_locations.csv'


def configure_portable_caches():
    if getattr(sys, 'frozen', False):
        cache = app_data_root() / 'cache'
        for name, folder in (('HF_HOME', 'huggingface'), ('TORCH_HOME', 'torch'),
                             ('MPLCONFIGDIR', 'matplotlib')):
            os.environ.setdefault(name, str(cache / folder))
