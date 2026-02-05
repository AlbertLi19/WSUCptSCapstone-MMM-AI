import sys
import shutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory
from PyQt5.QtGui import QFont
from views import MainView
import os
import test_module

# Define paths for various directories
PARENT = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App')
IMAGES = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_SEM_Images')
DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
SEG = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
READY = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Ready Images')
PDF = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','PDF Images')
COMBINED_IMPURITY_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'Combined_Impurity_Data')   # combined impirity/coord spacing for all images
CRATER_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Crater_Data')  # crater data for all images
SAM_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','SAM_Data')  # SAM model data

def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


# Modern dark theme color palette
dark_palette = """
    QMainWindow {
        background-color: #2b2b2b;
    }
    QWidget {
        color: #ffffff;
        background-color: #2b2b2b;
        font-size: 14px;
    }
    QPushButton {
        background-color: #3d3d3d;
        border: 1px solid #5d5d5d;
        border-radius: 4px;
        padding: 5px 15px;
        min-height: 30px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #4d4d4d;
    }
    QLineEdit, QComboBox {
        background-color: #3d3d3d;
        border: 1px solid #5d5d5d;
        border-radius: 4px;
        padding: 5px;
        font-size: 14px;
    }
    QLabel {
        font-size: 14px;
    }
    QSpinBox, QDoubleSpinBox {
        font-size: 14px;
        padding: 5px;
    }
    QCheckBox {
        font-size: 14px;
    }
"""

                
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(dark_palette)
        self.setFont(QFont('Segoe UI', 14))
        self.setWindowTitle('Impurity Segmentation App')
        self.main_view = MainView(self)
        self.setCentralWidget(self.main_view)

    def closeEvent(self, event):
        """Called when user tries to close the application"""
        # deleting files that have been loaded in, so assets dont persist
        # after the app is closed. They get cleared on app init too but that
        # is just for a backup. This way random files are lingering around the
        # users computer
        clear_directory(SEG)
        clear_directory(READY)
        clear_directory(PDF)
        clear_directory(DATA)
        clear_directory(COMBINED_IMPURITY_DATA)
        clear_directory(CRATER_DATA)
        clear_directory(SAM_DATA)
        clear_directory(IMAGES)

        self.main_view._controller.close()
        event.accept()


def main():
    """Main application entry point"""
    #test_module.test_wrapper() # Test cases (Pass in 'True' to print verbose test output, 'False' by default)
    '''
    Clear directories if they are not empty in case there are leftover 
    artifacts from when the program was last run
    TODO: delete directories when the app is shutdown, this should be for backup 
    purposes only in case the app crashes. Need to add functionality so the user
    can download the images to a different location.
    '''
    clear_directory(SEG)
    clear_directory(READY)
    clear_directory(PDF)
    clear_directory(DATA)
    clear_directory(COMBINED_IMPURITY_DATA)
    clear_directory(CRATER_DATA)
    clear_directory(IMAGES)
    clear_directory(SAM_DATA)

    # Create necessary directories if they don't exist
    if not os.path.exists(PARENT):
        os.mkdir(PARENT)
    if not os.path.exists(IMAGES):
        os.mkdir(IMAGES)   
    if not os.path.exists(DATA):
        os.mkdir(DATA) 
    if not os.path.exists(SEG):
        os.mkdir(SEG)
    if not os.path.exists(READY):
        os.mkdir(READY)
    if not os.path.exists(PDF):
        os.mkdir(PDF)
    if not os.path.exists(CRATER_DATA):
        os.mkdir(CRATER_DATA)
    if not os.path.exists(COMBINED_IMPURITY_DATA):
        os.mkdir(COMBINED_IMPURITY_DATA)
    if not os.path.exists(SAM_DATA):
        os.mkdir(SAM_DATA)

    # Initialize the PyQt5 application
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    
    main_window = MainWindow()  # Use our new MainWindow class
    main_window.showMaximized()
    app.exec()


if __name__ == '__main__':
    main()