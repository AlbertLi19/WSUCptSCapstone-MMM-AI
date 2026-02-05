import sys
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QSemaphore, QCoreApplication, Qt
from PyQt5.QtWidgets import QFileDialog
from segmentation_scrips import segment_impurity_image
from analysis_scripts import fit_and_plot
from crater_scripts import CraterVolume_BCShot4_python as CraterVolume
import pandas as pd
research_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Research')
sys.path.append(research_path)
from PyQt5 import QtWidgets
from segmentation_scrips.SAM_segmentation import sam_segmentation, analyze_sam_regions
import numpy as np
from math import sqrt

SEGMENTED_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
IMPURITY_DATA_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'Impurity_Data')              #individual impurity data/coord spacing
COMBINED_IMPURITY_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'Combined_Impurity_Data')   # combined impirity/coord spacing for all images
IMPURITY_CSV = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'Impurity_SEM_Images')
READY_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Ready Images')
PDF_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'PDF Images')
import time
from typing import Optional, List
class SegmentationWorker(QObject):
    _segmentation_complete = pyqtSignal(list, list)  # object can be str or None
    _sam_segmentation_complete = pyqtSignal(list, list)
    new_pdf_img = pyqtSignal(str)
    finished = pyqtSignal(str)
    finished2 = pyqtSignal(str)
    segmentation_started = pyqtSignal(int)
    processed_images = pyqtSignal(int, int)
    distribution_started = pyqtSignal(int)
    analysis_progress = pyqtSignal(int)
    impurity_data = []

    crater_vol_started = pyqtSignal(bool)
    crater_vol_finished = pyqtSignal(dict)

    def __init__(self, parent:QObject = None):
        super().__init__(parent=parent)
        
    @pyqtSlot(list)
    def run_segmentation(self, settings):
        start = time.time()
        count = 0
        unsegmented_images = []
        print("Segmentation started")
        self.segmentation_started.emit(len(settings))
        self.processed_images.emit(0, len(settings))
        # returns pandas dataframe with impurity data
        self.impurity_data = []
        for setting in settings:
            '''Run segmentation algorithim on each image in the list of settings
                Segment_impurity_image runs the segmentation algorithm on the image and
                saves:
                - Segmented image as "segmented-<filename>.png" in SEG = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
                - impurity measurements as "<filename>_impurity_measurements.csv" in os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
                - coordinate spacing as "<filename>_coord_spacing.csv" in os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
                Those files are used to generate the PDF
            '''
            filename = setting.filename
            um_per_pix = setting.nm_per_pix / 1000.0  # nm to um
            image_width = setting.width_in_pix
            intensity_threshold = setting._intensity_threshold
            disk_radius = setting._disk_radius
            thresh_num = setting._thresh_num
            blur_num = setting._blur_num
            min_particle_area = setting._min_particle_area
            blocksize = setting._blocksize
            c = setting._c
            smooth_kernel_size = setting._smooth_kernel_size
            d = setting._d
            sigma_color = setting._sigma_color
            sigma_space = setting._sigma_space
            footprint_num = setting._footprint_num
            ellipse_width = setting._ellipse_width
            ellipse_height = setting._ellipse_height
            _crop_rect = setting._crop_rect
            
            try:
                _data = segment_impurity_image(filename, um_per_pix, image_width, intensity_threshold, disk_radius,
                                                    thresh_num, blur_num, min_particle_area, blocksize, c,
                                                    smooth_kernel_size, d, sigma_color, sigma_space,
                                                    footprint_num, ellipse_width, ellipse_height, _crop_rect)
            except ZeroDivisionError:
                print(f"ZeroDivisionError: Check um_per_pix for image {filename}.")
                unsegmented_images.append(filename)
                count+= 1
                self.processed_images.emit(count, len(settings))
                continue
           
            count += 1
            self.processed_images.emit(count, len(settings))
            self.impurity_data.append(_data)
        end = time.time()
        print("Segmentation finished in {} seconds".format(end-start))
        '''
        Changed segmentation complete signal to just emit impurity data list and a list of unsegmented images (if any)
        segmentation complete function in main_view class will set the image to the first image in the list of segmented images.
        Unsegemnted images resulting from divide by zero will be removed from the list of images.
        '''
        self._segmentation_complete.emit(self.impurity_data, unsegmented_images)

    @pyqtSlot(list)
    def run_sam_segmentation(self, settings):

        # def save_results_to_csv(sizes, spacings, out_path="impurity_results.csv"):
        #     # Pad shorter list with NaN so both columns align
        #     max_len = max(len(sizes), len(spacings))
        #     sizes_extended = sizes + [None] * (max_len - len(sizes))
        #     spacings_extended = spacings + [None] * (max_len - len(spacings))

        #     df = pd.DataFrame({ # This dataframe has too many spacing values per impurity, and the sizes are in the wrong format. 
        #         "Impurity Size (µm²)": sizes_extended,
        #         "Impurity Spacing (µm)": spacings_extended
        #     })

        #     # If file exists, append without header; otherwise, create new with header
        #     if os.path.exists(out_path):
        #         df.to_csv(out_path, mode="a", header=False, index=False)
        #     else:
        #         df.to_csv(out_path, index=False)

        #     print(f"Results appended to {out_path}")
        #     self._sam_segmentation_complete.emit(self.impurity_data)


        # # Calculates the area
        # # Does so by taking the sum of the mask in pixels and then calculating the square unit value using the size of the pixels
        # # Size of pixels is extracted from initial scale process
        # def compute_sizes(segmented_regions, um_per_pix): 
        #     sizes = []
        #     for mask in segmented_regions["masks"]:
        #         area_px = np.sum(mask)   # count True pixels
        #         area_um2 = area_px * (um_per_pix**2)
        #         sizes.append(area_um2)
        #     return sizes

        # def compute_spacings(segmented_regions, um_per_pix):
        #     centers = []
        #     for mask in segmented_regions["masks"]:
        #         ys, xs = np.where(mask)   # pixel coords where mask=True
        #         if len(xs) == 0:
        #             continue  # skip empty masks
        #         cx, cy = np.mean(xs), np.mean(ys)  # centroid in px
        #         centers.append((cx * um_per_pix, cy * um_per_pix))  # convert to µm
            
        #     distances = []
        #     for i in range(len(centers)):
        #         for j in range(i+1, len(centers)):
        #             dx = centers[i][0] - centers[j][0]
        #             dy = centers[i][1] - centers[j][1]
        #             distances.append(sqrt(dx*dx + dy*dy))
        #     return distances
    
        # for setting in settings:
        #     filename = setting.filename
        #     saved_crop_rect = setting._crop_rect
        #     '''
        #     each index of segmented regions dict contains:
        #     {
        #     "segmentation": np.ndarray,   # 2D boolean mask (True = inside region, False = outside)
        #     "area": int,                  # number of pixels in the mask 
        #     "bbox": [x, y, width, height],# bounding box around the mask
        #     "predicted_iou": float,       # SAM’s confidence score for the mask
        #     "stability_score": float,     # stability of the mask under perturbations
        #     "point_coords": np.ndarray,   # sampled input points that led to this mask
        #     "crop_box": [x0, y0, x1, y1]  # crop region used for this mask
        #     }
        #     '''
        #     segmented_regions, mask_path = sam_segmentation(filename=filename, crop_area=saved_crop_rect)

        #     print(f"The type of segmented_regions is: {type(segmented_regions)}")
     

        #     um_per_pix = setting.nm_per_pix / 1000.0  # nm → µm

        #     sizes = compute_sizes(segmented_regions, um_per_pix)
        #     spacings = compute_spacings(segmented_regions, um_per_pix)

        #     save_results_to_csv(sizes, spacings, "impurity_analysis.csv")
        start = time.time()
        count = 0
        unsegmented_images = []
        print("SAM Segmentation started")
        self.segmentation_started.emit(len(settings))
        self.processed_images.emit(0, len(settings))
        # returns pandas dataframe with impurity data
        self.impurity_data = []
        for setting in settings:
            '''Run segmentation algorithim on each image in the list of settings
                Segment_impurity_image runs the segmentation algorithm on the image and
                saves:
                - Segmented image as "segmented-<filename>.png" in SEG = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
                - impurity measurements as "<filename>_impurity_measurements.csv" in os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
                - coordinate spacing as "<filename>_coord_spacing.csv" in os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
                Those files are used to generate the PDF
            '''
            filename = setting.filename
            um_per_pix = setting.nm_per_pix / 1000.0  # nm to um
            image_width = setting.width_in_pix
            intensity_threshold = setting._intensity_threshold
            disk_radius = setting._disk_radius
            thresh_num = setting._thresh_num
            blur_num = setting._blur_num
            min_particle_area = setting._min_particle_area
            blocksize = setting._blocksize
            c = setting._c
            smooth_kernel_size = setting._smooth_kernel_size
            d = setting._d
            sigma_color = setting._sigma_color
            sigma_space = setting._sigma_space
            footprint_num = setting._footprint_num
            ellipse_width = setting._ellipse_width
            ellipse_height = setting._ellipse_height
            _crop_rect = setting._crop_rect
            
            try:
                _data = segment_impurity_image(filename, um_per_pix, image_width, intensity_threshold, disk_radius,
                                                    thresh_num, blur_num, min_particle_area, blocksize, c,
                                                    smooth_kernel_size, d, sigma_color, sigma_space,
                                                    footprint_num, ellipse_width, ellipse_height, _crop_rect, True)
            except ZeroDivisionError:
                print(f"ZeroDivisionError: Check um_per_pix for image {filename}.")
                unsegmented_images.append(filename)
                count+= 1
                self.processed_images.emit(count, len(settings))
                continue
           
            count += 1
            self.processed_images.emit(count, len(settings))
            self.impurity_data.append(_data)
        end = time.time()
        print("Segmentation finished in {} seconds".format(end-start))
        '''
        Changed segmentation complete signal to just emit impurity data list and a list of unsegmented images (if any)
        segmentation complete function in main_view class will set the image to the first image in the list of segmented images.
        Unsegemnted images resulting from divide by zero will be removed from the list of images.
        '''
        self._sam_segmentation_complete.emit(self.impurity_data, unsegmented_images)


    @pyqtSlot()
    def run_pdf(self, overlay, name):
        '''
        Generate the PDF from multiple segmented images and impurity data files.
        '''

        os.makedirs(COMBINED_IMPURITY_DATA, exist_ok=True)

        impurity_dfs = [] # Currently populates this list with all elements ending with impurity_measurements.csv - there will be old, unwanted files with this name! TODO!
        spacing_dfs = []

        # Signal to create progress dialog FIRST
        self.distribution_started.emit(8)

        #QThread.msleep(200)

        # Initial progress value
        self.analysis_progress.emit(0)
        
        for file in os.listdir(IMPURITY_DATA_FOLDER):
            file_path = os.path.join(IMPURITY_DATA_FOLDER, file)
            if file.endswith('_impurity_measurements.csv'):
                impurity_dfs.append(pd.read_csv(file_path))
            elif file.endswith('_coord_spacing.csv'):
                spacing_dfs.append(pd.read_csv(file_path))

        if not impurity_dfs:
            print("No impurity measurement CSV files found")
            return 
        if not spacing_dfs:
            print("No spacing CSV files found")
            return


        # Concatenate all data into single DataFrame
        impurity_df = pd.concat(impurity_dfs, ignore_index=True)
        spacing_df = pd.concat(spacing_dfs, ignore_index=True)
        impurity_df.to_csv(os.path.join(COMBINED_IMPURITY_DATA, 'combined_impurity_measurements.csv'), index=False)
        spacing_df.to_csv(os.path.join(COMBINED_IMPURITY_DATA, 'combined_coord_spacing.csv'), index=False)

        # Signal to create progress dialog FIRST
        self.distribution_started.emit(8)

        #QThread.msleep(200)

        # Initial progress value
        self.analysis_progress.emit(0)
    
        #Give UI thread time to process signals, 
        #this is crucial to ensure the progress dialog is created before the next signal is emitted
        QCoreApplication.processEvents()
        
        fit_and_plot(impurity_df, spacing_df, name, overlay, progress_signal=self.analysis_progress)
        print("Saving PDF...")
        extension = "_overlay" if overlay else "_no_overlay"
        # Save the combined PDF to the PDF_FOLDER
        self.finished.emit(os.path.join(PDF_FOLDER, f'combined_PDFs{extension}.png'))
        self.finished2.emit(os.path.join(PDF_FOLDER, 'Combined_PDF_2x2.png'))


    @pyqtSlot()
    def crater_analysis(self, crater_params: dict):
        self.crater_vol_started.emit(True)
        image_dir = crater_params['image_dir']
        start = crater_params['image_start']
        end = crater_params['image_end']
        roi = crater_params['roi']
        vx = crater_params['vx']
        vy = crater_params['vy']
        vz = crater_params['vz']
        contor_threshold = crater_params['contour_threshold']
        fitting_threshold = crater_params['fitting_threshold']
        binary_threshold = crater_params['binarization_threshold']
        craterData = CraterVolume.run_crater_analysis(image_dir, roi, start, end, binary_threshold, contor_threshold, fitting_threshold, vx, vy, vz)
        self.crater_vol_finished.emit(craterData)


