from pathlib import Path
import sys


def resource_root():
    return (Path(sys._MEIPASS) if getattr(sys, 'frozen', False)
            else Path(__file__).resolve().parents[2])


def output_root():
    if getattr(sys, 'frozen', False):
        from src.app.utility.app_paths import app_data_root
        return app_data_root()
    return resource_root()


def training_checkpoint():
    return output_root() / 'models/crack_unet.pt'


def default_checkpoint():
    trained = training_checkpoint()
    return trained if trained.is_file() else resource_root() / 'models/crack_unet.pt'


def reviewed_measurements_dir():
    return output_root() / 'data/Indentation_Image_Labels/reviewed_measurements'
