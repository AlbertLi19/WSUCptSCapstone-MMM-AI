import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import matplotlib.colors as colors
import cv2
from dataclasses import dataclass
import numpy as np
from skimage.measure import EllipseModel, find_contours
import matplotlib.pyplot as plt


CRATER_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Crater_Data')  # crater data for all images

@dataclass
class CraterImg:
    img_path: str
    binarized_img: np.ndarray


def run_crater_analysis(image_dir, roi, start, end, binarization_thresh, fitting_thresh, contor_thresh, vx=43.6353, vy=43.6353, vz=43.6353) -> dict:
    # start and end of slices to process
    start_idx = start # 750
    end_idx = end #803

    # a voxel is the smallest unit of space in the image
    VX = vx    # Voxel size in X direction in microns
    VY = vy    # Voxel size in Y direction in microns
    VZ = vz    # Voxel size in Z direction in microns

    BINARIZATION_THRESHOLD = binarization_thresh # 0.4  # Set a threshold value for binarization
    FITTING_THRESHOLD = fitting_thresh #1          # Set a threshold value for analyzing the heatmap for crater diameter via best fit elipse
    CONTOR_THRESHOLD = contor_thresh # 0.3  
    
    processed_images = init_images(image_dir, start_idx, end_idx, BINARIZATION_THRESHOLD)

    ROI = roi  # Get the ROI from the user
    if ROI:
        width, height = ROI[2], ROI[3]
    else:
        width, height = processed_images[0].binarized_img.shape[1], processed_images[0].binarized_img.shape[0]

    heatmap_array = np.zeros((height, width))  # Creates a 2D array of zeros with dimensions height×width
    
    crater_volume = calculate_volume(processed_images, heatmap_array, ROI, VX, VY, VZ)
    
    major_diameter_mm, minor_diameter_mm, avg_diameter_mm = calculate_diamater(heatmap_array, VX, VY, fitting_threshold=FITTING_THRESHOLD, contor_threshold=CONTOR_THRESHOLD)\
    
    max_depth_mm = calculate_depth(heatmap_array, VZ)

    crater_data = { 
        "volume": crater_volume,
        "diameter": {
            "major": major_diameter_mm,
            "minor": minor_diameter_mm,
            "average": avg_diameter_mm
        },
        "depth": max_depth_mm
    }

    return crater_data

def calculate_depth(heatmap_array: np.ndarray, VZ: float) -> None:
    max_depth_voxels = np.max(heatmap_array)  # Find the maximum depth in voxels
    max_depth_microns = max_depth_voxels * VZ  # Convert to microns
    max_depth_mm = max_depth_microns * 1e-3  # Convert to mm
    return max_depth_mm


def calculate_volume(processed_images, heatmap_array, roi, vx, vy, vz):
    
    count = 0
    crater_volume = 0  

    # get volume of each image
    for image in processed_images:
        print(f"Processing image {count + 1}/{len(processed_images)}: {image.img_path}")

        if roi:
            # If ROI was selected, crop the image
            image.binarized_img = image.binarized_img[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]

        # Create a boolean mask of black pixels (where value is 0)
        black_pixel_mask = (image.binarized_img == 0)
        
        # Update the heatmap for these locations
        heatmap_array[black_pixel_mask] += 1
        
        # Calculate volume contribution from this slice
        # Volume = number of black pixels * voxel volume
        black_pixel_count = np.sum(black_pixel_mask)
        slice_volume = black_pixel_count * (vx * vy * vz) * (1e-9)  # Convert to mm^3
        crater_volume += slice_volume
        
        count += 1

    ### Crater vol. Need to return this to user ###
    print(f"Crater Volume: {crater_volume:.6f} mm³")

    fname = "crater_heatmap.png"
    path = os.path.join(CRATER_DATA, fname)
    save_heatmap(heatmap_array, path, vz)
    return crater_volume # dont need to return heatmap array because it is modified in place


