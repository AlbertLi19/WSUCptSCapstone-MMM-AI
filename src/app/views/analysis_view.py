import os
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QVBoxLayout, QScrollArea, QCheckBox, QLineEdit, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from widgets import  SettingsDialog, ProgressBarDialog, NameDatasetDialog
import functools
from utility.download_handler import DownloadHandler
from Databases.database_handler import DatabaseHandler
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#distribution_csv_path = os.path.join(base_dir, "analysis_scripts", "distributions.csv")
distribution_csv_path = resource_path("analysis_scripts/distributions.csv")

from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PyQt5.QtGui import QPixmap, QImage
from io import BytesIO

def latex_to_pixmap(latex, fontsize=9, dpi=200, bgcolor='#2b2b2b', fontcolor='white'):
    try:
        fig = plt.figure(figsize=(0.01, 0.01), dpi=dpi)
        fig.patch.set_facecolor(bgcolor)

        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        text = fig.text(0, 0, f"${latex}$", fontsize=fontsize, color=fontcolor)

        # Tight fit
        fig.canvas.draw()
        bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
        width, height = bbox.width / dpi, bbox.height / dpi
        fig.set_size_inches(width, height)

        fig.canvas.draw()
        buffer = BytesIO()
        fig.savefig(buffer, format="png", bbox_inches='tight', pad_inches=0.05, facecolor=bgcolor)
        plt.close(fig)

        qimg = QImage()
        qimg.loadFromData(buffer.getvalue(), "PNG")
        return QPixmap.fromImage(qimg)
    except:
        qimg = QImage()
        return QPixmap.fromImage(qimg)


