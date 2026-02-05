'''
This file contains a script to perform image segmentation using the Segment Anything Model (SAM) from Meta AI.
'''
from transformers import pipeline
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import os
import cv2  
import torch
from skimage.measure import regionprops, label
from scipy.spatial import distance_matrix
import pandas as pd
import numpy as np
import math

SAM_DATA = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','SAM_Data')  # SAM model data
SEGMENTED_FOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Impurity_Segmented_Images')


def show_mask(mask, ax, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)

def sam_automatic_hardware_optimization(image_path, show_results=True, save_masks=False):
    """
    Run SAM with automatically optimized parameters based on available hardware.
    
    Args:
        image_path (str): Path to input image
        show_results (bool): Whether to display results with matplotlib
        save_masks (bool): Whether to save individual masks to files
        output_dir (str): Directory to save masks if save_masks=True
    
    Returns:
        dict: SAM outputs with masks and metadata
    """
    
    # Detect available hardware
    has_cuda = torch.cuda.is_available()
    device = 0 if has_cuda else -1
    device_name = "GPU (CUDA)" if has_cuda else "CPU"
    
    print(f"Hardware detected: {device_name}")
    
    # Get GPU memory if available
    gpu_memory_gb = 0
    if has_cuda:
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"GPU Memory: {gpu_memory_gb:.1f} GB")
    
    # Set CPU threads for better performance
    if not has_cuda:
        num_threads = min(8, torch.get_num_threads())
        torch.set_num_threads(num_threads)
        print(f"🧵 Using {num_threads} CPU threads")
    
    # Configure parameters based on hardware
    if has_cuda:
        # GPU-optimized parameters
        if gpu_memory_gb >= 8:
            # High-end GPU
            config = {
                "points_per_side": 64,
                "points_per_batch": 512,
                "pred_iou_thresh": 0.88,
                "stability_score_thresh": 0.95,
                "crop_n_layers": 1,
                "crop_n_points_downscale_factor": 2,
                "min_mask_region_area": 50
            }
            print("Using high-performance GPU settings")
        elif gpu_memory_gb >= 4:
            # Mid-range GPU
            config = {
                "points_per_side": 32,
                "points_per_batch": 256,
                "pred_iou_thresh": 0.88,
                "stability_score_thresh": 0.95,
                "crop_n_layers": 1,
                "crop_n_points_downscale_factor": 2,
                "min_mask_region_area": 100
            }
            print("Using standard GPU settings")
        else:
            # Low VRAM GPU
            config = {
                "points_per_side": 16,
                "points_per_batch": 64,
                "pred_iou_thresh": 0.86,
                "stability_score_thresh": 0.92,
                "crop_n_layers": 0,
                "min_mask_region_area": 150
            }
            print("Using low-memory GPU settings")
    else:
        # CPU-optimized parameters
        config = {
            "points_per_side": 16,
            "points_per_batch": 32,
            "pred_iou_thresh": 0.86,
            "stability_score_thresh": 0.92,
            "crop_n_layers": 0,
            "min_mask_region_area": 100
        }
        print("Using CPU-optimized settings (this will be slower)")
    
    # Resize image for CPU or low-memory scenarios
    original_path = image_path
  
    try:
        # Initialize SAM pipeline
        print("Loading SAM model...")
        generator = pipeline(
            "mask-generation",
            model="facebook/sam-vit-base",
            device=device,
            torch_dtype=torch.float32
        )
        
        # Run SAM with optimized parameters
        print("Generating masks...")
        outputs = generator(image_path, **config)
        
        num_masks = len(outputs["masks"])
        print(f"Generated {num_masks} masks successfully!")
        
        # Display results
        if show_results:
            _display_results(image_path, outputs)
        
        # Save masks if requested
        if save_masks:
            _save_masks(image_path, outputs, output_dir=SAM_DATA)
            print(f"Masks saved to {SAM_DATA}/")

        return outputs
        
    except Exception as e:
        print(f"Error running SAM: {str(e)}")
        
        # Fallback to more conservative settings
        if has_cuda:
            print("Trying with reduced settings...")
            config.update({
                "points_per_side": 8,
                "points_per_batch": 32,
                "crop_n_layers": 0
            })
            try:
                outputs = generator(image_path, **config)
                print(f"Fallback successful! Generated {len(outputs['masks'])} masks")
                if show_results:
                    _display_results(image_path, outputs)
                return outputs
            except Exception as e2:
                print(f"Fallback also failed: {str(e2)}")
        
        raise e

