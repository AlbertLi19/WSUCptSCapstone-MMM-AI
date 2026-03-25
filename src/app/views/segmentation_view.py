import os
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QComboBox, QLabel, QStackedWidget
from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QFont
from widgets import ImageWidget, FootprintTypeDialog, ThresholdTypeDialog, BlurTypeDialog, MinParticleAreaDialog, LoadImageDialog, SettingsDialog, ProgressBarDialog, DownloadDataDialog, UnsegmentedImageDialog
import pandas as pd
import pyqtgraph as pg
import numpy as np
from dataclasses import dataclass
from PyQt5.QtWidgets import QFileDialog
import shutil
from utility.download_handler import DownloadHandler


READY_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Ready Images')

"""The SegmentationView Containts the 
UI components for the segmentation tab. Along
with other functionalities that only relate to segmentation."""

class SegmentationView(QWidget):
    request_segmentation = pyqtSignal(list)
    request_sam_segmentation = pyqtSignal(list)
    
    def __init__(self, parent=None, main_controller=None):
        super().__init__(parent)

        # Our parent / main view
        self.main_view = parent

        self._images = []
        self._image_settings = []
        self._current_image_index = -1
        self._all_impurity_data = None # a list of dataframes of impurity data
        self._is_sam = False

        self.row = 0

        # Our main controller for communication
        self.main_controller = main_controller

        # Create the respecitve layout
        self._layout = QGridLayout(self)
        self.setLayout(self._layout)



        self._init_UI()

    def _init_UI(self):
        self._connect_signals()  # Connect signals to slots
        self._init_footprint()  # Footprint type input
        self._init_thresholding()  # Thresholding type input
        self._init_blur()  # Blur type input
        self._init_min_area()  # Min. particle area input
        self._init_output()  # Desired output property selection
        self._init_run_basic()  # Run segmentation button
        self._init_run_sam() # Run SAM segmentation
        self._init_reset()  # Reset button
        self._init_load_images_button()  # Load images button
        self._init_image()  # Load in image button
        self._init_crop()  # Crop button
        self._init_scale()  # Set Scale button
        self._init_image_output()  # Image output selection
        self._init_navigation()  # Navigation buttons for previous/next image
        self.init_tip_label()  # Initialize the tip label
        self._init_apply_all()  # Apply All button to apply settings to all images
        self._column_stretches()  # Set column stretches for the layout
        self._download_button()  # Download button for segmented images
        self._update_display_settings()  # Update the display settings for the first image if any images are loaded


    def _init_footprint(self):
        #Footprint type
        self._footprint_type_label = QLabel('Footprint Type', self)
        self._footprint_type_edit = QPushButton(self)
        footprint_text = "Edit"
        if self._current_image_index >=0 and self._image_settings[self._current_image_index]._footprint_type is not None:
            footprint_text = self._image_settings[self._current_image_index]._footprint_type
        self._footprint_type_edit.setText(footprint_text)
        self._footprint_type_edit.setToolTip('Click to edit the footprint type.')
        self._footprint_type_edit.clicked.connect(self._edit_footprint_type)
        self._layout.addWidget(self._footprint_type_label,self.row,0,1,1)
        self._layout.addWidget(self._footprint_type_edit,self.row,1,1,1)
        self.row += 1
 
    def _init_thresholding(self):
        #Thresholding type input
        self._threshold_type_label = QLabel('Thresholding Type', self)
        self._threshold_type_edit = QPushButton(self)
        thresh_text = "Edit"
        if self._current_image_index >=0 and self._image_settings[self._current_image_index]._thresh_type is not None:
            footprint_text = self._image_settings[self._current_image_index]._thresh_type
        self._threshold_type_edit.setText(thresh_text)
        self._threshold_type_edit.setToolTip('Click to edit the thresholding type.')
        self._threshold_type_edit.clicked.connect(self._edit_thresh_type)
        self._layout.addWidget(self._threshold_type_label,self.row,0,1,1)
        self._layout.addWidget(self._threshold_type_edit,self.row,1,1,1)
        self.row += 1
      
        
    def _init_blur(self):
        #Blur type input
        self._blur_type_label = QLabel('Blur Type', self)
        self._blur_type_edit = QPushButton(self)
        blur_text = "Edit"
        if self._current_image_index >=0 and self._image_settings[self._current_image_index]._blur_type is not None:
            footprint_text = self._image_settings[self._current_image_index]._blur_type
        self._blur_type_edit.setText(blur_text)
        self._blur_type_edit.setToolTip('Click to edit the blur type.')
        self._blur_type_edit.clicked.connect(self._edit_blur_type)
        self._layout.addWidget(self._blur_type_label,self.row,0,1,1)
        self._layout.addWidget(self._blur_type_edit,self.row,1,1,1)
        self.row += 1

    def _init_min_area(self):
        #Min. particle area input.
        self._min_particle_label = QLabel('Min. Particle Area:',self)
        self._min_particle_edit = QPushButton(self)
        min_particle_text = "Edit"
        if self._current_image_index >=0 and self._image_settings[self._current_image_index]._min_particle_area is not None:
            footprint_text = str(self._image_settings[self._current_image_index]._min_particle_area)
        self._min_particle_edit.setText(min_particle_text)
        self._min_particle_edit.setToolTip('Click to edit the minimum particle area.')
        self._min_particle_edit.clicked.connect(self._edit_min_particle_area)
        self._layout.addWidget(self._min_particle_label,self.row,0,1,1)
        self._layout.addWidget(self._min_particle_edit,self.row,1,1,1)
        self.row += 1

    def _init_run_basic(self):
        #Run segmentation button.
        self._run_segmentation_button = QPushButton(self)
        self._run_segmentation_button.setText('Run Segmentation')
        self._run_segmentation_button.clicked.connect(self._run_segmentation)
        self._layout.addWidget(self._run_segmentation_button,self.row,0,1,2)
        self.row += 1

    def _init_run_sam(self):
        # Run SAM button
        self._run_sam_button = QPushButton(self)
        self._run_sam_button.setText('Run SAM Segmentation')
        self._run_sam_button.clicked.connect(self._run_sam_segmentation)
        self._layout.addWidget(self._run_sam_button,self.row,0,1,2)
        self.row += 1


    def _init_output(self):
        #Desired output property selection.
        self._desired_output_property_select = QComboBox(self)
        self._desired_output_property_select.addItems(['Size',
                                                       'Orientation',
                                                       'Aspect Ratio'])
        self._desired_output_property_select.setToolTip('Select the desired output property for the histogram.')
        self._desired_output_property_select.currentIndexChanged.connect(self._update_hist_plot)
        self._layout.addWidget(self._desired_output_property_select,self.row,0,1,2)
        self.row += 1

    def _init_reset(self):
        # Reset button.
        self._reset_application_button = QPushButton(self)
        self._reset_application_button.setText('Reset Application')
        self._reset_application_button.setToolTip('Click to reset the application to its initial state.')
        self._reset_application_button.clicked.connect(self._reset)
        self._layout.addWidget(self._reset_application_button,self.row,0,1,2)
        self.row += 1

    def _init_load_images_button(self):
        #Load in images and buttons.
        self._left_image = ImageWidget(self)
        self._left_image.crop_started.connect(self._start_crop)
        self._left_image.scale_started.connect(self._start_scale)
        self._left_image.crop_ended.connect(self._end_crop)
        self._left_image.scale_ended.connect(self._end_scale)
        self._layout.addWidget(self._left_image,0,2,self.row,1)

        self._right_display = QStackedWidget(self)
        self._right_image = ImageWidget(self)
        self._right_display.addWidget(self._right_image)
        self._hist_view = pg.GraphicsView()
        self._hist_layout = pg.GraphicsLayout()
        self._hist_view.setCentralItem(self._hist_layout)
        self._hist_plot = self._hist_layout.addPlot()
        self._right_display.addWidget(self._hist_view)
        self._pdf_image = ImageWidget(self)
        self._right_display.addWidget(self._pdf_image)
        self._layout.addWidget(self._right_display,0,3,self.row,1)
        

    def _init_image(self):
         # Load in image button
        self._load_image_button = QPushButton(self)
        self._load_image_button.setText('Load Images')
        self._load_image_button.setToolTip('Click to load images or a folder for segmentation.')
        self._load_image_button.clicked.connect(self._load_images)
        self._layout.addWidget(self._load_image_button,self.row,2,1,1)


    def _init_crop(self):
         #crop button
        self._crop_button = QPushButton(self)
        self._crop_button.setText('Crop')
        self._crop_button.setToolTip('Click to crop to the desiered area.')
        self._crop_button.clicked.connect(self._left_image.crop)
        self._layout.addWidget(self._crop_button,self.row,3,1,1)
        self.row += 1

    def _init_scale(self):
         # Set Scale button
        self._set_scale_button = QPushButton(self)
        self._set_scale_button.setText('Set Scale')
        self._set_scale_button.clicked.connect(self._left_image.scale)
        self._layout.addWidget(self._set_scale_button,self.row,2,1,1)

    def _init_image_output(self):
         self._set_right_display = QComboBox(self)
         self._set_right_display.addItems(['Segmented Image','Histograms']) # view histograms on this tab, but put the PDF on its own tab since it is                                                               #  expensive to generate
         self._set_right_display.setToolTip('Select segmented image or histogram display.')
         self._set_right_display.currentIndexChanged.connect(self._change_right_display)
         self._layout.addWidget(self._set_right_display,self.row,3,1,1)

    def _init_navigation(self):
        # Add navigation buttons (moved before tip label)
        navigation_row = self.row + 1  # Create a new row for navigation
        self._prev_image_button = QPushButton('<', self)
        self._prev_image_button.setToolTip('Show previous image.')
        self._prev_image_button.clicked.connect(lambda: self._show_next_image('Left')) 
        self._layout.addWidget(self._prev_image_button, navigation_row, 0, 1, 1)

        self._next_image_button = QPushButton('>', self)
        self._next_image_button.setToolTip('Show next image.')
        self._next_image_button.clicked.connect(lambda: self._show_next_image('Right')) 
        self._layout.addWidget(self._next_image_button, navigation_row, 1, 1, 1)


    def _init_apply_all(self):
        # Apply All button
        self._apply_all_button = QPushButton(self)
        self._apply_all_button.setText('Apply All')
        self._apply_all_button.setToolTip('Click to apply the current image settings to all images.')
        self._apply_all_button.clicked.connect(self._apply_all_settings)
        self._layout.addWidget(self._apply_all_button, self.row, 0, 1, 2)
        self.row += 1

    def init_tip_label(self):
        # Tip label in a fixed-width, scrollable box
        from PyQt5.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout
        self._tip_label = QLabel(self)
        self._tip_label.setFont(QFont('Arial', 11))
        self._tip_label.setStyleSheet('color:red;') # Change Tip Box Color (Was white)
        self._tip_label.setWordWrap(True)
        self._tip_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._tip_label.setMinimumWidth(250)
        self._tip_label.setMaximumWidth(250)
        self._tip_label.setMinimumHeight(60)
        self._tip_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self._tip_label)
        scroll_area.setMinimumWidth(250)
        scroll_area.setMaximumWidth(250)
        scroll_area.setMinimumHeight(60)
        scroll_area.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        self._layout.addWidget(scroll_area, self.row, 4, 2, 2)

    def _download_button(self):
         # Add Download button to top right corner
        self.segmentation_download_button = QPushButton('Download', self)
        self.segmentation_download_button.setToolTip('Download image data')
        self._layout.addWidget(self.segmentation_download_button, 0, 4, 1, 1, Qt.AlignRight | Qt.AlignTop)
        self.segmentation_download_button.clicked.connect(lambda: self._popup_download_box("segmentation"))

    def _column_stretches(self):
        #Set column stretches.
        self._layout.setColumnStretch(0,1)
        self._layout.setColumnStretch(1,1)
        self._layout.setColumnStretch(2,2)
        self._layout.setColumnStretch(3,2)

    def _init_default_settings(self, additional_images=None):

        """
        params: additional_images: a list of images to be added to the current settings list (for uploading images more than once)
        Initializes the default settings for the image settings dataclass. This is called when the user loads in images.
        filename, nm_per_pix, intensity_threshold, disk_radius, thresh_num, blur_num, min_particle_area, blocksize, c,
        smooth_kernel_size, d, sigma_color, sigma_space, footprint_num, ellipse_width, ellipse_height
        """
        # Define default settings
        default_settings = {
            'filename': None,
            'nm_per_pix': None, # This is the value that the user input for scale, in NM
            'width_in_pix': None, # This is the width of the image in pixels
            '_right_image': None, # Added this to store the right image
            '_footprint_num': None,
            '_footprint_type': None,
            '_disk_radius': 1,
            '_ellipse_width': 5,
            '_ellipse_height': 3,
            '_intensity_threshold': 127,
            '_blocksize': 11,
            '_c': 2,
            '_thresh_num': 0,
            '_thresh_type': None,
            '_blur_num': 0,
            '_blur_type': None,
            '_smooth_kernel_size': 5,
            '_d': 9,
            '_sigma_color': 75,
            '_sigma_space': 75,
            '_min_particle_area': 60,
            '_impurity_data': None,
            '_scale_point1' : None,  
            '_scale_point2': None,  
            '_crop_rect':  None,  
            '_original_crop_rect': None   # Could be removed eventually
        }

        # Initialize settings for each image

        '''
        default behavior is setting default settings for all images in self._images (initializing the list). If additional images
        are passed in as an optional parameter then those files are added to image settings instead
        '''
        if additional_images is None:
            # making sure that if the list is empty, then we start with an empty list
            if self._image_settings is None:
                self._image_settings = []

            for image_filename in self._images:
                settings = default_settings.copy()
                settings['filename'] = image_filename
                self._image_settings.append(image_settings(**settings))
        else:
            for image_filename in additional_images:
                settings = default_settings.copy()
                settings['filename'] = image_filename
                self._image_settings.append(image_settings(**settings))

    def _connect_signals(self):
        if hasattr(self.main_controller, 'segmentation_worker'):
            # SEGMENTATION
            self.main_controller.segmentation_worker._segmentation_complete.connect(self._segmentation_complete)
            self.main_controller.segmentation_worker._sam_segmentation_complete.connect(self._segmentation_complete)
            # SEGMENTATION
            self.main_controller.segmentation_worker.new_pdf_img.connect(self._new_pdf_img)
            
            # Talks to the working thread in the controller, lets us know when it has started segmentation
            self.main_controller.segmentation_worker.segmentation_started.connect(self._segmentation_started) 
            # Talks to the working thread in the controller, lets us know when it has processed an image
            self.main_controller.segmentation_worker.processed_images.connect(self._processed_images)

            self.request_segmentation.connect(self.main_controller.segmentation_worker.run_segmentation)

            self.request_sam_segmentation.connect(self.main_controller.segmentation_worker.run_sam_segmentation)

    def tip_text(self) -> str:
        text = 'Current Settings:\n'
        if self._current_image_index >= 0:
            settings = self._image_settings[self._current_image_index]
            #Footprint type text
            if settings._footprint_type is not None:
                text += 'Footprint Type: ' + settings._footprint_type + '\n'
            
            #Extra footprint type parameters
            if settings._footprint_type is not None:
                if settings._footprint_num == 0:
                    text += 'Disk Radius: ' + str(settings._disk_radius) + '\n'
                else:
                    text += 'Ellipse Width: ' + str(settings._ellipse_width) + '\n'
                    text += 'Ellipse Height: ' + str(settings._ellipse_height) + '\n'

            #Threshold type text
            if settings._thresh_type is not None:
                text += 'Threshold Type: ' + settings._thresh_type + '\n'

            #Extra threshold type parameters
            if settings._thresh_type is not None:
                if settings._thresh_num == 0:
                    text += 'Intensity Threshold: ' + str(settings._intensity_threshold) + '\n'
                elif settings._thresh_num == 1 or settings._thresh_num == 2:
                    text += 'Block Size: ' + str(settings._blocksize) + '\n'
                    text += 'c: ' + str(settings._c) + '\n'

            #BLur type text
            if settings._blur_type is not None:
                text += 'Blur Type: ' + settings._blur_type + '\n'

            #Extra blur type parameters
            if settings._blur_type is not None:
                if settings._blur_num >= 0 and settings._blur_num <= 2:
                    text += 'Smooth Kernel Size: ' + str(settings._smooth_kernel_size) + '\n' # Issue here, NOW FIXED
                else:
                    text += 'd: ' + str(settings._d) + '\n'
                    text += 'Sigma Color: ' + str(settings._sigma_color) + '\n'
                    text += 'Sigma Space: ' + str(settings._sigma_space) + '\n'

            #MPA text
            if settings._min_particle_area is not None:
                text += 'Min. Particle Area: ' + str(settings._min_particle_area) + '\n'
            
            #Scale text
            if self._left_image.length_in_pixels is not None and self._left_image.scale_value is not None\
                and self._left_image.unit is not None:
                scale = str(self._left_image.scale_value / self._left_image.length_in_pixels).split('.')
                scale = scale[0] + '.' + scale[1][:3]
                unit = self._left_image.unit.lower()
                if unit[-1] == 's':
                    unit = unit[:-1]
                text += f'Current Scale: 1 Pixel = {scale} {unit}s\n'
            else:
                text += 'Current Scale: None'
        else: 
            text += 'None'
        return text
        
    def _update_hist_plot(self):
        # Warning: if you edit this edit the download histogram code in _popup_download_box as well because it is based off this
        settings = self._image_settings[self._current_image_index]
        if settings is not None:
            # Clear previous plots
            for item in self._hist_plot.items:
                self._hist_plot.removeItem(item)
            
            # Get the column name from UI
            col_name = self._desired_output_property_select.currentText()
            clean_col_name = col_name.replace(' ','_')
            
            # Get data if available
            if settings._impurity_data is not None and clean_col_name in settings._impurity_data.columns:
                clean_data = settings._impurity_data[clean_col_name]
                
                y, x = np.histogram(clean_data, bins=15)
                
                bgi = pg.BarGraphItem(
                    x0=x[:-1], 
                    x1=x[1:], 
                    height=y, 
                    pen=pg.mkPen(color='k', width=0.5),  
                    brush=pg.mkBrush(30, 110, 216, 180)  
                )
                
                # Add the histogram to the plot
                self._hist_plot.addItem(bgi)
                
                # Set proper axis labels and title
                self._hist_plot.setLabel('left', 'Frequency')
                self._hist_plot.setLabel('bottom', col_name)
                self._hist_plot.setTitle(f'Distribution of {col_name}')
                
                # Improve grid visibility
                self._hist_plot.showGrid(x=True, y=True, alpha=0.3)

                
                
                
            else:
                # Display a message when no data is available
                text = pg.TextItem(text="No data available", color=(200, 0, 0))
                text.setPos(self._hist_plot.width()/2, self._hist_plot.height()/2)
                self._hist_plot.addItem(text)
                
                # Reset labels
                self._hist_plot.setLabel('left', '')
                self._hist_plot.setLabel('bottom', '')
                self._hist_plot.setTitle('')

                
    def _change_right_display(self):
        self._right_display.setCurrentIndex(self._set_right_display.currentIndex())

    def _start_crop(self):
        self._focus_image()
        self._image_settings[self._current_image_index]._original_crop_rect = self._left_image._crop_rect
        self._tip_label.setText('Click and drag on the\nimpurity image to crop!')

    def _end_crop(self):
        self._unfocus_image()
        self._image_settings[self._current_image_index]._crop_rect = self._left_image._crop_rect # Sets the crop rect for the current index
        self._tip_label.setText(self.tip_text())

    def _start_scale(self):
        self._focus_image()
        self._tip_label.setText('Click on the impurity image\nto create two points,\ndrag them to a known length\nin microns, then\npress enter and\nyou can specify the scale!')
        
    def _end_scale(self):
        self._unfocus_image()
        self._image_settings[self._current_image_index].nm_per_pix = self._left_image.nm_per_pix # Sets the pixel per um value for the current index
        self._image_settings[self._current_image_index].width_in_pix = self._left_image._length_in_pixels
        self._tip_label.setText(self.tip_text())

    def _focus_image(self):
        """
        Makes the image the main view of the application. Disables all other buttons except for the image buttons.
        """
        for row in range(self._layout.rowCount()):
            for col in range(self._layout.columnCount()):
                layout_item = self._layout.itemAtPosition(row, col)
                if layout_item and layout_item.widget() != self._left_image:
                    layout_item.widget().setEnabled(False)
        self._left_image.setFocus()

    def _unfocus_image(self):
        """
        Resets focus back
        """
        for row in range(self._layout.rowCount()):
            for col in range(self._layout.columnCount()):
                layout_item = self._layout.itemAtPosition(row, col)
                if layout_item and layout_item.widget() != self._left_image:
                    layout_item.widget().setEnabled(True)
        self.setFocus()

    """Loads a popup dialog box that will be 
    used to display a message to the user"""
    def _popup_dialog_loadimage(self):
        """
        Do we Need to generate the dialog box for loading images?
        """
        if self._current_image_index == -1:
            dialog = LoadImageDialog(self)
            dialog.exec()
            return False
        else:
            return True

    def _load_images(self):
        """
        Loads the images from the controller and sets the first image to be displayed.
        Initialized default settings for all the images
        TODO: add file upload support
        """
        loaded_images = self.main_controller.get_images()
        if not loaded_images:
            return
            
        if not self._images:
            # initialize array of image settings to default. _image_settings[i] corresponds to _images[i]
            self._images = loaded_images
            self._init_default_settings()

        else:
            # if images are already loaded, append the new images to the images list and default settings to the settings list
            self._images.extend(loaded_images)
            self._init_default_settings(loaded_images)

        if self._images:
            self._current_image_index = 0
            self._left_image.set_image(self._images[self._current_image_index])  

    def _segmentation_started(self, total_images):
        """Takes in the total number of images to be segmented and creates a progress bar dialog box"""
        self._progress_dialog = ProgressBarDialog(total_images)
        self._progress_dialog.show()

    def _processed_images(self, processed_images, total_images):
        """Updates the progress bar dialog box with the number of images that have been segmented"""
        self._progress_dialog.progressBar.setValue(processed_images)
        if processed_images == total_images:
            self._progress_dialog.accept()
            self._progress_dialog = None

    def _find_segmented_image(self, file_path):
        '''
        Given an image that has been segmented already, it looks for its name in the segmented folder and returns the full path to the segmented image
        '''
        SEGMENTED_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
        if self._is_sam is True:
            target = "segmented-" + os.path.splitext(os.path.basename(file_path))[0] + '.png'
        else:
            target = "segmented-" + os.path.splitext(os.path.basename(file_path))[0] + '.png'
        for file in os.listdir(SEGMENTED_FOLDER):
            if os.path.basename(file) == target:
                return os.path.join(SEGMENTED_FOLDER, file)

    def _show_next_image(self, direction):
         """
         see show_prev_image for documentation. Is identical except for how current_image_index is updated (+1 here, -1 in show_prev_image)
         """
         if self._images:
            # save current image settings first
            self._image_settings[self._current_image_index]._crop_rect = self._left_image._crop_rect
            self._image_settings[self._current_image_index]._scale_point1 = self._left_image._scale_point1
            self._image_settings[self._current_image_index]._scale_point2 = self._left_image._scale_point2

            # update current image being displayed
            # if there is a saved crop rect, apply it to the new image, otherwise set the current images crop rect to nothing (reset from previous image)
            if direction == 'Right':
                self._current_image_index = (self._current_image_index + 1) % len(self._images)
            else:
                self._current_image_index = (self._current_image_index - 1) % len(self._images)

            crop_rect = None
            # if a crop rect is saved, apply it to the new image
            if self._image_settings[self._current_image_index]._crop_rect:
                crop_rect = self._image_settings[self._current_image_index]._crop_rect
                self._left_image._crop_rect = crop_rect
            else:
                self._left_image._crop_rect = None

            # Apply saved crop rect to the new image
            self._left_image.set_image(self._images[self._current_image_index], crop_rect)
             
            self._right_image.set_image(self._image_settings[self._current_image_index]._right_image)
            self._update_hist_plot()

            # Update displayed settings from internal state.
            ft = self._image_settings[self._current_image_index]._footprint_type or "Edit"
            self._footprint_type_edit.setText(ft)
            tt = self._image_settings[self._current_image_index]._thresh_type or "Edit"
            self._threshold_type_edit.setText(tt)
            bt = self._image_settings[self._current_image_index]._blur_type or "Edit"
            self._blur_type_edit.setText(bt)
            mpa = self._image_settings[self._current_image_index]._min_particle_area or "Edit"
            self._min_particle_edit.setText(str(mpa))
            self._tip_label.setText(self.tip_text())
        
            self._update_display_settings()
            # handle the right image
            seg_fname = self._find_segmented_image(self._image_settings[self._current_image_index].filename)
            self._right_image.set_image(seg_fname)
            
    def _run_segmentation(self):
        self._is_sam = False
        if self._current_image_index < 0:
            return
        if self._can_run_segmentation():
            self._run_segmentation_button.setEnabled(False) # Disabling the button while segmentation is running
            self._run_single_segmentation()

    def _run_sam_segmentation(self):
        self._is_sam = True
        if self._current_image_index < 0:
            return
        if self._can_run_segmentation():
            img_settings = self._image_settings[self._current_image_index]
            if img_settings.filename is not None and self._left_image.nm_per_pix is not None\
                    and img_settings._intensity_threshold is not None and img_settings._disk_radius is not None:
                location = os.path.join(READY_FOLDER, os.path.basename(img_settings.filename).split('.')[0] + '.png')
                self._left_image.save(location)
                self.request_sam_segmentation.emit(self._image_settings)
            # Turn cursor into spinning wheel?
            self.setCursor(Qt.WaitCursor)
        
    def _run_single_segmentation(self):
         self._is_sam = False
         img_settings = self._image_settings[self._current_image_index]
         if img_settings.filename is not None and self._left_image.nm_per_pix is not None\
                and img_settings._intensity_threshold is not None and img_settings._disk_radius is not None:
            location = os.path.join(READY_FOLDER, os.path.basename(img_settings.filename).split('.')[0] + '.png')
            self._left_image.save(location)
            self.request_segmentation.emit(self._image_settings)

    def _edit_thresh_type(self):
        if self._popup_dialog_loadimage():
            tt_dialog = ThresholdTypeDialog(self)
            if tt_dialog.exec() == ThresholdTypeDialog.Accepted:
                idx = self._current_image_index
                self._image_settings[idx]._thresh_num, self._image_settings[idx]._thresh_type, intensity_threshold, blocksize, c = tt_dialog.get_threshold_type()
                if self._image_settings[idx]._thresh_num == 0:
                    self._image_settings[idx]._intensity_threshold = intensity_threshold
                elif self._image_settings[idx]._thresh_num == 1 or self._image_settings[idx]._thresh_num == 2:
                    self._image_settings[idx]._blocksize = blocksize
                    self._image_settings[idx]._c = c
                self._threshold_type_edit.setText(self._image_settings[idx]._thresh_type)
            self._tip_label.setText(self.tip_text()) # Fixed issure where tip label was not updating
            #self._can_run_segmentation()

    def _edit_blur_type(self):
        if self._popup_dialog_loadimage():
            bt_dialog = BlurTypeDialog(self)
            if bt_dialog.exec() == BlurTypeDialog.Accepted:
                idx = self._current_image_index
                self._image_settings[idx]._blur_num, self._image_settings[idx]._blur_type, smooth_kernel_size, d, sigma_color, sigma_space = bt_dialog.get_blur_type()
                if self._image_settings[idx]._blur_num >= 0 and self._image_settings[idx]._blur_num <= 2:
                    self._image_settings[idx]._smooth_kernel_size = smooth_kernel_size
                else:
                    self._image_settings[idx]._d = d
                    self._image_settings[idx]._sigma_color = sigma_color
                    self._image_settings[idx]._sigma_space = sigma_space
                self._blur_type_edit.setText(self._image_settings[idx]._blur_type)
            #self._tip_label.setText(self.tip_text)
            #self._can_run_segmentation()


    def _edit_min_particle_area(self):
        if self._popup_dialog_loadimage():
            idx = self._current_image_index
            mpa_dialog = MinParticleAreaDialog(self)
            if mpa_dialog.exec() == MinParticleAreaDialog.Accepted:
                self._image_settings[idx]._min_particle_area = mpa_dialog.get_min_particle_area()
                self._min_particle_edit.setText(str(self._image_settings[idx]._min_particle_area))
            #clself._tip_label.setText(self.tip_text)
            #self._can_run_segmentation()


    def _edit_footprint_type(self):
        if self._popup_dialog_loadimage():
            ft_dialog = FootprintTypeDialog(self)
            if ft_dialog.exec() == FootprintTypeDialog.Accepted:
                idx = self._current_image_index
                self._image_settings[idx]._footprint_num, self._image_settings[idx]._footprint_type, disk_radius, ellipse_width, ellipse_height = ft_dialog.get_footprint_type()
                if self._image_settings[idx]._footprint_num == 0:
                    self._image_settings[idx]._disk_radius = disk_radius
                else:
                    self._image_settings[idx]._ellipse_width = ellipse_width
                    self._image_settings[idx]._ellipse_height = ellipse_height
                self._footprint_type_edit.setText(self._image_settings[idx]._footprint_type)
            self._tip_label.setText(self.tip_text())
            #self._can_run_segmentation()


       
    def _apply_all_settings(self):
        if self._current_image_index < 0:
            return
        current = self._image_settings[self._current_image_index]

        # Get current crop and scale info for later changing the images
        _crop_rect = self._left_image._crop_rect
        

        for s in self._image_settings:
            if s is not current:
                # copy all current image settings to all other items in _image_settings array.
                # when left/right arrows are clicked, these settings will need to be applied to the current image
                s._footprint_num = current._footprint_num
                s._footprint_type = current._footprint_type
                s._disk_radius = current._disk_radius
                s._ellipse_width = current._ellipse_width
                s._ellipse_height = current._ellipse_height
                s._intensity_threshold = current._intensity_threshold
                s._blocksize = current._blocksize
                s._c = current._c
                s._thresh_num = current._thresh_num
                s._thresh_type = current._thresh_type
                s._blur_num = current._blur_num
                s._blur_type = current._blur_type
                s._smooth_kernel_size = current._smooth_kernel_size
                s._d = current._d
                s._sigma_color = current._sigma_color
                s._sigma_space = current._sigma_space
                s._min_particle_area = current._min_particle_area
                # Add crop and scale
                s._crop_rect = _crop_rect
                s._scale_point1 = current._scale_point1 
                s._scale_point2 = current._scale_point2
                s.nm_per_pix = current.nm_per_pix
                
        
        self._update_display_settings() # calling this to update the UI elements
        self._tip_label.setText(self.tip_text()) # calling this to update the tip label

            
    def _update_display_settings(self):
        """Update all UI elements to show current image settings"""
        if self._current_image_index >= 0:
            current = self._image_settings[self._current_image_index]
            # Update buttons
            self._footprint_type_edit.setText(current._footprint_type or "Edit")
            self._threshold_type_edit.setText(current._thresh_type or "Edit")
            self._blur_type_edit.setText(current._blur_type or "Edit")
            self._min_particle_edit.setText(str(current._min_particle_area or "Edit"))
            # Update tip label
            self._tip_label.setText(self.tip_text())

    def _print_settings(self):
        """Prints the current image settings to the console for debugging purposes at the moment
           CAN BE REMOVED LATER"""

        print("\n=== Current Image Settings ===")
        print(f"Current Image Index: {self._current_image_index}")
        if self._current_image_index >= 0:
            current = self._image_settings[self._current_image_index]
            print(f"Filename: {current.filename}")
            print(f"Footprint: Type={current._footprint_type}, Num={current._footprint_num}")
            print(f"Disk Radius: {current._disk_radius}")
            print(f"Ellipse: Width={current._ellipse_width}, Height={current._ellipse_height}")
            print(f"Threshold: Type={current._thresh_type}, Num={current._thresh_num}")
            print(f"Intensity Threshold: {current._intensity_threshold}")
            print(f"Blocksize: {current._blocksize}")
            print(f"C: {current._c}")
            print(f"Blur: Type={current._blur_type}, Num={current._blur_num}")
            print(f"Kernel Size: {current._smooth_kernel_size}")
            print(f"D: {current._d}")
            print(f"Sigma: Color={current._sigma_color}, Space={current._sigma_space}")
            print(f"Min Particle Area: {current._min_particle_area}")
            print(f"Scale: {current.nm_per_pix} px/um")
            print(f"crop area (saved): {current._crop_rect}")
            print(f"Crop area in image_widge state: {self._left_image._crop_rect}")
            print(f"impurity data: {current._impurity_data}") # To see if the impurity data is being saved CURRENTLY NOT WORKING
            print(f"Right Image: {current._right_image}")
            print("========================\n")
        

    @pyqtSlot(list)
    def _sam_segmentation_complete(self, impurity_data:list):
        self.setCursor(Qt.ArrowCursor)

        
        if self._images: # if some or all images were able to be segmented
            self._current_image_index = 0

            # keep track of all impurity data in case needed later
            self._all_impurity_data = impurity_data

            # update impurity data for all images
            for i in range(len(self._image_settings)):
                self._image_settings[i]._impurity_data = impurity_data[i]

            crop_rect = None
            # if a crop rect is saved, apply it to the new image
            if self._image_settings[self._current_image_index]._crop_rect:
                crop_rect = self._image_settings[self._current_image_index]._crop_rect
            else:
                self._left_image._crop_rect = None

            # set left image to the unsegmented segmented image
            self._left_image.set_image(self._images[self._current_image_index], crop_rect)
            seg_fname = self._find_segmented_image(self._image_settings[self._current_image_index].filename)
            self._right_image.set_image(seg_fname)

        else: 
            # no images were segmented so reset the app to its default state.
            self._reset()

    @pyqtSlot(list, list)
    def _segmentation_complete(self, impurity_data:list, unsegmented_images:list):
        '''
        This function is being called from a signal in the main controller that is activated after the segmentation is complete for all
        images in the batch. The function takes in the filename of the segmented image and the impurity data that was generated from the segmentation.
        Once the segmentation is complete the gui will show the first image in the batch. The function will set the image on the right side of the GUI to
        the segmented image
        '''
        self.setCursor(Qt.ArrowCursor)
        if unsegmented_images:
            #Popup dialog here
            for idx, image in enumerate(self._images): # _images is a list of file paths. Check if the file paths match in unsegmented images and remove
                if image in unsegmented_images:
                    self._images.remove(image)
                    self._image_settings.pop(idx) # remove corresponding setting for the unsegmented image

            dialog = UnsegmentedImageDialog(unsegmented_images)
            dialog.exec()
            
        if self._images: # if some or all images were able to be segmented
            self._current_image_index = 0

            # keep track of all impurity data in case needed later
            self._all_impurity_data = impurity_data

            # update impurity data for all images
            for i in range(len(self._image_settings)):
                self._image_settings[i]._impurity_data = impurity_data[i]

            crop_rect = None
            # if a crop rect is saved, apply it to the new image
            if self._image_settings[self._current_image_index]._crop_rect:
                crop_rect = self._image_settings[self._current_image_index]._crop_rect
            else:
                self._left_image._crop_rect = None

            # set left image to the unsegmented segmented image
            self._left_image.set_image(self._images[self._current_image_index], crop_rect)
            seg_fname = self._find_segmented_image(self._image_settings[self._current_image_index].filename)
            self._right_image.set_image(seg_fname)

        else: 
            # no images were segmented so reset the app to its default state.
            self._reset()

        # enable the run segmentation button again
        self._run_segmentation_button.setEnabled(True)

    @pyqtSlot(str)
    def _new_pdf_img(self, filename:str):
        self._pdf_image.set_image(filename)

    def _can_run_segmentation(self):
        '''
        Gets called whenever an image setting is changed. Checks if the current image settings are valid for segmentation.
        '''
        runnable = True
        for setting in self._image_settings:
            if not self._is_sam:
                if (setting.filename is None or setting.nm_per_pix is None or 
                    setting._footprint_num is None or setting._min_particle_area is None or 
                    setting._blur_num is None or setting._thresh_num is None or
                    setting._min_particle_area <= 0):
                    runnable = False
            else:
                if setting.nm_per_pix is None:
                    runnable = False
        if runnable:
            return True
        else:
            dialog = SettingsDialog(self)
            dialog.exec()
            return False
    
    def _reset(self):
        """
        Resets the current image index and clears the left and right images.
        Not Working
        """
        self._current_image_index = -1
        self._left_image.clear()
        self._right_image.clear()
        self._pdf_image.clear()

        # Reset UI labels to default
        if hasattr(self, '_footprint_type_edit'):
            self._footprint_type_edit.setText('Edit')
        if hasattr(self, '_threshold_type_edit'):
            self._threshold_type_edit.setText('Edit')
        if hasattr(self, '_blur_type_edit'):
            self._blur_type_edit.setText('Edit')
        if hasattr(self, '_min_particle_edit'):
            self._min_particle_edit.setText('Edit')

        self._tip_label.setText('')
        self._images = []
        self._image_settings = []
        self._all_impurity_data = None

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

        DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
        SEG = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
        READY = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Ready Images')
        PDF = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','PDF Images')
        COMBINED_IMPURITY_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'Combined_Impurity_Data')  
        clear_directory(SEG)
        clear_directory(READY)
        #clear_directory(PDF) # Want to leave the created JSON in folder on Reset
        clear_directory(DATA)
        clear_directory(COMBINED_IMPURITY_DATA)

    def _popup_download_box(self, data_type: str):
        download_dialog = DownloadHandler(self, data_type, self._image_settings)
        download_dialog.download()


@dataclass
class image_settings:
    """
    Dataclass to store image settings for segmentation. Each image that is loaded in will have its own instance of this class.
    It will contain the different crop, scale, and segmentation settings for each image. In the MainView class, there is a list
    of filenames (self._images) that are loaded in. There is also a current index variable, which indicates which index of the _images
    list is currently being displayed. The _image_settings list is correlated to the _images list such that _images[i] has the settings
    from _image_setting[i]
    """
    filename:str
    #image: np.ndarray
    nm_per_pix:float
    width_in_pix:int
    _right_image:str
    _footprint_num:int
    _footprint_type:str
    _disk_radius:int
    _ellipse_width:int
    _ellipse_height:int
    _intensity_threshold:int
    _blocksize:int
    _c:int
    _thresh_num:int
    _thresh_type:str
    _blur_num:int
    _blur_type:str
    _smooth_kernel_size:int
    _d:int
    _sigma_color:int
    _sigma_space:int
    _min_particle_area:int
    _impurity_data: pd.DataFrame = None
    _scale_point1: QPoint = None  
    _scale_point2: QPoint = None  
    _crop_rect: QRect = None      
    _original_crop_rect: QRect = None  # Could be removed eventually Added it just to try and revert back to original crop rect
