## Place known bugs here for fixing later
### **Move issue to bottom after fixing**

### Parameter Text Box Shifts GUI 
**How to recreate**: Load images, press any button that triggers the text box to appear and it will cause the GUI to shift over, which appears
a little strange. Should be an easy fix
**Possible fix**: Position text box elsewhere

### Add units to image segmentation parameters
Error/Bug: The units are unclear on the settings which may make it confusing to the user

### Divide by zero error
How to recreate: Load in images, sometimes the min particle area is too small causing a divide by zero error, even if it is not zero
**Error Message**: looking for segmented-61620A_IP_09_53x35_04.png in C:\Users\nelso\AppData\Local\Segmentation App\Impurity_Segmented_Images
Segmentation started
Traceback (most recent call last):
  File "C:\Users\nelso\Desktop\Computer Science\CS School Projects\Capstone\-wsum-fullstackapp-\src\app\controllers\main_controller.py", line 55, in run_segmentation
    _data = segment_impurity_image(filename, px_per_um, intensity_threshold, disk_radius,
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\nelso\Desktop\Computer Science\CS School Projects\Capstone\-wsum-fullstackapp-\src\app\segmentation_scrips\impurity_segmentation.py", line 99, in segment_impurity_image
    aspect_ratio = [ma / mi for ma, mi in zip(major, minor)] # In pixels
                    ~~~^~~~
ZeroDivisionError: float division by zero
**Possible Fix**: Try/catch block around that code

### Run segmentation more than once 
**How to recreate**: self explanatory
Need to make sure that the settings are added correctly.

### Unable to reset values
**Issue**: There is no reset button that clears the app back to its default state (no settings and no images)
**Fix**: add a button to do so

### Histograms have no label
**Fix**: add labeling to histograms.See _update_hist_plot function

### Unable to select/deselect all fitter functions
**Fix**: add button to do so. 


## Fixed Issues
### Load images bug
**How to recreate**: Press load images, and exit out without loading anything
**Error/Bug**:  File "C:\Users\nelso\Desktop\Computer Science\CS School  \Projects\Capstone\-wsum-fullstackapp-\src\app\views\main_view.py", line 479, in _load_images \
    self._images = self._controller.get_images()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\nelso\Desktop\Computer Science\CS School Projects\Capstone\-wsum-fullstackapp-\src\app\controllers\main_controller.py", line 153, in get_images \
    return sorted(image_files) if image_files else [] \
                                  ^^^^^^^^^^^ \
UnboundLocalError: cannot access local variable 'image_files' where it is not associated with a value 
**Possible fix**: check if image files is returning as none, or check if the return value of the popup is false, indicating that it was closed out of

### Uploading images multiple times
**How to recreate**: Upload images and and apply settings, then upload images again
**Issue**: The images overwrite the existing images and the settings are applied to them. 
**Possible fix**: The image/ setting arrays need to be checked if they are not empty and appended to if true
