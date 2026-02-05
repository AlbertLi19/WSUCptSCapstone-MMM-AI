import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from skimage import morphology, measure
import csv

def run():
    # Set the directory path where the images are located.
    folder_name = "Select_SEM_Images" #input name of folder here, folder must be in res
    path = os.getcwd()  + "\\res\\" + folder_name


    # Parameters that the user can change to adjust image processing:
    min_particle_area = 300  # Minimum area of particles to consider. Arbitrary
    bottom_crop = 4376 - 4096  # Pixels to crop from the bottom. Maybe different for some pictures
    disc_radius = 1  # Radius for disk structuring element used for morphological closing.
    smooth_kernel_size = 3  # Kernel size for Gaussian smoothing. Arbitrary
    sensetivity = 0.07 # effects how much black and white shows up in the image

    # Loop over all files in the specified directory.
    for filename in os.listdir(path):
        if filename.endswith('.tif') or filename.endswith('.jpg') or filename.endswith('.png'):  # Check for image file extensions.
            loc = os.path.join(path, filename)
            original_image = cv2.imread(loc, cv2.IMREAD_GRAYSCALE)  # Read the image in grayscale.
            watershed_img = cv2.imread(loc) # Grayscaling done later, after it has been cropped. This can probebly be optimised down to grayscaling then cropping
            
            if watershed_img is None:
                print(f"Warning: Could not read {filename}. Skipping...")
                continue
            
            # image prep:
            watershed_img = watershed_img[:-bottom_crop, :] # cut off bottom image specifications
            gray = cv2.cvtColor(watershed_img,cv2.COLOR_BGR2GRAY) # gray scale
            gray = cv2.GaussianBlur(gray, (smooth_kernel_size, smooth_kernel_size), 0) # blurring can close really close edges
            ret, thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU) # I assume if the image comes out black and white instead of white and black you can fix thatr here
            # image prep
            
            
            
            # Compute the new scale factor based on the image dimensions
            image_height, image_width = original_image.shape
            image_dimension_in_microns = 200  # 200x200 micron image
            scale_factor = image_dimension_in_microns / image_width  # Assuming square pixels and square images
            print(f"Dimensions of original image {filename} with scale factor {scale_factor}: {original_image.shape}")
            
            
            
            # Noise removal
            kernel = np.ones((3,3),np.uint8)
            opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 2)

            # Sure background area
            sure_bg = cv2.dilate(opening,kernel,iterations=3)

            # Finding sure foreground area
            dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
            ret, sure_fg = cv2.threshold(dist_transform,0.05*dist_transform.max(),255,0)

            # Finding unknown region
            sure_fg = np.uint8(sure_fg)
            unknown = cv2.subtract(sure_bg,sure_fg)
            
            # Marker labelling
            ret, markers = cv2.connectedComponents(sure_fg)

            # Add one to all labels so that sure background is not 0, but 1
            markers = markers+1

            # Now, mark the region of unknown with zero
            markers[unknown==255] = 0

            # create markers, currently I don't use this.
            markers = cv2.watershed(watershed_img, markers)
            
            # This part hasn't run before, and I don't know why, if it did line 64 would be useful.
            # original_image[markers == -1] = [255,0,0]
            
            
            # I'm using sure_fg or sure foreground as the sample for recognition, to use another varieble this needs to be changed
            sure_fg = morphology.remove_small_objects(sure_fg, min_size=min_particle_area)
            sure_fg = morphology.remove_small_holes(sure_fg, area_threshold=min_particle_area)
            sure_fg = morphology.closing(sure_fg, morphology.disk(disc_radius))
    
            label_image = measure.label(sure_fg)
            regions = measure.regionprops(label_image)
            centroids = [region.centroid for region in regions]
            
            if not regions:
                print(f"Warning: No particles detected in {filename}. Skipping...")
                continue
            
            
            # Apply scale factor to equivalent_diameters and area
            equivalent_diameters = [r.equivalent_diameter * scale_factor for r in regions]
            areas = [r.area * scale_factor * scale_factor for r in regions]


            fig, axs = plt.subplots(1, 4, figsize=(15, 5))
            axs[0].imshow(original_image, cmap=plt.cm.gray) # image of the original image for comparison
                                                    # Next image is done twice to avoid visual overcrowding
            axs[1].imshow(sure_fg, cmap=plt.cm.gray) # Image being used with all diameters measured
            axs[2].imshow(sure_fg, cmap=plt.cm.gray) # Same image but with area displayed instead

            plt.title(filename)
            
            header = ["Number", "Diameter", "Area","Region"]
            with open (filename+"_data.csv","w",encoding="UTF8",newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                # Watershed based variables saved
                for idx, (region, diameter, area) in enumerate(zip(regions, equivalent_diameters, areas)):
                    y, x = centroids[idx]
                    # axs[1].text(x, y, f"{diameter:.2f}", color="red", size=8, ha="center", va="center") # applying diameter
                    # axs[2].text(x, y, f"{area:.2f}", color="red", size=8, ha="center", va="center") # applying area
                    axs[0].text(x, y, f"#{idx}", color="red", size=6, ha="center", va="center") # applying area
                    writer.writerow([idx,diameter,area,region])
    
            # from here code is almost completely unchanged, only difference the is no nearest neighbor code becuase that wasn't something we are looking for and it takes up a ton of time
            
            # Scaled centroids
            scaled_centroids = [(y * scale_factor, x * scale_factor) for y, x in centroids]

            nearest_neighbor_distances = []
            centroids = [r.centroid for r in regions]  # This gives the unscaled centroids

            # writing area file
            areas = [r.area * scale_factor * scale_factor for r in regions]
            area_df = pd.DataFrame(areas, columns=["Particle_Area"])
            # area_df.to_csv(os.path.join(path, 'particle_areas.csv'), index=False)

            #plot histogram of areas
            # area_df = area_df.groupby('Particle_Area').size().reset_index(name='Count')
            # print(area_df)

            # Plot histogram
            axs[3].hist(area_df["Particle_Area"])

            # writing additionall properties files
            additional_props = pd.DataFrame(
                list(zip(
                    scaled_centroids,
                    [r.orientation for r in regions],
                    [r.major_axis_length * scale_factor for r in regions],
                    [r.minor_axis_length * scale_factor for r in regions],
                    [major / minor if minor != 0 else np.nan for major, minor in zip([r.major_axis_length for r in regions], [r.minor_axis_length for r in regions])],
                    nearest_neighbor_distances
                    )),
                columns=["Centroid", "Orientation", "Major_Axis", "Minor_Axis", "Aspect_Ratio", "Nearest_Neighbor_Distance"]
                )
            # additional_props.to_csv(os.path.join(path, 'scaled_additional_properties.csv'), index=False)
            
            # save each segmented image to "segmented" folder, filename is the same, file extension is .png
            plt.savefig("segmented\\"+filename.split('.')[0])