def _resize_image(image_path, max_size=800):
    """Resize image if it's too large for efficient processing"""
    img = cv2.imread(image_path)
    if img is None:
        return image_path
        
    h, w = img.shape[:2]
    
    if max(h, w) > max_size:
        if h > w:
            new_h, new_w = max_size, int(w * max_size / h)
        else:
            new_h, new_w = int(h * max_size / w), max_size
        
        img_resized = cv2.resize(img, (new_w, new_h))
        
        # Create temp file
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        temp_path = f"temp_{base_name}_resized.jpg"
        cv2.imwrite(temp_path, img_resized)
        return temp_path
    
    return image_path

def _display_results(image_path, outputs):
    """Display SAM results with matplotlib"""
    def show_mask(mask, ax, random_color=True):
        if random_color:
            color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
        else:
            color = np.array([30/255, 144/255, 255/255, 0.6])
        h, w = mask.shape[-2:]
        mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
        ax.imshow(mask_image)
    
    raw_image = Image.open(image_path).convert("RGB")
    plt.figure(figsize=(12, 8))
    plt.imshow(np.array(raw_image))
    ax = plt.gca()
    
    for mask in outputs["masks"]:
        show_mask(mask, ax=ax, random_color=True)
    
    plt.axis("off")
    plt.title(f"SAM Results: {len(outputs['masks'])} masks detected")
    plt.tight_layout()
    plt.show()

def save_sam_visualization(image_path, outputs):
    """We need to save the visualization to show the user"""
   
    # Read the original image
    orig_image = cv2.imread(image_path)
    if orig_image is None:
        print(f"Error reading image: {image_path}")
        return None
    
    # Convert to RGB for visualization
    orig_rgb = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
    
    
    # Create figure for visualization
    plt.figure(figsize=(10, 10))
    plt.imshow(orig_rgb)
    
    ax = plt.gca()
    for mask in outputs["masks"]:
        # Resize mask if needed to match image dimensions
        if mask.shape != orig_rgb.shape[:2]:
            mask_resized = cv2.resize(mask.astype(np.uint8), 
                                    (orig_rgb.shape[1], orig_rgb.shape[0]))
            mask = mask_resized.astype(bool)
        
        color = np.concatenate([np.random.random(3), np.array([0.35])], axis=0)
        
        h, w = mask.shape
        mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
        ax.imshow(mask_image)
    
    plt.axis('off')
    
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    out_name = f"segmented-{base_name}.png"
    out_path = os.path.join(SEGMENTED_FOLDER, out_name)
    
    # Save the visualization
    os.makedirs(SEGMENTED_FOLDER, exist_ok=True)
    plt.savefig(out_path, bbox_inches='tight', pad_inches=0)
    plt.close()
    
    print(f"Saved segmentation visualization to {out_path}")
    return out_path

def _save_masks(image_path, outputs, output_dir):
    """Save individual masks to files"""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    for i, mask in enumerate(outputs["masks"]):
        mask_uint8 = (mask * 255).astype(np.uint8)
        mask_path = os.path.join(output_dir, f"{base_name}_mask_{i:03d}.png")
        cv2.imwrite(mask_path, mask_uint8)