def calculate_diamater(heatmap:np.ndarray, vx: float, vy: float, fitting_threshold: float = 0.4, contor_threshold: float = 0.3) -> None:
     # Apply threshold to create a mask where crater areas are True
    if np.max(heatmap) <= 0:
        return None
    heatmap_normalized = heatmap / np.max(heatmap) 
    FITTING_THRESHOLD = fitting_threshold
    heatmap_mask = heatmap_normalized > FITTING_THRESHOLD 
    
    # Create binary image
    binary_display = np.ones_like(heatmap_mask, dtype=np.uint8)
    binary_display[heatmap_mask] = 0  # Set crater areas to black
    

  
    # Assuming you have a binary mask as a numpy array called 'mask'
    # where 1 or True represents your blob and 0 or False represents the background

    # Step 1: Extract the boundary points of the blob
    CONTOR_THRESHOLD = contor_threshold  # Adjust this threshold as needed
    contours = find_contours(heatmap_mask, CONTOR_THRESHOLD)  # contor threshold controls the sensitivity of contour detection

    # Use the largest contour if there are multiple
    contour = contours[0] if len(contours) == 1 else max(contours, key=len)

    # Step 2: Fit an ellipse to these boundary points

    if success:
        # Get the ellipse parameters (center_x, center_y, semi-major axis, semi-minor axis, angle)
        params = ellipse.params
        print(f"Ellipse parameters: {params}")
        
        # Generate points of the fitted ellipse for visualization
        t = np.linspace(0, 2 * np.pi, 100)
        ellipse_points = ellipse.predict_xy(t)
        
        center_x, center_y, semi_major, semi_minor, angle = ellipse.params
        

        major_diameter_microns = 2 * semi_major * vx
        minor_diameter_microns = 2 * semi_minor * vy
        
        # Convert to millimeters
        major_diameter_mm = major_diameter_microns * 1e-3
        minor_diameter_mm = minor_diameter_microns * 1e-3
        
        # Average diameter
        avg_diameter_mm = (major_diameter_mm + minor_diameter_mm) / 2
        
        print(f"Major Diameter: {major_diameter_mm:.6f} mm")
        print(f"Minor Diameter: {minor_diameter_mm:.6f} mm")    
        print(f"Average Diameter: {avg_diameter_mm:.6f} mm")

        # Save the visualization to a file
        plt.figure(figsize=(10, 8))
        plt.imshow(heatmap_mask, cmap='gray')
        plt.plot(contour[:, 1], contour[:, 0], 'r.', markersize=2, label='Contour')
        plt.plot(ellipse_points[:, 1], ellipse_points[:, 0], 'b-', linewidth=2, label='Fitted Ellipse')
        plt.legend()
        plt.axis('equal')
        plt.title('Ellipse fit to binary mask')
        
        # Save the figure to a file
        fname = "crater_ellipse.png"
        path = os.path.join(CRATER_DATA, fname)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Ellipse fit visualization saved to {path}")
        return major_diameter_mm, minor_diameter_mm, avg_diameter_mm
    else:
        print("Failed to fit ellipse to the contour points.")  



