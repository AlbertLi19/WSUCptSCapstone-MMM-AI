import os
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from views.about_view import AboutView
from views.analysis_view import AnalysisView
from views.segmentation_view import SegmentationView
from views.crater_view import CraterView  # Uncomment if CraterView is needed
from views.comparison_view import ComparisonView
from controllers import MainController
from analysis_scripts.pdf_generator import pull_timeout

READY_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Ready Images')
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
distribution_csv_path = os.path.join(base_dir, "analysis_scripts", "distributions.csv")

# this is a test seeing if we initiate an update from the executable file
class MainView(QWidget):
    request_segmentation = pyqtSignal(list)
    def __init__(self, parent:QWidget = None):
        super().__init__(parent=parent)

        self.timeout_value = 30 # Timeout value for pdf_generator / ANALYSIS
        self._controller = MainController(self)
       
        # Create main layout
        self._main_layout = QVBoxLayout()
        self.setLayout(self._main_layout)
        
        # Create tab widget
        self._tab_widget = QTabWidget()
        self._main_layout.addWidget(self._tab_widget)

        self._image_settings = None
        
        # Creating the about tab using the AboutView class
        self._about_view = AboutView(self)
        self._segmentation_view = SegmentationView(self, self._controller)

        # passing in the image settings to the analysis view
        # for download and analysis
        self._analysis_view = AnalysisView(self, self._controller)
        #self._crater_view = CraterView(self, self._controller)

        self._comparison_view = ComparisonView(self, self._controller)
        
        # Add tabs to tab widget
        self._tab_widget.addTab(self._segmentation_view, "Segmentation")
        self._tab_widget.addTab(self._analysis_view, "Analysis")
        self._tab_widget.addTab(self._comparison_view, "Comparison")
        #self._tab_widget.addTab(self._crater_view, "Crater Analysis") # Remove
        self._tab_widget.addTab(self._about_view, "About")
        
        
        self._analysis_view.timeout_updated.connect(pull_timeout)