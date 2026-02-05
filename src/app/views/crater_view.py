import os
from PyQt5.QtWidgets import (QWidget, QGridLayout, QPushButton, QComboBox, QLabel, 
                            QStackedWidget, QDoubleSpinBox, QSpinBox, QVBoxLayout, QHBoxLayout, 
                            QGroupBox, QFileDialog, QSizePolicy, QFrame, QScrollArea,
                            QRubberBand, QDialog)
from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal, QPoint, QRect, QSize, QEvent
from PyQt5.QtGui import QFont, QPixmap
from controllers import main_controller as MC
from widgets import NoImagesSelectedDialog, InvalidCraterParamsDialog


"""Crater View class for CT crater analysis in PyQt5 application."""
class ROISelectionDialog(QDialog):
    """Dialog for selecting a region of interest on an image"""
    
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Region of Interest")
        self.image_path = image_path
        self.roi = None
        self.setMinimumSize(600, 600)
        self.drawing = False  # Flag to track if we're currently drawing
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Image display widget
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.pixmap = QPixmap(image_path)
        self.image_label.setPixmap(self.pixmap.scaled(
            580, 580,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        
        # Make label accept mouse tracking
        self.image_label.setMouseTracking(True)
        self.image_label.installEventFilter(self)
        
        # Variables for rubber band
        self.origin = QPoint()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.image_label)
        
        # Instructions label
        instructions = QLabel("Click and drag to select a region of interest.\nWhen satisfied with your selection, press OK.")
        instructions.setAlignment(Qt.AlignCenter)
        
        # Status label to show selected coordinates
        self.status_label = QLabel("No region selected")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(instructions)
        layout.addWidget(self.image_label)
        layout.addWidget(self.status_label)
        
        # Add OK/Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
    
    def eventFilter(self, source, event):
        if source is self.image_label:
            # Get the size of the pixmap
            pixmap_size = self.image_label.pixmap().size()
            # Get the size of the label
            label_size = self.image_label.size()
            
            # Calculate scale factors
            scale_x = pixmap_size.width() / self.pixmap.width()
            scale_y = pixmap_size.height() / self.pixmap.height()
            
            # Calculate offset (for centered pixmap)
            offset_x = (label_size.width() - pixmap_size.width()) / 2
            offset_y = (label_size.height() - pixmap_size.height()) / 2
            
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # Clear any previous selection
                self.rubberBand.hide()
                self.drawing = True
                self.origin = QPoint(event.pos())
                self.rubberBand.setGeometry(QRect(self.origin, QSize()))
                self.rubberBand.show()
                return True
                
            elif event.type() == QEvent.MouseMove and self.drawing:
                # Update the rubber band size as we drag
                self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
                return True
                
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton and self.drawing:
                # Finish drawing the selection
                self.drawing = False
                rect = self.rubberBand.geometry()
                
                # Adjust for offset and scale
                x1 = int((rect.left() - offset_x) / scale_x)
                y1 = int((rect.top() - offset_y) / scale_y)
                width = int(rect.width() / scale_x)
                height = int(rect.height() / scale_y)
                
                # Ensure values are within image bounds
                x1 = max(0, min(x1, self.pixmap.width()))
                y1 = max(0, min(y1, self.pixmap.height()))
                width = max(1, min(width, self.pixmap.width() - x1))
                height = max(1, min(height, self.pixmap.height() - y1))
                
                self.roi = [x1, y1, width, height]
                
                # Update status label to show the selected coordinates
                self.status_label.setText(f"Selected ROI: x={x1}, y={y1}, width={width}, height={height}")
                return True
                
        return super().eventFilter(source, event)


class CraterView(QWidget):

    analysis_complete = pyqtSignal(float)
                                        #(images, roi, voxel_x, voxel_y, voxel_z)
    request_crater_analysis = pyqtSignal(dict)

    def __init__(self, parent=None, main_controller: MC = None):
        super().__init__(parent)
        self.main_view = parent
        self.main_controller = main_controller
        self.images = []
        self.crater_in_progress = False
        
        self.crater_volume = 0.0
        self.crater_depth = 0.0
        self.crater_diameter_min = 0.0
        self.crater_diameter_max = 0.0
        self.crater_diameter_avg = 0.0

        self.heatmap_widget = None
        self.ellipse_widget = None
        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        # Create main layout as horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create left panel for controls
        left_panel = QFrame(self)
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_panel_layout = QVBoxLayout(left_panel)
        
        # Create scroll area for controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignTop)
        
        # Create control groups
        image_group = self._create_image_controls()
        threshold_group = self._create_threshold_controls()
        voxel_group = self._create_voxel_controls()
        
        # Add groups to scroll layout
        scroll_layout.addWidget(image_group)
        scroll_layout.addWidget(threshold_group)
        scroll_layout.addWidget(voxel_group)
        
        # Setup scroll area
        scroll_area.setWidget(scroll_content)
        left_panel_layout.addWidget(scroll_area)
        
        # Create center panel for image display
        center_panel = QFrame(self)
        center_panel.setFrameShape(QFrame.StyledPanel)
        center_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.center_layout = QVBoxLayout(center_panel)
        
        # Create stacked widget for image display
        self.image_stack = QStackedWidget()
        self.image_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add placeholder for future image display
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        image_placeholder = QLabel("Image display will appear here")
        image_placeholder.setAlignment(Qt.AlignCenter)
        image_placeholder.setStyleSheet("background-color: #f0f0f0; border: 1px dashed #cccccc;")
        placeholder_layout.addWidget(image_placeholder)
        
        # Create widget for displaying analysis results
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Create containers for the heatmap and ellipse images
        results_images_layout = QHBoxLayout()
        
        # Create containers for heatmap
        heatmap_container = QGroupBox("Crater Heatmap")
        heatmap_layout = QVBoxLayout(heatmap_container)
        self.heatmap_label = QLabel("No heatmap available")
        self.heatmap_label.setAlignment(Qt.AlignCenter)
        self.heatmap_label.setStyleSheet("background-color: #f0f0f0;")
        self.heatmap_label.setMinimumSize(300, 300)
        heatmap_layout.addWidget(self.heatmap_label)
        
        # Create containers for ellipse
        ellipse_container = QGroupBox("Crater Ellipse")
        ellipse_layout = QVBoxLayout(ellipse_container)
        self.ellipse_label = QLabel("No ellipse available")
        self.ellipse_label.setAlignment(Qt.AlignCenter)
        self.ellipse_label.setStyleSheet("background-color: #f0f0f0;")
        self.ellipse_label.setMinimumSize(300, 300)
        ellipse_layout.addWidget(self.ellipse_label)
        
        # Add the containers to results layout
        results_images_layout.addWidget(heatmap_container)
        results_images_layout.addWidget(ellipse_container)
        results_layout.addLayout(results_images_layout)
        
        # Add widgets to stack
        self.image_stack.addWidget(placeholder_widget)
        self.image_stack.addWidget(results_widget)
        
        # Add stack to center layout
        self.center_layout.addWidget(self.image_stack)
        
        # Create right panel for results
        right_panel = QFrame(self)
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_panel_layout = QVBoxLayout(right_panel)
        
        # Create results group
        results_group = self._create_results_display()
        right_panel_layout.addWidget(results_group)
        right_panel_layout.addStretch()
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(center_panel, 2)
        main_layout.addWidget(right_panel, 1)

    def _create_image_controls(self):
        group_box = QGroupBox("Image Controls")
        layout = QVBoxLayout()
        
        # Load images button
        self._load_image_button = QPushButton("Load Images")
        self._load_image_button.setToolTip('Click to load images or a folder for segmentation.')
        self._load_image_button.clicked.connect(self._load_images)
        layout.addWidget(self._load_image_button)
        
        # Run analysis button
        self._crater_analysis_button = QPushButton("Run Crater Analysis")
        self._crater_analysis_button.setToolTip('Click to run crater analysis on the loaded images.')
        self._crater_analysis_button.clicked.connect(self._run_crater_analysis)
        layout.addWidget(self._crater_analysis_button)
        
        # Image range controls
        image_range_layout = QGridLayout()
        
        image_start_label = QLabel("Image Start:")
        self._image_start_input = QSpinBox()
        self._image_start_input.setToolTip('Set the image start value')
        self._image_start_input.setValue(0)
        self._image_start_input.setSingleStep(1)
        self._image_start_input.setMinimum(0)
        self._image_start_input.setMaximum(9999)
        
        
        image_end_label = QLabel("Image End:")
        self._image_end_input = QSpinBox()
        self._image_end_input.setToolTip('Set the image end value')
        self._image_end_input.setValue(0)
        self._image_end_input.setSingleStep(1)
        self._image_end_input.setMinimum(0)
        self._image_end_input.setMaximum(9999)
        
        image_range_layout.addWidget(image_start_label, 0, 0)
        image_range_layout.addWidget(self._image_start_input, 0, 1)
        image_range_layout.addWidget(image_end_label, 1, 0)
        image_range_layout.addWidget(self._image_end_input, 1, 1)
        
        layout.addLayout(image_range_layout)
        group_box.setLayout(layout)
        return group_box
        
    def _create_threshold_controls(self):
        group_box = QGroupBox("Threshold Settings")
        layout = QGridLayout()
        
        # Binarization threshold
        threshold_label = QLabel("Binarization Threshold:")
        self._threshold_input = QDoubleSpinBox()
        self._threshold_input.setToolTip('Set the threshold value for image binarization.')
        self._threshold_input.setRange(0.0, 1.0)
        self._threshold_input.setValue(0.4)
        self._threshold_input.setDecimals(2)
        self._threshold_input.setSingleStep(0.1)
        
        # Fitting threshold
        fitting_label = QLabel("Fitting Threshold:")
        self._fitting_input = QDoubleSpinBox()
        self._fitting_input.setToolTip('Set the fitting threshold value')
        self._fitting_input.setRange(0.0, 1.0)
        self._fitting_input.setValue(0.7)
        self._fitting_input.setDecimals(2)
        self._fitting_input.setSingleStep(0.1)
        
        # Contour threshold
        contour_label = QLabel("Contour Threshold:")
        self._contour_input = QDoubleSpinBox()
        self._contour_input.setToolTip('Set the contour threshold value')
        self._contour_input.setRange(0.0, 1.0)
        self._contour_input.setValue(0.7)
        self._contour_input.setDecimals(2)
        self._contour_input.setSingleStep(0.1)
        
        layout.addWidget(threshold_label, 0, 0)
        layout.addWidget(self._threshold_input, 0, 1)
        layout.addWidget(fitting_label, 1, 0)
        layout.addWidget(self._fitting_input, 1, 1)
        layout.addWidget(contour_label, 2, 0)
        layout.addWidget(self._contour_input, 2, 1)
        
        group_box.setLayout(layout)
        return group_box
    
    def _create_voxel_controls(self):
        group_box = QGroupBox("Voxel Settings")
        layout = QGridLayout()
        
        # Voxel X
        voxel_x_label = QLabel("Voxel X Size:")
        self._voxel_x_input = QDoubleSpinBox()
        self._voxel_x_input.setRange(0.001, 1000.0)
        self._voxel_x_input.setValue(43.6353)
        self._voxel_x_input.setDecimals(4)
        self._voxel_x_input.setSingleStep(1)
        
        # Voxel Y
        voxel_y_label = QLabel("Voxel Y Size:")
        self._voxel_y_input = QDoubleSpinBox()
        self._voxel_y_input.setRange(0.001, 1000.0)
        self._voxel_y_input.setValue(43.6353)
        self._voxel_y_input.setDecimals(4)
        self._voxel_y_input.setSingleStep(1)
        
        # Voxel Z
        voxel_z_label = QLabel("Voxel Z Size:")
        self._voxel_z_input = QDoubleSpinBox()
        self._voxel_z_input.setRange(0.001, 1000.0)
        self._voxel_z_input.setValue(43.6353)
        self._voxel_z_input.setDecimals(4)
        self._voxel_z_input.setSingleStep(1)
        
        layout.addWidget(voxel_x_label, 0, 0)
        layout.addWidget(self._voxel_x_input, 0, 1)
        layout.addWidget(voxel_y_label, 1, 0)
        layout.addWidget(self._voxel_y_input, 1, 1)
        layout.addWidget(voxel_z_label, 2, 0)
        layout.addWidget(self._voxel_z_input, 2, 1)
        
        group_box.setLayout(layout)
        return group_box
    
    def _create_results_display(self):
        group_box = QGroupBox("Analysis Results")
        layout = QVBoxLayout()
        
        # Create result labels with consistent styling
        self._volume_label = QLabel("Crater Volume: 0.0 mm³")
        self._depth_label = QLabel("Crater Depth: 0.0 mm³")
        self._diameter_min_label = QLabel("Min Crater Diameter: 0.0 mm³")
        self._diameter_max_label = QLabel("Max Crater Diameter: 0.0 mm³")
        self._diameter_avg_label = QLabel("Average Crater Diameter: 0.0 mm³")
        
        # Apply consistent styling to all result labels
        result_labels = [
            self._volume_label, self._depth_label, 
            self._diameter_min_label, self._diameter_max_label, 
            self._diameter_avg_label
        ]
        
        for label in result_labels:
            label.setFont(QFont("Arial", 10, QFont.Bold))
            label.setAlignment(Qt.AlignLeft)
            label.setStyleSheet("padding: 5px; margin-bottom: 2px;")
            layout.addWidget(label)
        
        layout.addStretch()
        group_box.setLayout(layout)
        return group_box

    def _init_signals(self):
        # Connect signals to slots properly using a lambda to handle the parameters
        self.request_crater_analysis.connect(lambda params: self.main_controller.segmentation_worker.crater_analysis(params))
        # Connect worker signals to view slots
        self.main_controller.segmentation_worker.crater_vol_started.connect(self._crater_started)
        self.main_controller.segmentation_worker.crater_vol_finished.connect(self._crater_finished)

    def _run_crater_analysis(self):
        """
        Slot to run crater analysis on the loaded images.
        """
        if not self.images:
            dialog = NoImagesSelectedDialog()
            dialog.exec()
            return

        roi_image = self.images[len(self.images) // 2]  # Use the middle image for ROI selection

        # Collect all parameters into a dictionary
        self.crater_params = {
            'binarization_threshold': self._threshold_input.value(),
            'fitting_threshold': self._fitting_input.value(),
            'contour_threshold': self._contour_input.value(),
            'vx': self._voxel_x_input.value(),
            'vy': self._voxel_y_input.value(),
            'vz': self._voxel_z_input.value(),
            'image_start': self._image_start_input.value(),
            'image_end': self._image_end_input.value(),
            'roi': None,
            'image_dir': self.img_dir
        }

        check = self._check_crater_params(self.crater_params)
        if check is not None:
            dialog = InvalidCraterParamsDialog(check)
            dialog.exec()
            return
        
        roi = self._get_roi(roi_image)
        self.crater_params['roi'] = roi
        # Debug print
        print("Crater analysis parameters:")
        for key, value in self.crater_params.items():
            print(f"  {key}: {value}")
        
        
        # Run the analysis in a separate thread or process
        self.request_crater_analysis.emit(self.crater_params)

    
    def _check_crater_params(self, params) -> list: 
        invalid_params = []
        if params['image_start'] < 0 or params['image_start'] >= len(self.images):
            invalid_params.append("Image start index is out of range.")
        if params['image_end'] < 0 or params['image_end'] >= len(self.images):
            invalid_params.append("Image end index is out of range.")
        if params['image_start'] >= params['image_end']:
            invalid_params.append("Image start index must be less than image end index.")
        if params['binarization_threshold'] < 0 or params['binarization_threshold'] > 1:
            invalid_params.append("Binarization threshold must be between 0 and 1.")
        if params['fitting_threshold'] < 0 or params['fitting_threshold'] > 1:
            invalid_params.append("Fitting threshold must be between 0 and 1.")
        if params['contour_threshold'] < 0 or params['contour_threshold'] > 1:
            invalid_params.append("Contour threshold must be between 0 and 1.")
        if params['vx'] <= 0:
            invalid_params.append("Voxel X size must be greater than 0.")
        if params['vy'] <= 0:
            invalid_params.append("Voxel Y size must be greater than 0.")
        if params['vz'] <= 0:
            invalid_params.append("Voxel Z size must be greater than 0.")
        
        return invalid_params if invalid_params else None
        

    def _load_images(self):
        self.images = []
        self.img_dir = QFileDialog.getExistingDirectory(self.parent(),
                                "Select Folder",
                                os.path.expanduser('~'))
        if self.img_dir:
                for f in os.listdir(self.img_dir):
                    if f.lower().endswith(('.png', '.jpg', '.tif', '.jpeg')):
                        self.images.append(os.path.join(self.img_dir, f))
       

    @pyqtSlot(bool)
    def _crater_started(self, value: bool):
        self.crater_in_progress = value
        # Could add a loading indicator here

    @pyqtSlot(dict)
    def _crater_finished(self, crater_data: dict):
        self.crater_in_progress = False
        self.crater_volume = crater_data['volume']
        self.crater_depth = crater_data['depth']
        self.crater_diameter_min = crater_data['diameter']['minor']
        self.crater_diameter_max = crater_data['diameter']['major']
        self.crater_diameter_avg = crater_data['diameter']['average']

        self._volume_label.setText(f"Crater Volume: {self.crater_volume} mm³")
        self._depth_label.setText(f"Crater Depth: {self.crater_depth} mm³")
        self._diameter_min_label.setText(f"Min Crater Diameter: {self.crater_diameter_min} mm³")
        self._diameter_max_label.setText(f"Max Crater Diameter: {self.crater_diameter_max} mm³")
        self._diameter_avg_label.setText(f"Average Crater Diameter: {self.crater_diameter_avg} mm³")

        CRATER_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Crater_Data')
        heatmap = os.path.join(CRATER_DATA, "crater_heatmap.png")
        ellipse = os.path.join(CRATER_DATA, "crater_ellipse.png")
        
        # Display the heatmap and ellipse images
        self._display_analysis_images(heatmap, ellipse)

    def _display_analysis_images(self, heatmap_path, ellipse_path):
        """Display the heatmap and ellipse images in the center panel."""
        # Check if the image files exist
        if os.path.exists(heatmap_path):
            heatmap_pixmap = QPixmap(heatmap_path)
            self.heatmap_label.setPixmap(heatmap_pixmap.scaled(
                self.heatmap_label.width(), 
                self.heatmap_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        else:
            self.heatmap_label.setText("Heatmap image not found")
            
        if os.path.exists(ellipse_path):
            ellipse_pixmap = QPixmap(ellipse_path)
            self.ellipse_label.setPixmap(ellipse_pixmap.scaled(
                self.ellipse_label.width(), 
                self.ellipse_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        else:
            self.ellipse_label.setText("Ellipse image not found")
            
        # Switch to results view
        self.image_stack.setCurrentIndex(1)

    def _get_roi(self, image_path):
        # Check if image path exists
        if not os.path.exists(image_path):
            print(f"Image path does not exist: {image_path}")
            return None
        
        # Use our custom ROI selection dialog instead of matplotlib
        dialog = ROISelectionDialog(image_path, self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted and dialog.roi:
            return dialog.roi
        
        return None