class AnalysisView(QWidget):
    timeout_updated = pyqtSignal(int)
    def __init__(self, parent=None, main_controller=None):
        super().__init__(parent)

        self.timeout_value = 30 # Timeout value for pdf_generator / ANALYSIS

        # Our parent / main view
        self.main_view = parent

        # Intialize database
        self.db = DatabaseHandler()

        # Our main controller for communication
        self.main_controller = main_controller

        # Create the respective layout
        self._analysis_layout = QGridLayout(self)
        self.setLayout(self._analysis_layout)

        self._connect_signals()

        # Initialize the UI Components
        self._init_UI()

        self.pdf_name = ""

        
    
    def _init_UI(self):
        self._histogram_analysis_button()
        self._download_button()
        #self._overlay_button()
        #self._timeout_textfield()
        #self._select_deselect_button()
        #self._scroll_area()
        self._analysis_label()
        self._analysis_label2()

    def _histogram_analysis_button(self):
        # Add content to Analysis tab with proper alignment
        self._generate_analysis_button = QPushButton('Generate PDF Probabilities', self)
        self._generate_analysis_button.setToolTip('Generate a chart of PDF probabilities from a default list of PDFs')
        # self._generate_analysis_button.setFont(QFont('Segoe UI', 14))
        self._analysis_layout.addWidget(self._generate_analysis_button, 0, 0, 1, 1, Qt.AlignLeft | Qt.AlignTop)
        self._generate_analysis_button.clicked.connect(lambda: self.main_controller._segmentation_worker.run_pdf(False, self.pdf_name) if self._can_generate_analysis() else None)

    def _download_button(self):
         self.analysis_download_button = QPushButton('Download', self)
         self.analysis_download_button.setToolTip('Download image data')
         self._analysis_layout.addWidget(self.analysis_download_button, 0, 4, 1, 1, Qt.AlignRight | Qt.AlignTop)
         self.analysis_download_button.clicked.connect(lambda: self._popup_download_box("analysis"))

    def _overlay_button(self):
         # Add second button to Analysis tab for optional PDF/MLE/FWHM overlay
        self._generate_overlay_button = QPushButton('Generate PDF Probabilities from List', self)
        self._generate_overlay_button.setToolTip('Generate a chart of PDF probabilities from the selected PDFs below')
        # self._generate_overlay_button.setFont(QFont('Segoe UI', 14))
        self._analysis_layout.addWidget(self._generate_overlay_button, 2, 0, 1, 1, Qt.AlignLeft | Qt.AlignTop)
        self._generate_overlay_button.clicked.connect(lambda: self.main_controller._segmentation_worker.run_pdf(True) if self._can_generate_analysis() else None)

    def _timeout_textfield(self):

        self._timeout_label = QLabel("Timeout (seconds):", self)
        self._timeout_label.setFont(QFont('Segoe UI', 12))
        self._analysis_layout.addWidget(self._timeout_label, 3, 0, 1, 1, Qt.AlignLeft | Qt.AlignTop)

        self._timeout_input = QLineEdit(self)
        self._timeout_input.setPlaceholderText("Default: 30")
        self._timeout_input.setFont(QFont('Segoe UI', 12))
        self._timeout_input.setFixedWidth(100)
        self._analysis_layout.addWidget(self._timeout_input, 3, 1, 1, 1, Qt.AlignLeft | Qt.AlignTop)

        self._timeout_input.textChanged.connect(self.update_timeout_value)


    def _select_deselect_button(self):
        # Adds a container for the two buttons
        button_container = QWidget(self)
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0) 
        button_layout.setSpacing(2) # Spacing between buttons

        # Select all button, will select all distributions
        self._select_all_button = QPushButton('Select All', self)
        self._select_all_button.setToolTip('Select all distributions.')
        self._select_all_button.setFont(QFont('Segoe UI', 12))
        self._select_all_button.clicked.connect(self.select_all_distributions)
        button_layout.addWidget(self._select_all_button)

        # Deselect all button, will deselect all distributions
        self._deselect_all_button = QPushButton('Deselect All', self)
        self._deselect_all_button.setToolTip('Deselect all distributions.')
        self._deselect_all_button.setFont(QFont('Segoe UI', 12))
        self._deselect_all_button.clicked.connect(self.deselect_all_distributions)
        button_layout.addWidget(self._deselect_all_button)

        # Adds our widget container to the analysis layout
        self._analysis_layout.addWidget(button_container, 4, 1, 1, 1, Qt.AlignLeft | Qt.AlignTop)

    def _scroll_area(self):
        self.scroll_layout = QVBoxLayout()
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_vbox = QVBoxLayout()
        self.checkboxes = {}
        self.scroll_widget.setLayout(self.scroll_vbox)
        self.scroll_area.setWidget(self.scroll_widget)
        self._analysis_layout.addWidget(self.scroll_area, 3, 0, 2, 1)
        self.setLayout(self._analysis_layout)
        self.load_distributions()
    
    def _analysis_label(self):
        self.analysis_label = QLabel("Waiting for probability plot...", self)
        self.analysis_label.setAlignment(Qt.AlignCenter)
        self.analysis_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._analysis_layout.addWidget(self.analysis_label, 1, 0, 2, 2)

    def _analysis_label2(self):
        self.analysis_label2 = QLabel("Waiting for PDF plot...", self)
        self.analysis_label2.setAlignment(Qt.AlignCenter)
        self.analysis_label2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._analysis_layout.addWidget(self.analysis_label2, 1, 3, 2, 2)

    def _load_data_images(self):
        pass


    def _connect_signals(self):
        if hasattr(self.main_controller, 'segmentation_worker'):
            self.main_controller.segmentation_worker.distribution_started.connect(self._distribution_started)
            self.main_controller.segmentation_worker.analysis_progress.connect(self._analysis_progress)
            self.main_controller.segmentation_worker.finished.connect(self.display_fitter)
            self.main_controller.segmentation_worker.finished2.connect(self.display_fitter2)


    def _can_generate_analysis(self):
        """Creates a dialog to tell the user they need to run segmentation first, 
           or ensure that their data is clean."""
        self.pdf_name = ""
        if len(self.main_controller.segmentation_worker.impurity_data): # if data present, then get name
            pdf_folder = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','PDF Images')
            while True:
                name_dialog = NameDatasetDialog(self)
                name_dialog.exec()
                self.pdf_name = name_dialog.get_dataset_name().strip()
                if self.pdf_name == "":
                    continue  # empty name, prompt again
                pdf_path = os.path.join(pdf_folder, f"{self.pdf_name}.json")
                if os.path.exists(pdf_path):
                    dialog = SettingsDialog(self, f"Dataset name '{self.pdf_name}' already exists. Please choose a different name.")
                    dialog.exec()
                    continue  # name exists, prompt again
                return True
            
        else: # no data and no name
            dialog = SettingsDialog(self, "Segmentation Needs to be Ran and Impurity Data Present.")
            dialog.exec()
            return False
        
        
           
         

    def _distribution_started(self, total_distributions):
        """Creates a progress bar dialog box for the distribution generation"""
        self._progress_dialog = ProgressBarDialog(total_distributions)
        self._progress_dialog.show()
    
    def _analysis_progress(self, processed_distributions):
        """Updates the progress bar dialog box with the number of distributions that have been processed"""
        self._progress_dialog.progressBar.setValue(processed_distributions)
        if processed_distributions >= 8:
            self._progress_dialog.accept()

    def load_distributions(self):
        #df = pd.read_csv(distribution_csv_path)
        distributions = self.db._get_all_distributions()

        for name, active, formula in distributions:
            # Horizontal layout for checkbox + formula image
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(10)

            # Create checkbox
            checkbox = QCheckBox(name)
            checkbox.setStyleSheet("color: white")  # Optional: change checkbox text to white
            checkbox.setChecked(bool(active)) # be from db call
            checkbox.stateChanged.connect(functools.partial(self.update_status, name)) # db call
            self.checkboxes[name] = checkbox #db call

            # Create LaTeX image label
            latex_label = QLabel()
            latex_label.setPixmap(latex_to_pixmap(formula, fontcolor='white'))  # Pass white font
            latex_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            # Prevent image from stretching
            latex_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            # Add to horizontal layout
            hbox.addWidget(checkbox)
            hbox.addWidget(latex_label)
            hbox.setAlignment(Qt.AlignLeft)

            

            # Wrap in a QWidget so you can add it to a QVBoxLayout
            container = QWidget()
            container.setLayout(hbox)
            self.scroll_vbox.addWidget(container)
    
    def update_timeout_value(self):
        text = self._timeout_input.text()
        if text.isdigit():
            self.timeout_value = int(text)
            self.timeout_updated.emit(self.timeout_value)

    def select_all_distributions(self):
        """Select all distributions in the list."""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all_distributions(self):
        """Deselect all distributions in the list."""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    # Write checked/unchecked updates to the CSV
    def update_status(self, name, state):

        checked = int(state > 0)
        # updates our database
        self.db._update_distribution_status(name, checked)

    def display_fitter(self, path):
        print(path)
        pixmap = QPixmap(path)

        # ✅ Scale pixmap to fit within label dimensions, preserving aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.analysis_label.width(),
            self.analysis_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.analysis_label.setPixmap(scaled_pixmap)
        self.analysis_label.setText("")


    def display_fitter2(self, path):
        pixmap = QPixmap(path)

        # ✅ Same logic for second label
        scaled_pixmap = pixmap.scaled(
            self.analysis_label2.width(),
            self.analysis_label2.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.analysis_label2.setPixmap(scaled_pixmap)
        self.analysis_label2.setText("")

    def _popup_download_box(self, data_type):
        download_dialog = DownloadHandler(self, data_type)
        download_dialog.download()

    def resizeEvent(self, event):
        if self.analysis_label.pixmap():
            self.analysis_label.setPixmap(
                self.analysis_label.pixmap().scaled(
                    self.analysis_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        if self.analysis_label2.pixmap():
            self.analysis_label2.setPixmap(
                self.analysis_label2.pixmap().scaled(
                    self.analysis_label2.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        super().resizeEvent(event)


       


        
        