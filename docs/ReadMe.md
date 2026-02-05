# <div align="center">WSUM-PythonApp: Improving Mechanical Performance for Extreme Environments</div>

#### <div align="center">Daniel Book, Daniel Lee, and Douglas Takada</div>
<div align="center">Multiscale Mechanics and Materials Laboratory</div>
<div align="center">Client: Dr. Arezoo Zare</div>

## Overview
This program was developed to automatically process SEM images using image segmentation to identify various measurements from breakage patterns called impurities for statistical analysis.

## Image Segmentation Process
* Image/set of images are selected as input by the user
* Crops out the bottom part of the SEM image(s)

### Blur:
* There are four image blurring options:
  * Average Blur
  * Gaussian Blur
  * Median Blur
  * Bilateral Filtering
* First three use the smooth_kernel_size variable that must be positive and odd
* Bilateral Filtering has its own variables (d, sigmaColor, sigmaSpace)
* Blurring is optional and is not requirement for thresholding/image segmentation
* https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html

### Binary Thresholding:
* There are three thresholding options:
  * Global Thresholding
  * Adaptive Thresholding
    * Mean
    * Gaussian
  * Otsu's Binarization
* Global Thresholding has a thresh_val variable that must be between 0 and 255
* Adaptive Thresholding use the blockSize and C variables
* Otsu's Binarization automatically determines the optimal thresholding value
* https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html 

### Morphology:
* Removes small objects and small holes from the image(s) that are smaller than a min_paticle_area variable value
* Performes closing (dilation then erosion) on the image based on a footprint option:
  * Disk
  * Ellipse
* Disk has a disk_radius variable
* Ellipse use the ellipse_width and ellipse_height variables
* https://scikit-image.org/docs/stable/api/skimage.morphology.html#

## Data Extraction and Visualization
* The data for the segmented image(s) is stored in the regions variable from measure.regionprops(), containing important measurements such as:
  * centroids
  * major_axis_length
  * minor_axis_length
  * orientation
* https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.regionprops
* From those values, we are looking for four types of data:
  * Size, which is major_axis_length
  * Aspect Ratio, which is major_axis_length/minor_axis_length
  * Orientation, which is converted to degrees
  * Spacing, which is the nearest neighbor for each impurity identified

### Spacing/Nearest Neighbor:
* The nearest neighbor of each impurity is calculated by comparing each one to all the others then calculating the distances between them, keeping track of the smallest one and its centroid/x,y coordinates

### Raw Data
* The program creates two csv files (per image) that contain all relevant measurements:
  * [Name of image]_impurity_measurements.csv, which contains size, aspect ratio, and orientation
  * [Name of image]_coord_spacing.csv, which contains the impurity/centroid nearest neighbor pairs and their minimum distance
* Scale factor is applied to the data to convert it from pixels to microns


### Ellipse Tracing
* Within an image(s), for every impurity/region:
  * Major axis is plotted, in red
  * Minor axis is plotted, in red
  * An ellipse shape is then fitted based on the two axes, in blue
* Example Figure:
<p align="center">
<img src="segmented-61620A_IP_09_53x35_01-1.png" width="700"/>
</p>

## Statistical Analysis
### Data Preprocessing
* Read input CSV files using pandas.
* Extract and clean numerical data for size, aspect ratio, orientation, and spacing columns
* https://pandas.pydata.org/

### Probability Densitiy Function Fitting
* Using the Fitter library to call scipy.stats statisitical distribution find the best fit for the data
* Save distribution name and parameters
* https://docs.scipy.org/doc/scipy/reference/stats.html
* https://fitter.readthedocs.io/en/latest/

### Aggragatted data
* Using k fold cross validation, find the optimal bandwidth parameter for the kerndel density estimation (KDE) function for the given data
* Using the KDE found previously, find the Maximum Likelihood Estimation (MLE) and Full Width Half Max (FWHM)
* MLE is calculated by extracting the max point of the KDE and saving the x and y coordinate to use for further calculations.
* FWHM is calculated by finding the max y point of the KDE and dividing it in half to find its middle point and finding the width between the first index that is greater than the half point and the last index above the half point. Because of this implimenation this does not work for bimodal distributions.

### Plot Results
* Create 4 respective plots for each of the features we are analyzing
* Plot original data in histogram format
* Plot MLE and FWHM
* Plot best fitted PDF
* Create a double y plot for each plot where one is for the histogram and the other for the pdf distribution
* https://matplotlib.org/

### Save Results
* save MLE, FWHM, and plots into CSV and PNG.

## GUI
* The GUI allows users to visually access the impurity segmentation and analysis scripts.

### Load Image
* This button allows the user to load an impurity SEM image from a selected folder. It is then displayed on the screen for the user to see.

### Set Scale
* This button enters the GUI into a scaling mode, allowing the user to specify the real-life length of the impurities, which is used to scale the segmentation results to real distance values rather than pixel values.

### Crop
* This button enters the GUI into a cropping mode, which can be used to crop out portions of the image such as the information tab on the bottom.

### Parameter Specification
* The menu on the left-hand side of the screen can be used to fine-tune the parameters used in the segmentation algorithm. Default values are shown in the bottom left.

### Run Segmentation
* Pressing this button will begin the segmentation of the cropped image. The segmentation script will finish running after a few seconds, while the analysis script will take around 2 minutes to complete.

### Visualization Dropdown Menu
* The dropdown menu on the bottom left of the screen allows the user to switch between viewing the segmented image, segmentation data histograms, and the generated probability distribution functions.

### Code File Structure
* PyQt5 - The GUI relies on the PyQt5 graphics library. The program mostly uses the event loop and the signal/slot mechanisms, along with the built-in widgets.
* main.py - This is the file that is used to run the entire program. It imports the necessary modules that are within the 'app' folder
* views - This folder contains the files that are responsible for displaying buttons and widgets to the user, and handling the user interaction with those buttons.
* widgets - This folder contains the files that make up the custom widgets used in the GUI.
* controllers - This folder contains the controller files, which are used to handle the multithreading of the application.
* segmentation_scripts - This folder contains the segmentation scripts that are used on the images.
* analysis_scripts - This folder contains the scripts that are used to generate PDFs based on the segmentation data.

### Windows File Structure
* All of the program data can be found in the folder "C:/Users/*username*/AppData/Local/Segmentation App". From there, the necessary subfolders can be found.
* Impurity_Data - This folder contains the csv files that are generated as a result of the segmentation script.
* Impurity_Segmented_Images - This folder contains the segmented images that are generated as a result of the segmentation script.
* PDF Images - This folder contains the probability distribution function graphs that are generated as a result of the analysis script.
* Ready Images - This folder contains the cropped images. It acts as a place to store images during the runtime of the program.

## Acknowledgements
We would like to express our deepest gratitude to Washington State University, whose resources and support made this research possible. We are particularly thankful to Dr. Arezoo Zare and Dr. Ananth Jallepalli for their insightful feedback and invaluable guidance throughout this work. We are also grateful to our families and friends for their patience and encouragement throughout the research process. Finally, we acknowledge the contributions of all participants who took part in this study, as their involvement was essential to its success. 
