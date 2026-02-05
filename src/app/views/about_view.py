from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class AboutView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Our parent is the main view class
        self.main_view = parent

        # Create layout for the about view
        self._about_layout = QVBoxLayout(self)
        self.setLayout(self._about_layout)
        
        # Initalize the UI Components
        self._init_UI()

    """
    Initialize the UI components for the about view.
    """
    def _init_UI(self):
        self._populate_about()

    
    """
    This gives the user instrructions on how to use the app,
    what different features do and an overall description of the app.
    """
    def _populate_about(self):
        """Add instructions to the about tab."""
        # Create a scroll area to ensure all content is accessible
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Application title
        app_title = QLabel("Segmentation Application")
        app_title.setFont(QFont('Arial', 16, QFont.Bold))
        app_title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(app_title)
        
        # Add spacing
        content_layout.addSpacing(20)
        
        # Segmentation Tab instructions
        seg_title = QLabel("Segmentation Tab")
        seg_title.setFont(QFont('Arial', 14, QFont.Bold))
        content_layout.addWidget(seg_title)
        
        seg_instructions = QLabel(
            "1. Click 'Load Images' to select images for processing.\n"
            "2. Use the 'Set Scale' button to define the scale by clicking two points and entering the known distance.\n"
            "3. Use 'Crop' to select a specific area of interest in the image.\n"
            "4. Configure segmentation settings:\n"
            "   - Footprint Type: Defines the shape used for morphological operations.\n"
            "   - Thresholding Type: Method used to separate particles from background.\n"
            "   - Blur Type: Type of blur to apply for noise reduction.\n"
            "   - Min. Particle Area: Minimum size of particles to be detected.\n"
            "5. Click 'Run Segmentation' to process the image.\n"
            "6. Use '<' and '>' buttons to navigate between loaded images.\n"
            "7. 'Apply All' will copy current settings to all loaded images."
        )
        seg_instructions.setWordWrap(True)
        content_layout.addWidget(seg_instructions)
        
        content_layout.addSpacing(20)
        
        # Analysis Tab instructions
        analysis_title = QLabel("Analysis Tab")
        analysis_title.setFont(QFont('Arial', 14, QFont.Bold))
        content_layout.addWidget(analysis_title)
        
        analysis_instructions = QLabel(
            "1. After running segmentation, use the 'Generate Analysis Histograms' button to create histograms of particle data.\n"
            "2. Use 'Generate Analysis with Overlay' to include probability distribution functions on the histograms.\n"
            "3. Select which distributions to include by checking the boxes in the list.\n"
            "4. The generated histograms show size, orientation, or aspect ratio distributions of detected particles."
        )
        analysis_instructions.setWordWrap(True)
        content_layout.addWidget(analysis_instructions)
        
        content_layout.addSpacing(20)
        
        # Comparison Tab instructions
        comparision_title = QLabel("Comparison Tab")
        comparision_title.setFont(QFont('Arial', 14, QFont.Bold))
        content_layout.addWidget(comparision_title)
        
        comparision_instructions = QLabel(
            "1. Run segmentation on a dataset, navigate to the analysis tab and generate a PDF\n" 
            "2. Return to the segmentation tab and click 'reset application. Then Run segmentation and analysis again. \n"
            "3. Navigate to the comparision and select data, then choose two of the datasets. Results will be displayed on the page\n"
        )

        comparision_instructions.setWordWrap(True)
        content_layout.addWidget(comparision_instructions)
        content_layout.addSpacing(20)

        # Tips and shortcuts
        tips_title = QLabel("Tips and Shortcuts")
        tips_title.setFont(QFont('Arial', 14, QFont.Bold))
        content_layout.addWidget(tips_title)
        
        tips_text = QLabel(
            "• For batch processing, configure one image and use 'Apply All'.\n"
            "• The current settings are shown in the right panel of the Segmentation tab.\n"
            "• Toggle between 'Segmented Image' and 'Histograms' views using the dropdown.\n"
            "• When setting scale, make sure to measure along a known distance in the image."
        )
        tips_text.setWordWrap(True)
        content_layout.addWidget(tips_text)
        
        # Add version information
        content_layout.addSpacing(20)
        version_info = QLabel("Version: 1.0")
        version_info.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(version_info)
        
        # Set scroll area content
        scroll.setWidget(content_widget)
        self._about_layout.addWidget(scroll)