def save_heatmap(heatmap_array: np.ndarray, filename: str, vz: float) -> None:
    """
    Save a heatmap visualization to a file without displaying it
    
    Args:
        heatmap_array: 2D array containing the heatmap data
        filename: Path where the heatmap image will be saved
    """
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(10, 8))
    heatmap_mm = heatmap_array * vz  # Convert voxel depth to mm
    # Create the heatmap visualization
    im = ax.imshow(heatmap_mm, cmap='turbo', interpolation='nearest')
    ax.set_title('Crater Depth Heatmap (mm)')
    ax.set_xlabel('X Position (mm)')
    ax.set_ylabel('Y Position (mm)')
    
    # Add colorbar on the left side
    cbar_ax = fig.add_axes([0.05, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label('Depth (voxels)')
    
    plt.tight_layout()
    
    # Save the figure to the specified filename
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)  # Close the figure to free memory
    
    print(f"Heatmap saved to {filename}")

def init_images(image_dir: str, start_idx: int, end_idx: int, threshhold: float) -> list[CraterImg]:
    '''
    ## Init Images
    Initialize the images by loading them and saving as binarized images (ndarrays). 
    **image_dir**: Directory containing the images to be processed
    '''
    processed_images = [] # a list of craterImg dataclass objects
    for i in range(start_idx, end_idx + 1):
        str_i = f"{i:05d}"
        im_name = f"slice{str_i}.tif"
        img_path = os.path.join(image_dir, im_name)


        '''
        Instead of reading the image as a 3-channel color image (RGB), this loads it as a single-channel grayscale image where 
        each pixel has a single intensity value (typically from 0-255).
        '''
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Read as grayscale
        if img is None:
            print(f"Warning: {im_name} not found.")
            continue

        '''
        Converts the grayscale image (which typically has values from 0-255) to 32-bit floating point
        Divides all pixel values by 255.0 to normalize them to the range [0,1]
        This normalization makes subsequent operations more consistent and simplifies threshold values
        '''
        normalized_img = img.astype(np.float32) / 255.0  # Normalize to range [0,1]


        '''
        Applies a global threshold of 0.4 to the normalized image
        Pixels with values > 0.4 become 1.0 (white); pixels ≤ 0.4 become 0 (black)
        The first return value (discarded with _) is the threshold used
        img_bw is the resulting binary image with values of either 0 or 1.0
        '''
        _, binary_img = cv2.threshold(normalized_img, threshhold, 1.0, cv2.THRESH_BINARY)

        newImg = CraterImg(
            img_path=img_path,
            binarized_img=binary_img
        )       
        # save path of original image with binarized image in case we need it later
        processed_images.append(newImg)
    return processed_images



def get_roi(image):
     # Find the rectangular region of interest via cursor selection
     # call this in main thread and pass ROI to the crater analysis function
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(image, cmap='gray')
    ax.set_title('Select region for displacement calculation.')

    # Global variables to store ROI coordinates and the selector
    global roi, selector
    roi = None
    
    def line_select_callback(eclick, erelease):
        global roi
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        roi = [x1, y1, x2-x1, y2-y1]  # [x, y, width, height]
        plt.close()

    # Store the selector in a variable that won't be garbage collected
    selector = RectangleSelector(ax, line_select_callback,
                        useblit=False, button=[1], 
                        minspanx=5, minspany=5, 
                        spancoords='pixels')
    plt.show()
    
    return roi



if __name__ == "__main__":
    '''
    Crater analysis testing
    Desired output params:
    - Crater volume in mm^3
    - Crater depth heatmap
    - max crater diameter 
    - max crater depth in 
    '''

    
   
    
    DEBUG = False  
    IMG_PATH = r"C:\Users\nelso\Desktop\Computer Science\CS School Projects\Capstone\SlicesZ"

    ### INIT PARAMS ###
    # Initialize the algorithm with the following parameters:
 
    # start and end of slices to process
    start_idx = 750
    end_idx = 803

    # a voxel is the smallest unit of space in the image
    VX = 43.6353    # Voxel size in X direction in microns
    VY = 43.6353    # Voxel size in Y direction in microns
    VZ = 43.6353    # Voxel size in Z direction in microns

    BINARIZATION_THRESHOLD = 0.4  # Set a threshold value for binarization
    FITTING_THRESHOLD = 1          # Set a threshold value for analyzing the heatmap for crater diameter via best fit elipse


    # images
    processed_images = init_images(IMG_PATH, start_idx, end_idx, BINARIZATION_THRESHOLD)
    print(f"Debug processed {len(processed_images)} images")
    ### ROI SELECTION ###
    roi = None
    roi = get_roi()  # Get the ROI from the user


    # if there was a ROI, create a heatmap array of zeros with the dimensions of the ROI
    # if there was no ROI, create a heatmap array of zeros with the dimensions of the first image
    if roi:
        width, height = roi[2], roi[3]
        
    else:
        width, height = processed_images[0].binarized_img.shape[1], processed_images[0].binarized_img.shape[0]

    
    heatmap = np.zeros((height, width))  # Creates a 2D array of zeros with dimensions height×width
    
    count = 0
    crater_volume = 0  

    for image in processed_images:
        print(f"Processing image {count + 1}/{len(processed_images)}: {image.img_path}")

        if roi:
            # If ROI was selected, crop the image
            image.binarized_img = image.binarized_img[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]

        # Create a boolean mask of black pixels (where value is 0)
        black_pixel_mask = (image.binarized_img == 0)
        
        # Update the heatmap for these locations
        heatmap[black_pixel_mask] += 1
        
        # Calculate volume contribution from this slice
        # Volume = number of black pixels * voxel volume
        black_pixel_count = np.sum(black_pixel_mask)
        slice_volume = black_pixel_count * (VX * VY * VZ) * (1e-9)  # Convert to mm³
        crater_volume += slice_volume
        
        count += 1

    ### Crater vol. Need to return this to user ###
    print(f"Crater Volume: {crater_volume:.6f} mm³")



    SHOW_HEATMAP = True
    if SHOW_HEATMAP:
        ### Create different visualizations of the heatmap ###
        ## Last one is my favorite - Nelson

        fig, axes = plt.subplots(2, 2, figsize=(16, 14))
        fig.suptitle('Crater Depth Heatmap - Different Visualization Methods', fontsize=16)
        
        # 1. Standard normalization
        normalized_heatmap = heatmap / heatmap.max() if heatmap.max() > 0 else heatmap
        im1 = axes[0, 0].imshow(normalized_heatmap, cmap='viridis', interpolation='nearest')
        axes[0, 0].set_title('Standard Normalization')
        axes[0, 0].set_xlabel('X Position (pixels)')
        axes[0, 0].set_ylabel('Y Position (pixels)')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 2. Logarithmic scaling - helps with data that has wide value ranges
        log_heatmap = np.log1p(heatmap)  # log(1+x) to handle zeros
        normalized_log = log_heatmap / log_heatmap.max() if log_heatmap.max() > 0 else log_heatmap
        im2 = axes[0, 1].imshow(normalized_log, cmap='viridis', interpolation='nearest')
        axes[0, 1].set_title('Logarithmic Scaling')
        axes[0, 1].set_xlabel('X Position (pixels)')
        axes[0, 1].set_ylabel('Y Position (pixels)')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # 3. Power-law transformation (gamma correction)
        gamma = 0.4  # Values < 1 enhance low-intensity details
        power_heatmap = np.power(normalized_heatmap, gamma)
        im3 = axes[1, 0].imshow(power_heatmap, cmap='plasma', interpolation='nearest')
        axes[1, 0].set_title(f'Power-law Transformation (γ={gamma})')
        axes[1, 0].set_xlabel('X Position (pixels)')
        axes[1, 0].set_ylabel('Y Position (pixels)')
        plt.colorbar(im3, ax=axes[1, 0])
        
        # 4. Percentile clipping - focus on a specific value range
        non_zero = heatmap[heatmap > 0]
        if len(non_zero) > 0:  # Check if there are non-zero values
            p_low, p_high = np.percentile(non_zero, [5, 95])
            clipped_heatmap = np.clip(heatmap, p_low, p_high)
            normalized_clipped = (clipped_heatmap - p_low) / (p_high - p_low) if p_high > p_low else clipped_heatmap
        else:
            normalized_clipped = normalized_heatmap
        
        im4 = axes[1, 1].imshow(normalized_clipped, cmap='turbo', interpolation='nearest')
        axes[1, 1].set_title('Percentile Clipping (5-95%)')
        axes[1, 1].set_xlabel('X Position (pixels)')
        axes[1, 1].set_ylabel('Y Position (pixels)')
        plt.colorbar(im4, ax=axes[1, 1])
        
        plt.tight_layout()
        plt.show()


    #### Diamater calculations ####
    '''
    IDEA: the heatmap is essentially recording all areas from all images in the dataset where the crater is present. We simply convert the 
    heatmap to a binary image, so values are either part of the image, or not. Then we find the elipse of best fit and return that diamater.
    '''
    # Apply threshold to create a mask where crater areas are True
    heatmap_normalized = heatmap / np.max(heatmap) if np.max(heatmap) > 0 else heatmap
    FITTING_THRESHOLD = .7
    heatmap_mask = heatmap_normalized > FITTING_THRESHOLD ## ignore extra noise. Low heatmap values are probably noise. Let user adjust. Also, look into normalizing the heatmap before this for easier use of threshold.
    
    # Create binary image
    binary_display = np.ones_like(heatmap_mask, dtype=np.uint8)
    binary_display[heatmap_mask] = 0  # Set crater areas to black
    
    SHOWMASK = False
    if SHOWMASK:
        # Display the binary mask (debugging)
        plt.figure(figsize=(12, 10), dpi=100)
        plt.imshow(binary_display, cmap='gray', interpolation='nearest')
        plt.title('Crater Area (Black) Mask')
        plt.colorbar(label='Pixel Value (0=Black, 1=White)')
        plt.tight_layout()
        plt.show()


    import numpy as np
    from skimage.measure import EllipseModel, find_contours
    import matplotlib.pyplot as plt

    # Assuming you have a binary mask as a numpy array called 'mask'
    # where 1 or True represents your blob and 0 or False represents the background

    # Step 1: Extract the boundary points of the blob
    CONTOR_THRESHOLD = 0.4  # Adjust this threshold as needed
    contours = find_contours(heatmap_mask, CONTOR_THRESHOLD)  # contor threshold controls the sensitivity of contour detection

    # Use the largest contour if there are multiple
    contour = contours[0] if len(contours) == 1 else max(contours, key=len)

    # Step 2: Fit an ellipse to these boundary points
    ellipse = EllipseModel()
    success = ellipse.estimate(contour)

    if success:
        # Get the ellipse parameters (center_x, center_y, semi-major axis, semi-minor axis, angle)
        params = ellipse.params
        print(f"Ellipse parameters: {params}")
        
        # Generate points of the fitted ellipse for visualization
        t = np.linspace(0, 2 * np.pi, 100)
        ellipse_points = ellipse.predict_xy(t)
        
        center_x, center_y, semi_major, semi_minor, angle = ellipse.params
        

        major_diameter_microns = 2 * semi_major * VX
        minor_diameter_microns = 2 * semi_minor * VY
        
        # Convert to millimeters
        major_diameter_mm = major_diameter_microns * 1e-3
        minor_diameter_mm = minor_diameter_microns * 1e-3
        
        # Average diameter
        avg_diameter_mm = (major_diameter_mm + minor_diameter_mm) / 2
        
        print(f"Major Diameter: {major_diameter_mm:.6f} mm")
        print(f"Minor Diameter: {minor_diameter_mm:.6f} mm")    
        print(f"Average Diameter: {avg_diameter_mm:.6f} mm")

        # Visualize the result
        plt.figure(figsize=(10, 8))
        plt.imshow(heatmap_mask, cmap='gray')
        plt.plot(contour[:, 1], contour[:, 0], 'r.', markersize=2, label='Contour')
        plt.plot(ellipse_points[:, 1], ellipse_points[:, 0], 'b-', linewidth=2, label='Fitted Ellipse')
        plt.legend()
        plt.axis('equal')
        plt.title('Ellipse fit to binary mask')
        plt.show()
    else:
        print("Failed to fit ellipse to the contour points.")    


    ### Depth Calculations ###

    max_depth_voxels = np.max(heatmap)  # Find the maximum depth in voxels
    max_depth_microns = max_depth_voxels * VZ  # Convert to microns
    max_depth_mm = max_depth_microns * 1e-3  # Convert to mm
    print(f"Max Depth: {max_depth_mm:.6f} mm")