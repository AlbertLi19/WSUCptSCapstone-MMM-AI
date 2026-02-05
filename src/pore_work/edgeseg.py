import os
from skimage.feature import canny
from skimage import morphology
from scipy import ndimage as ndi
import cv2 as cv
import matplotlib.pyplot as plt

bottom_crop = 4376 - 4096  # Pixels to crop from the bottom. Maybe different for some pictures
smooth_kernel_size = 51  # Kernel size for Gaussian smoothing. Arbitrary
min_object = 21

folder_name = "Select_SEM_Images" #input name of folder here, folder must be in res
path = os.getcwd()  + "\\res\\" + folder_name

for filename in os.listdir(path):
    #load image into cv
    filepath = os.path.join(path,filename)
    img = cv.imread(filepath)
    img = img[:-bottom_crop, :] #crop bottom of image

    #Otsu's binarization to find approximate estimations of pores
    gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (smooth_kernel_size, smooth_kernel_size), 0) # blurring can close really close edges
    _, thresh = cv.threshold(gray,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)

    edges = canny(thresh)

    fig, ax = plt.subplots(1,3,figsize=(15, 5))
    ax[0].imshow(edges, cmap=plt.cm.gray)
    ax[0].set_title('Canny detector')
    ax[0].axis('off')


    fill_pores = ndi.binary_fill_holes(edges)

    ax[1].imshow(fill_pores, cmap=plt.cm.gray)
    ax[1].set_title('filling the holes')
    ax[1].axis('off')


    pores_cleaned = morphology.remove_small_objects(fill_pores, min_object)

    ax[2].imshow(pores_cleaned, cmap=plt.cm.gray)
    ax[2].set_title('removing small objects')
    ax[2].axis('off')

    plt.show()