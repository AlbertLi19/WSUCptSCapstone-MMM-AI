from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox, QProgressBar, QWidget, QHBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os

"""This Class will be used to create a dialog 
box that will be used to display a message to the user
when they try to do segmentation without loading an image first."""
class LoadImageDialog(QDialog):
    def __init__(self, parent: QDialog = None):
        super().__init__(parent)
        self.setWindowTitle("Load Image Requirement")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        message = QLabel("Please Load in an Image\nbefore setting parameters.")
        message.setAlignment(Qt.AlignCenter)  # Centers the text
        message.setFont(QFont('Arial', 20))  # Sets font family and size
        layout.addWidget(message)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)

class UnsegmentedImageDialog(QDialog):
    def __init__(self, unsegmented_images:list, parent: QDialog = None):
        super().__init__(parent)
        self.setWindowTitle("Segmentation Fail Warning")
        # Remove fixed size to allow auto-sizing
        
        layout = QVBoxLayout()

        message = QLabel("Warning: The following images could not be segmented due to a processing error:\n" + "\n".join(unsegmented_images) + "\n\nThis is likely from Min. particle are being too small.")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)  # Enable text wrapping
        layout.addWidget(message)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)
        
        # Adjust size to content after everything is added
        self.adjustSize()

class DownloadDataDialog(QDialog):
    """This Class will be used to create a dialog box 
    for downloading. Type must be either "segmentation" or "analysis"
    to determine the type of data to be downloaded."""
    def __init__(self, parent=None, data_type=None):
        super().__init__(parent)
        self.data_type = data_type
        self.segmentedImagesBox = QCheckBox()
        self.histogramBox = QCheckBox()
        self.impurityDataBox = QCheckBox()
        self.datasetBox = QCheckBox()
        self.datasetoverlayBox = QCheckBox()
        self.datasetImpurityBox = QCheckBox()

        if data_type == "segmentation":
            self.setWindowTitle("Download Segmentation Data")
        else:
            self.setWindowTitle("Download Analysis Data")

        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        message = QLabel("Check each box to download the data.\nClick 'OK' to proceed.")
        message.setAlignment(Qt.AlignTop)  # Centers the text
        layout.addWidget(message)
        
        # Add type-specific checkboxes
        if data_type == "segmentation":
            self.segmentedImagesBox = QCheckBox("Segmented Images")
            self.histogramBox = QCheckBox("Image Histograms")
            self.impurityDataBox = QCheckBox("Image Impurity Data")
            layout.addWidget(self.segmentedImagesBox)
            layout.addWidget(self.histogramBox)
            layout.addWidget(self.impurityDataBox)
        else:  
            self.datasetBox = QCheckBox("Dataset Histogram")
            self.datasetoverlayBox = QCheckBox("Dataset Histogram with Overlay")
            self.datasetImpurityBox = QCheckBox("Dataset Impurity Data")
            layout.addWidget(self.datasetBox)
            layout.addWidget(self.datasetoverlayBox)
            layout.addWidget(self.datasetImpurityBox)
        
        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)

"""This Class will be used to create a dialog box 
that will be used to display a message to the user
when they try to do segmentation without setting the parameters first."""
class SettingsDialog(QDialog):
    def __init__(self, parent=None, message=None):
        super().__init__(parent)
        self.setWindowTitle("Settings Requirement")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        

        # Allowing the message to be passed in as a parameter
        # Will also also a default message to be displayed if none is passed in
        if message is None:
            message = "Ensure all settings are set, for every image(s)\nbefore running segmentation."
        
        # Create label with proper styling
        message_label = QLabel(message)
      
        layout.addWidget(message_label)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)

"""This Class will be used to create a popup progress bar dialog box
that will be used to display the progress of the segmentation process or Statistical analysis.
The users actions will be blocked until the process is complete."""
class ProgressBarDialog(QDialog):
    def __init__(self, totalImages: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing...")
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)  # Disable close button


        layout = QVBoxLayout()

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, totalImages) # n will be the total number of images to process
        layout.addWidget(self.progressBar)
       
    
        self.setLayout(layout)


class NoImagesSelectedDialog(QDialog):
    def __init__(self, parent: QDialog = None):
        super().__init__(parent)
        self.setWindowTitle("Crater Analysis Fail Warning")
        # Remove fixed size to allow auto-sizing
        
        layout = QVBoxLayout()

        message = QLabel("Error: Unable to run crater analysis.\nNo images were selected. Please select a folder and try again.")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)  # Enable text wrapping
        layout.addWidget(message)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)
        
        # Adjust size to content after everything is added
        self.adjustSize()


