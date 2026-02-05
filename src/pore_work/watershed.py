import os
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import csv

#IMAGE SIZE
#PX: 6144 x 4096
#1um = 328px

#image parameters
bottom_crop = 4376 - 4096  # Pixels to crop from the bottom. Maybe different for some pictures
smooth_kernel_size = 31  # Kernel size for Gaussian smoothing
pxperum = 1481 #pixels per micrometer
opening_iterations = 15 #iterations for morphological opening
dilation_iterations = 15 #iterations for dilation after morphological opening
dist_transform_multiplier = 0.005 #minimum distance from sure_bg for finding sure_fg pixels

folder_name = "Select_SEM_Images" #input name of folder here, folder must be in res
path = os.getcwd()  + "\\res\\" + folder_name

def watershedOnImage(filename):
    #load image into cv
    filepath = os.path.join(path,filename)
    img = cv.imread(filepath)
    img = img[:-bottom_crop, :] #crop bottom of image

    #Otsu's binarization to find approximate estimations of pores
    gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (smooth_kernel_size, smooth_kernel_size), 0) # blurring can close really close edges
    _, thresh = cv.threshold(gray,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)

    # noise removal
    kernel = np.ones((3,3),np.uint8) #TODO: increase the kernel for opening and dilation
    opening = cv.morphologyEx(thresh,cv.MORPH_OPEN,kernel, iterations = opening_iterations)

    # sure background area
    sure_bg = cv.dilate(opening,kernel,iterations=dilation_iterations)

    # Finding sure foreground area
    dist_transform = cv.distanceTransform(sure_bg,cv.DIST_L2,5) #TODO: try using sure_bg instead of opening
    _, sure_fg = cv.threshold(dist_transform,dist_transform_multiplier*dist_transform.max(),255,0) #changing dist_transform multiplier makes a big difference

    # Finding unknown region
    sure_fg = np.uint8(sure_fg)
    unknown = cv.subtract(sure_bg,sure_fg)

    # Marker labelling
    _, markers = cv.connectedComponents(sure_fg)

    # Add one to all labels so that sure background is not 0, but 1
    markers = markers+1

    # Now, mark the region of unknown with zero
    markers[unknown==255] = 0

    #apply watersehd
    watershed = cv.watershed(img, markers)
    img[watershed == -1] = [255,0,0]
    # img[watershed != -1] = [255,255,255]

    #show final image
    fig, axs = plt.subplots(1,4,figsize=(15,5))
    axs[0].imshow(img)
    axs[1].imshow(watershed, cmap='jet')
    axs[2].imshow(sure_bg)
    axs[3].imshow(sure_fg)

    # areas = {}
    diameters = {}

    # Iterate over each connected component
    for i in range(1, markers.max() + 1):
        #get each pixel in each pore
        centroid = np.where(markers == i)

        if centroid[0].size > 0:
            #save the area as amount of pixels
            # areas[i] = centroid[0].size

            #get centroid x and y
            centroid_x = np.mean(centroid[1])
            centroid_y = np.mean(centroid[0])

            # Calculate the convex hull of the component
            points = np.column_stack((centroid[1], centroid[0]))
            hull = cv.convexHull(points, returnPoints=False)
            hull_points = points[hull[:, 0]]
            
            # Calculate the pairwise distances between points on the convex hull
            distances = np.linalg.norm(hull_points[:, None] - hull_points, axis=-1)
            
            # Find the maximum distance
            max_distance_index = np.unravel_index(np.argmax(distances), distances.shape)
            max_distance = distances[max_distance_index]
            diameters[i] = max_distance

            #mark watershed image with pore number
            axs[1].text(centroid_x, centroid_y, str(i), color='white', fontsize=8)

    # #print pore areas for each label
    # print("Pore Areas:")
    # for key in areas:
    #     #format area to 5 decimal places so it looks nice
    #     area = str(areas[key]/pxperum).split('.')
    #     print("Pore #"+str(key)+":", area[0]+"."+area[1][:5]+"um^2")

    # print("\nPore Diameters (Longest Distance Between Sides):")
    with open("segmented\\"+filename.split('.')[0]+'_diameters.csv','w',encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Pore","Diameter"])
        sum = 0.0
        count = 0.0
        for key in diameters:
            if key != 1:
                #format diameter to 5 decimal places so it looks nice
                # diameter = str(diameters[key]/pxperum).split('.')
                diameter = diameters[key]/pxperum
                writer.writerow([str(key),str(diameter)])
                sum += diameter
                count += 1.0
                # print("Pore #"+str(key)+":", diameter[0]+"."+diameter[1][:5]+"um")
        writer.writerow(['avg',str(sum/count)])

    plt.savefig("segmented\\"+filename.split('.')[0])

if __name__ == "__main__":
    for filename in os.listdir(path):
        watershedOnImage(filename)