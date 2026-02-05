import os
import cv2
import matplotlib
matplotlib.use('Agg')
from matplotlib import patches
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
from skimage import morphology, measure
from PyQt5.QtCore import QRect
from segmentation_scrips.SAM_segmentation import sam_automatic_hardware_optimization
from scipy.spatial import distance_matrix

IMAGES = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_SEM_Images','61620A_IP_09_53x35')
DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Data')
SEG = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')
IMPURITY_DATA_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App', 'Impurity_Data')              #individual impurity data/coord spacing
SAM_IMAGE = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','SAM_Data')

def sam_outputs_to_label_image(outputs):
    """
    Convert SAM outputs['masks'] into a labeled image compatible
    with extract_pore_data and regionprops.
    """
    if "masks" not in outputs or len(outputs["masks"]) == 0:
        return None

    h, w = outputs["masks"][0].shape
    label_image = np.zeros((h, w), dtype=np.int32)

    label_id = 1
    for mask in outputs["masks"]:
        label_image[mask.astype(bool)] = label_id
        label_id += 1

    return label_image


# Define the saved cropping rectangle
saved_crop_rect = QRect(0, 0, 1025, 1025)

def segment_impurity_image(filename:str, um_per_pix:float, width_in_px:int, intensity_threshold:int,
                           disk_radius:int, thresh_option:int, blur_option:int,
                           min_particle_area:int, blockSize:int, C:int,
                           smooth_kernel_size:int, d:int, sigmaColor:int,
                           sigmaSpace:int, footprint_option:int,
                           ellipse_width:int, ellipse_height:int, saved_crop_rect: QRect = None, Use_SAM:bool = False): # Use_SAM condition = True for Kenan's SAM implementation
    

    # Global Variables
    thresh_val = intensity_threshold
    test = False
    
    # Loop over all files 
    folder = [filename]
    for file in folder:
        if file.endswith('.tif') or file.endswith('.jpg') or file.endswith('.png'):  
            original_image = cv2.imread(file, cv2.IMREAD_GRAYSCALE)  # Read the image in grayscale.
            I = original_image
            # Image segmentation method
            if original_image is None:
                print(f"Warning: Could not read {file}. Skipping...")
                continue
            
            if saved_crop_rect is not None:
                # Apply cropping using the saved rectangle
                I = original_image[saved_crop_rect.y():saved_crop_rect.y() + saved_crop_rect.height(),
                                saved_crop_rect.x():saved_crop_rect.x() + saved_crop_rect.width()]

            # Determine image dimensions and compute pixel-based morphological parameters.
            # width_in_px is intended to indicate the image width in pixels (if provided).
            img_h_px, img_w_px = I.shape[0], I.shape[1]
            image_width_px = width_in_px if (width_in_px and width_in_px > 0) else img_w_px

            disk_radius_px = int(disk_radius)
        
            min_particle_area_px = int(min_particle_area)

            ellipse_width_px = int(ellipse_width)

            ellipse_height_px = int(ellipse_height)

            # if Use_SAM:
            #     temp_path = os.path.join(SAM_IMAGE, "temp_cropped_input.png")
            #     cv2.imwrite(temp_path, I)

            #     outputs, mask_path = sam_segmentation(temp_path)

            #     #outputs, mask_path = sam_segmentation(file) # While Save Outputs is true?

            #     #base_name = os.path.splitext(os.path.basename(file))[0]
            #     #sam_mask_path = os.path.join(SAM_IMAGE, f"{base_name}_preprocessed_mask_000.png")
            #     sam_mask_path = os.path.join(SAM_IMAGE, "temp_cropped_input_preprocessed_mask_000.png")

            #     thresh = cv2.imread(sam_mask_path, cv2.IMREAD_GRAYSCALE)
            #     if thresh is None:
            #         print(f"Warning: Could not read SAM mask at {sam_mask_path}. Skipping...")
            #         continue

            #     thresh = thresh < 127

            if Use_SAM:
                print("YES WE HERE")
                temp_path = os.path.join(SAM_IMAGE, "temp_cropped_input.png")
                cv2.imwrite(temp_path, I)

                outputs = sam_automatic_hardware_optimization(
                    image_path=temp_path,
                    show_results=False,
                    save_masks=False
                )

                label_image = sam_outputs_to_label_image(outputs)

                if label_image is None:
                    print("Warning: SAM produced no masks")
                    continue

                thresh = label_image > 0

                #maskList = outputs["masks"]
                #thresh = maskList[1]
                # thresh = np.array(thresh)
                # if thresh.dtype != bool:
                #     thresh = thresh > 0.5
                # thresh = ~thresh
            else:
                #apply blur to image
                if blur_option == 0:
                    I = cv2.blur(I, (smooth_kernel_size, smooth_kernel_size))
                elif blur_option == 1:
                    I = cv2.GaussianBlur(I, (smooth_kernel_size, smooth_kernel_size), 0)
                elif blur_option == 2:
                    I = cv2.medianBlur(I, smooth_kernel_size)
                elif blur_option == 3:
                    I = cv2.bilateralFilter(I, d, sigmaColor, sigmaSpace)

                #Thresholding method
                if thresh_option == 0:
                    ret, global_thresh = cv2.threshold(I, thresh_val, 255, cv2.THRESH_BINARY)
                    thresh = global_thresh
                elif thresh_option == 1:
                    adapt_thresh = cv2.adaptiveThreshold(I, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, blockSize, C)
                    thresh = adapt_thresh
                elif thresh_option == 2:
                    adapt_thresh = cv2.adaptiveThreshold(I, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize, C)
                    thresh = adapt_thresh
                elif thresh_option == 3:
                    ret, otsu_thresh = cv2.threshold(I, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    thresh = otsu_thresh

                if thresh is None:
                    print(f"Warning: Could not threshold {file}. Skipping...")
                    continue
                
                # Morphological operations (operate in pixel units)
                thresh = thresh.astype(bool)
                thresh = morphology.remove_small_objects(thresh, min_size=min_particle_area_px)
                thresh = morphology.remove_small_holes(thresh, area_threshold=min_particle_area_px)

                if footprint_option == 0:
                    thresh = morphology.closing(thresh, morphology.disk(disk_radius_px))
                elif footprint_option == 1:
                    thresh = morphology.closing(thresh, morphology.ellipse(ellipse_width_px, ellipse_height_px))

            # Ensure final morphology cleanup uses pixel-based minimum area
            thresh = morphology.remove_small_objects(thresh, min_size=min_particle_area_px)
            thresh = morphology.remove_small_holes(thresh, area_threshold=min_particle_area_px)

            # Extracts data measurments from segmented image into "regions" variable
            if not Use_SAM:
                label_image = measure.label(thresh)

            impurity_measurements, coord_spacing = extract_pore_data(label_image, um_per_pix) 
            regions = measure.regionprops(label_image)
            if not regions:
                print(f"Warning: No particles detected in {file}. Skipping...")
                continue

            # Accesses data measurements from "regions" variable (for reference)
            '''
            This is where the function commonly crashes. The aspect ratio is what causes the 
            error but it is not even used so maybe it should be removed.
            '''
            centroids = [region.centroid for region in regions] # In pixels
            major = [region.axis_major_length for region in regions] # In pixels
            minor = [region.axis_minor_length for region in regions] # In pixels
            orientation = [region.orientation for region in regions] # In radians

     
            fig, ax = plt.subplots(figsize=(10, 10))

            # Display the image
            ax.imshow(thresh, cmap=plt.cm.gray, extent=[0, thresh.shape[1], thresh.shape[0], 0])
            # The extent parameter ensures the image coordinates match exactly with the plot coordinates
            # Note the reversed y-coordinates (shape[0], 0) to maintain proper image orientation

            # Plot the regions
            for props in regions:
                y0, x0 = props.centroid
                ori = props.orientation
                x1 = x0 + math.cos(ori) * 0.5 * props.axis_minor_length
                y1 = y0 - math.sin(ori) * 0.5 * props.axis_minor_length
                x2 = x0 - math.sin(ori) * 0.5 * props.axis_major_length
                y2 = y0 - math.cos(ori) * 0.5 * props.axis_major_length
                ax.plot((x0, x1), (y0, y1), 'y-', linewidth=2)
                ax.plot((x0, x2), (y0, y2), 'r-', linewidth=2)
                ax.plot(x0, y0, 'g.', markersize=5)

                angle_in_degrees = ori * (180/math.pi) + 90
                ellipses = patches.Ellipse(xy=(x0, y0), width=props.axis_major_length, height=props.axis_minor_length, 
                                        angle=(-angle_in_degrees), edgecolor='b', lw=2, facecolor='none')
                ax.add_patch(ellipses)

          # Set the axis limits explicitly to match the image dimensions
            ax.set_xlim(0, thresh.shape[1])
            ax.set_ylim(thresh.shape[0], 0)

            # REMOVE ALL AXIS VISUALS
            ax.set_axis_off()  # hides axis, ticks, labels, spines
            plt.margins(0, 0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())

            # Remove excess whitespace
            plt.tight_layout()

            base_filename = os.path.basename(filename).split('.')[0]
            path = os.path.join(SEG, f"segmented-{base_filename}.png")
            plt.savefig(path, bbox_inches='tight', pad_inches=0)
            plt.close()
                    
           

            # Writing to CSV
            os.makedirs(IMPURITY_DATA_FOLDER, exist_ok=True) # Does the folder exist

            # File paths
            csv_path_1 = os.path.join(IMPURITY_DATA_FOLDER, file.split('\\')[-1].split('.')[0] + '_impurity_measurements.csv')
            csv_path_2 = os.path.join(IMPURITY_DATA_FOLDER, file.split('\\')[-1].split('.')[0] + '_coord_spacing.csv')

            base_filename = os.path.basename(file)  # Gets just the filename from the path
            name_without_ext = os.path.splitext(base_filename)[0]  # Removes the extension
            csv_path_1 = os.path.join(IMPURITY_DATA_FOLDER, f"{name_without_ext}_impurity_measurements.csv")
            csv_path_2 = os.path.join(IMPURITY_DATA_FOLDER, f"{name_without_ext}_coord_spacing.csv")

            impurity_measurements.to_csv(csv_path_1, index=False)
            coord_spacing.to_csv(csv_path_2, index=False)

            return impurity_measurements



def extract_pore_data(outputs, um_per_pixel):
    '''
    Extracts impurity measurements and centroid spacing from SAM outputs.
    Returns two DataFrames: impurity measurements and centroid spacing.
    '''
   
    # --- Extract region properties ---
    props = measure.regionprops(outputs)
    
    sizes, aspects, orientations, centroids = [], [], [], []
    for p in props:
        if p.major_axis_length > 0 and p.minor_axis_length > 0:
            size = p.major_axis_length * um_per_pixel
            centroid = (p.centroid[1] * um_per_pixel, p.centroid[0] * um_per_pixel)
            #aspect = p.major_axis_length / p.minor_axis_length
            if p.minor_axis_length <= 0:
                continue   # skip degenerate regions
            aspect = p.major_axis_length / p.minor_axis_length

            orientation = abs(np.degrees(p.orientation))
            
            sizes.append(size)
            aspects.append(aspect)
            orientations.append(orientation)
            centroids.append(centroid)
    
    impurity_measurements_df = pd.DataFrame({
        "Size": sizes,
        "Aspect_Ratio": aspects,
        "Orientation": orientations
    })

    # --- Compute centroid spacing ---
    centroids = np.array(centroids)
    if len(centroids) > 1:
        dist_mat = distance_matrix(centroids, centroids)
        np.fill_diagonal(dist_mat, np.inf)
        nearest_idx = np.argmin(dist_mat, axis=1)
        nearest_dist = np.min(dist_mat, axis=1)

        # Build rows while avoiding reciprocal duplicates (i->j and j->i)
        rows = []
        seen_pairs = set()
        for i, (j, d) in enumerate(zip(nearest_idx, nearest_dist)):
            pair = tuple(sorted((i, j)))
            if pair in seen_pairs:
                # Reciprocal (or already-recorded) pair — skip to avoid duplicates
                continue
            seen_pairs.add(pair)
            rows.append({
                "X1": centroids[i, 0],
                "Y1": centroids[i, 1],
                "X2": centroids[j, 0],
                "Y2": centroids[j, 1],
                "Distance": d
            })

        coord_spacing_df = pd.DataFrame(rows)
    else:
        # If only one impurity, write empty file
        coord_spacing_df = pd.DataFrame(columns=["X1_um", "Y1_um", "X2_um", "Y2_um", "Distance_um"])

    return impurity_measurements_df, coord_spacing_df


if __name__ == "__main__":
    # Sorts SEM images folder
    folder = os.listdir(IMAGES)
    folder = sorted(folder)
    count = 1
    for filename in folder:
        filename = os.path.join(IMAGES,filename)
        segment_impurity_image(filename=filename, um_per_pix=0.1, intensity_threshold=127,
                               disk_radius=1, thresh_option=3, blur_option=1, min_particle_area=60, blockSize=11, C=2,
                               smooth_kernel_size=5, d=9, sigmaColor=75, sigmaSpace=75, footprint_option=0, ellipse_width=5, ellipse_height=3)
        count = count + 1