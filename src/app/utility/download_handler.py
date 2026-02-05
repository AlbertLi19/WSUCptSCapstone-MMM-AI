from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os
import shutil
from widgets.popup_dialogs import DownloadDataDialog
import pandas as pd
import pyqtgraph as pg
from pyqtgraph import exporters
import numpy as np

class DownloadHandler(QWidget):
    def __init__(self, parent=None, data_type=None, image_settings=None):
        super().__init__(parent)
        self.view = parent
        self.data_type = data_type
        self._image_settings = image_settings

    def download(self):
        '''
        Parameters: data_type (str) - either "segmentation" or "analysis". This determines which tab the download dialog box will be created for.
        Returns: None
        Function creates a dialog box for downloading data. The user can select which data to download by checking the appropriate boxes. Then the
        path to the selected data corresponding to the check bod will be added to data_paths. The user selects the location of the data to be downloaded
        to, then all items in data_paths are copied to the selected location.
        '''
        SEGMENTED_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
        IMPURITY_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
        COMBINED_IMPURITY_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'Combined_Impurity_Data')   # combined impirity/coord spacing for all images
        PDF_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','PDF Images')

        self.data_type = self.data_type.lower()
        if self.data_type not in ['segmentation', 'analysis']:
            raise ValueError("Invalid type. Must be 'segmentation' or 'analysis'.")
        
        dialog = DownloadDataDialog(parent=self.view, data_type=self.data_type)
        result = dialog.exec()
        if not result:  # if the user cancels the dialog, do nothing
            return
        if not dialog.segmentedImagesBox.isChecked() and not dialog.histogramBox.isChecked() and not dialog.impurityDataBox.isChecked() and \
            not dialog.datasetBox.isChecked() and not dialog.datasetoverlayBox.isChecked() and not dialog.datasetImpurityBox.isChecked():
            return # if no boxes are checked, do nothing
        
        save_directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save Data")
        if save_directory:  # If the user didn't cancel
            # Get the save directory from the dialog
            print(f"Selected directory: {save_directory}")
        else: # if the user cancels the dialog, do nothing
            print("No directory selected, cancelling download.")
            return
        
        if self.data_type == "segmentation": # if active tab is segmentation
            # Download segmented images, histograms, and impurity data
            if dialog.segmentedImagesBox.isChecked():  # download segmented images
                print("Downloading Segmented images")
                for file in os.listdir(SEGMENTED_FOLDER):
                    filepath = os.path.join(SEGMENTED_FOLDER, file)
                    shutil.copy(filepath, save_directory)

            if dialog.histogramBox.isChecked():        # download image historgrams
                print("Downloading Histograms")
                # referenced from _update_hist_plot
                histogram_types = ['Size','Orientation','Aspect_Ratio']
                settings = self._image_settings

                if settings is not None:
                    histogram_data = []
                    for setting in settings:
                        fname = setting.filename.split('.')[0] 
                        image_histogram_data = {}
                        image_histogram_data['filename'] = fname
                        if setting._impurity_data is not None:
                            for col_name in histogram_types:
                                if col_name in setting._impurity_data.columns:
                                    image_histogram_data[col_name] = setting._impurity_data[col_name]
                            histogram_data.append(image_histogram_data)
                        else:
                            continue
                        if histogram_data:
                            for data_item in histogram_data:
                              
                                filename = data_item['filename']
                                for col_name in data_item.keys():
                                    if col_name == 'filename':
                                        continue
                                    fname = data_item['filename']
                                    y,x = np.histogram(data_item[col_name],bins=10)
                                    
                                    filename = (filename).split('.')[0]
                                    histogram_fname = filename + f'_{col_name}_histogram.png'
                                    
                                    # Create an offscreen QGraphicsScene
                                    scene = pg.GraphicsScene()
                                    plot_item = pg.PlotItem()
                                    scene.addItem(plot_item)
                                    
                                    # Add histogram data to the plot
                                    bgi = pg.BarGraphItem(x0=x[:-1], x1=x[1:], height=y, pen='w', brush=(0,0,255,150))
                                    plot_item.addItem(bgi)
                                    plot_item.setTitle(f"{col_name} Distribution")
                                    plot_item.setLabel('left', 'Frequency')
                                    plot_item.setLabel('bottom', col_name)
                                    
                                    # Set the size for the output image
                                    view = pg.GraphicsView()
                                    view.setCentralItem(plot_item)
                                    view.resize(800, 600)
                                    
                                    # Export the plot directly without showing it
                                    export_path = os.path.join(save_directory, os.path.basename(histogram_fname))
                                    exporter = pg.exporters.ImageExporter(plot_item)
                                    exporter.export(export_path)
                            
            if dialog.impurityDataBox.isChecked():     # download impurity data csv for each image
                print("Dowlading individual impurity data")
                for file in os.listdir(IMPURITY_DATA):
                    filepath = os.path.join(IMPURITY_DATA, file)
                    shutil.copy(filepath, save_directory)
                
        else: # if active tab is analysis
            if dialog.datasetBox.isChecked():          # download the dataset histogram
                print("Downloading Dataset histogram (No Overlay)")
                for file in os.listdir(PDF_FOLDER):
                    if "_no_overlay" in file:
                        filepath = os.path.join(PDF_FOLDER, file)
                        shutil.copy(filepath, save_directory)

            if dialog.datasetoverlayBox.isChecked():   # download the dataset histogram with PDF overlay
                print("Download dataset histogram (with Overlay)")
                for file in os.listdir(PDF_FOLDER):
                    if "_overlay" in file and "no_overlay" not in file:
                        # Only copy files with "_overlay" in the name and not "_no_overlay"
                        filepath = os.path.join(PDF_FOLDER, file)
                        shutil.copy(filepath, save_directory)

            if dialog.datasetImpurityBox.isChecked():  # download the impurity data csv for the dataset
                print("Downloading combined impurity data")
                for file in os.listdir(COMBINED_IMPURITY_DATA):
                    filepath = os.path.join(COMBINED_IMPURITY_DATA, file)
                    shutil.copy(filepath, save_directory)



        