class InvalidCraterParamsDialog(QDialog):
    def __init__(self, parameters: list, parent: QDialog = None):
        super().__init__(parent)
        self.setWindowTitle("Crater Analysis Fail Warning")
        # Remove fixed size to allow auto-sizing
        
        layout = QVBoxLayout()

        message = QLabel("Error: Unable to run crater analysis.\nThe following errors were found in the parameters:\n")
        for param in parameters:
            message.setText(message.text() + "\n" + param)
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)  # Enable text wrapping
        layout.addWidget(message)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)
        
        # Adjust size to content after everything is added
        self.adjustSize()

class NameDatasetDialog(QDialog):
    def __init__(self, parent: QDialog = None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QLineEdit  # local import so top-of-file imports don't need changing

        self.setWindowTitle("Name Dataset")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        message = QLabel("Please enter a name for the dataset before proceeding with analysis.")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Dataset name")
        self.name_edit.returnPressed.connect(self._on_accept)  # Enter key will accept
        layout.addWidget(self.name_edit)

        button = QPushButton("Continue")
        button.clicked.connect(self._on_accept)
        layout.addWidget(button)

        self.setLayout(layout)

        self._dataset_name = None

    def _on_accept(self):
        # Save the text and close the dialog
        self._dataset_name = self.name_edit.text().strip()
        self.accept()

    def get_dataset_name(self) -> str:
        """Return the entered dataset name (or None if none was entered)."""
        return self._dataset_name
    
class SelectAnalysisData(QDialog):
    def __init__(self, parent: QDialog = None):
        super().__init__(parent)
        self.setWindowTitle("Select Analysis Data to Download")
        self.setFixedSize(400, 200)

        PDF_FOLDER = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Segmentation App', 'PDF Images')
        self.pdf_folder = PDF_FOLDER

        layout = QVBoxLayout()

        # Gather files (only files, no directories)
        files = []
        if os.path.isdir(PDF_FOLDER):
            for fname in sorted(os.listdir(PDF_FOLDER)):
                if not fname.lower().endswith('.json'):
                    continue
                fullpath = os.path.join(PDF_FOLDER, fname)
                if os.path.isfile(fullpath):
                    files.append(fname)

        self.checkboxes = []
        self.checkbox_to_filename = {}

        if not files:
            no_files_label = QLabel("No files found in PDF Images folder.")
            no_files_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_files_label)
            ok_btn = QPushButton("OK")
            ok_btn.clicked.connect(self.accept)
            layout.addWidget(ok_btn)
        else:
            info_label = QLabel("Select up to two files:")
            layout.addWidget(info_label)

            # Create a checkbox for each file, displaying name without extension
            for fname in files:
                name_no_ext = os.path.splitext(fname)[0]
                cb = QCheckBox(name_no_ext)
                cb.stateChanged.connect(self._on_checkbox_state_changed)
                layout.addWidget(cb)
                self.checkboxes.append(cb)
                self.checkbox_to_filename[cb] = fname

            # Buttons
            btn_layout_widget = QWidget()
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("OK")
            ok_btn.clicked.connect(self.accept)
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            btn_layout_widget.setLayout(btn_layout)
            layout.addWidget(btn_layout_widget)

        self.setLayout(layout)

    def _on_checkbox_state_changed(self, state=None):
        # Enforce maximum of two selections by disabling unchecked boxes when two are selected
        selected_count = sum(1 for cb in self.checkboxes if cb.isChecked())
        if selected_count >= 2:
            for cb in self.checkboxes:
                if not cb.isChecked():
                    cb.setEnabled(False)
        else:
            for cb in self.checkboxes:
                cb.setEnabled(True)

    def get_selected_paths(self) -> tuple:
        """Return a tuple of full paths for the selected files (max 2)."""
        selected = []
        for cb in self.checkboxes:
            if cb.isChecked():
                fname = self.checkbox_to_filename.get(cb)
                if fname:
                    selected.append(os.path.join(self.pdf_folder, fname))
        return tuple(selected)


class InvalidComparisonDialog(QDialog):
    def __init__(self, parent: QDialog = None):
        super().__init__(parent)
        self.setWindowTitle("Comparison Analysis Warning")
        # Remove fixed size to allow auto-sizing
        
        layout = QVBoxLayout()

        message = QLabel("Error: Two samples must be selected for comparison analysis.\nPlease select two samples and try again.")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)  # Enable text wrapping
        layout.addWidget(message)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)
        
        # Adjust size to content after everything is added
        self.adjustSize()