class MainController(QObject):
    def __init__(self, parent:QObject = None):
        super().__init__(parent=parent)

        self._segmentation_worker = SegmentationWorker() #Worker object to handle segmentation
        self._segmentation_thread = QThread() #Worker thread to allow segmentation without stopping user interaction
        self._segmentation_worker.moveToThread(self._segmentation_thread)
        self._segmentation_thread.start()

    @property
    def segmentation_worker(self):
        return self._segmentation_worker

    def get_image(self):
        file, _ = QFileDialog.getOpenFileName(self.parent(),
                                           'Load Image',
                                           os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App'),
                                           'Image Files (*.png *.jpg *.tif)')
        return file
    
    def get_images(self):
        '''
        Pyqt5 has very limited control over native os file dialogs and does not support
        selecting multiple files and folders at the same time. Prompting the user to select a folder or files
        is essentially our best option that we can accomplish in a reasonable amount of time. Found a workaround
        on stack overflow, but it is very ugly.
        '''
        dialog = QtWidgets.QMessageBox()
        dialog.setWindowTitle("Upload Choice")
        dialog.setText("Would you like to upload individual files or a folder?")
        file_button = dialog.addButton("Files", QtWidgets.QMessageBox.YesRole)
        folder_button = dialog.addButton("Folder", QtWidgets.QMessageBox.NoRole)
        exit_button = dialog.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)

        dialog.exec_()
        clicked_button = dialog.clickedButton()

        # Check if X button or Cancel was pressed
        if clicked_button is None or clicked_button == exit_button:
            return []
            
        image_files = []

        if clicked_button == file_button:
            image_files, _ = QFileDialog.getOpenFileNames(self.parent(),
                              "Select Files",
                              os.path.expanduser('~'),
                              'Image Files (*.png *.jpg *.tif *.jpeg)')
            
        elif clicked_button == folder_button:
            folder = QFileDialog.getExistingDirectory(self.parent(),
                                "Select Folder",
                                os.path.expanduser('~'))
            if folder:
                for f in os.listdir(folder):
                    if f.lower().endswith(('.png', '.jpg', '.tif', '.jpeg')):
                        image_files.append(os.path.join(folder, f))
                
        return sorted(image_files) if image_files else []

    def close(self):
        self._segmentation_thread.quit()