def image_preprocessing(tif_path: str, crop_area=None):
    """
    Convert tif to png and apply crop, then save in temporary directory.
    Returns: path to the processed image.
    """
    img_cv = cv2.imread(tif_path, cv2.IMREAD_UNCHANGED)
    if img_cv is None:
        print("Error: Unable to read image with OpenCV.")
        return

    # If image is color, convert to grayscale
    if len(img_cv.shape) == 3:
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    else:
        img_gray = img_cv

    # If image is 16-bit, normalize to 8-bit
    if img_gray.dtype == np.uint16:
        img_gray = cv2.normalize(img_gray, None, 0, 255, cv2.NORM_MINMAX)
        img_gray = img_gray.astype(np.uint8)
    
    if crop_area is not None:
        # Apply cropping using the saved rectangle
        img_gray = img_gray[crop_area.y():crop_area.y() + crop_area.height(),
                crop_area.x():crop_area.x() + crop_area.width()]
        
    base_name = os.path.splitext(os.path.basename(tif_path))[0]
    out_name = f"{base_name}_preprocessed.png"
    out_path = os.path.join(SAM_DATA, out_name)
    cv2.imwrite(out_path, img_gray)
    print(f"Saved preprocessed image to {out_path}")
    return out_path


def sam_segmentation(filename: str, crop_area=None):
    """
    Run SAM segmentation on the given image file.

    Args:
        filename (str): Path to the input image file.
        saved_crop_rect (QRect, optional): Crop rectangle if any.

    Returns:
        dict: SAM outputs with masks and metadata.
    """
    print("Starting SAM segmentation...")
    preprocessed_path = image_preprocessing(filename, crop_area)
    outputs = sam_automatic_hardware_optimization(
        image_path=preprocessed_path,
        show_results=False,
        save_masks=True,
        #output_dir=SAM_DATA
    )
    mask_path = save_sam_visualization(preprocessed_path, outputs)

    return outputs, mask_path


def analyze_sam_regions(un_per_pixel: float, outputs: dict):
    """
    Analyze SAM masks to extract region properties.

    Args:
        un_per_pixel (float): Microns per pixel scaling factor.
        outputs (dict): SAM outputs containing masks.

    Returns:
        list: List of dictionaries with region properties.
    """
    combined_mask = np.zeros_like(outputs["masks"][0], dtype=np.int32)

    # Add each mask from SAM output to the combined mask with a unique label
    for i, mask in enumerate(outputs["masks"]):
        combined_mask[mask == 1] = i + 1  # Use i+1 to avoid 0 (background)
    
    # Label the combined mask and get region properties
    labeled_mask = label(combined_mask)
    regions = regionprops(labeled_mask)

    if not regions:
        print("No regions detected in SAM output")
        empty_impurity = pd.DataFrame(columns=["Size", "Aspect_Ratio", "Orientation"])
        empty_spacing = pd.DataFrame(columns=["X1", "Y1", "X2", "Y2", "Distance"])
        return empty_impurity, empty_spacing
    
    # Extract impurity measurements (similar to impurity_segmentation.py)
    sizes = []
    aspect_ratios = []
    orientations = []
    centroids = []
    
    for region in regions:
        size = region.major_axis_length * un_per_pixel
        sizes.append(size)
        
        if region.minor_axis_length > 0:
            aspect_ratio = region.major_axis_length / region.minor_axis_length
        else:
            aspect_ratio = 1.0
        aspect_ratios.append(aspect_ratio)
        
        orientation = abs(region.orientation * (180 / math.pi))
        orientations.append(orientation)
        
        centroid_nm = (region.centroid[1] * un_per_pixel, region.centroid[0] * un_per_pixel)
        centroids.append(centroid_nm)
    
    impurity_measurements = pd.DataFrame({
        "Size": sizes,
        "Aspect_Ratio": aspect_ratios,
        "Orientation": orientations
    })
    
    coord_spacing_data = []
    
    if len(centroids) > 1:
        for i, (x1, y1) in enumerate(centroids):
            min_distance = float('inf')
            nearest_centroid = None
            
            for j, (x2, y2) in enumerate(centroids):
                if i != j:
                    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_centroid = (x2, y2)
            
            if nearest_centroid:
                coord_spacing_data.append([x1, y1, nearest_centroid[0], nearest_centroid[1], min_distance])
    
    coord_spacing = pd.DataFrame(coord_spacing_data, columns=["X1", "Y1", "X2", "Y2", "Distance"])
    print("Finished in the sam_regions portion")
    return impurity_measurements, coord_spacing

    

    