import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import pandas as pd
import argparse
import glob
from transformers import pipeline
from PIL import Image
from skimage.measure import regionprops, label
from scipy.spatial import distance_matrix

#'/Users/nicholaslopez/Desktop/School Work/Capstone/-wsum-fullstackapp-/src/META_AI_SAM/50 nm 63020B_TP08 Images'

"""
SAM (Segment Anything Model) Impurity Analysis Script

This script uses Meta's Segment Anything Model to detect impurities in microscopy images,
extract measurements, and calculate spacing between impurities.

Usage:
1. For a single file: python SAM_script.py --file path/to/image.png --scale 100
2. For a folder: python SAM_script.py --folder path/to/folder --scale 100
"""

def get_file_paths(path, is_folder=True):
    """
    Get file path(s) for processing based on input arguments.
    
    Args:
        path (str): Path to a file or folder
        is_folder (bool): Whether the path is a folder
    
    Returns:
        list: List of file paths to process
    """
    if not is_folder:
        return [path] if os.path.isfile(path) else []
    
    # Handle folder case - get all images
    valid_extensions = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
    files = []
    for ext in valid_extensions:
        files.extend(glob.glob(os.path.join(path, f"*{ext}")))
    return sorted(files)

def extract_measurements(masks, microns_per_pixel):
    """
    Extract size and position measurements from segmentation masks.
    
    This function calculates various properties for each detected impurity including:
    - Area in square microns
    - Major/minor axis lengths in microns
    - Aspect ratio
    - Orientation angle
    - Centroid coordinates
    
    It also calculates distances between impurity centroids.
    
    Args:
        masks (list): List of binary masks from SAM
        microns_per_pixel (float): Conversion factor from pixels to microns
        
    Returns:
        tuple: (impurity_measurements_df, spacing_df) - Pandas DataFrames with measurements
    """
    # Create combined mask
    combined_mask = np.zeros_like(masks[0], dtype=np.int32)
    for i, mask in enumerate(masks, start=1):
        combined_mask[mask] = i
    
    # Extract region properties
    props = regionprops(combined_mask)
    
    measurements = []
    centroids = []
    
    for p in props:
        if p.major_axis_length > 0 and p.minor_axis_length > 0:
            # Convert pixel measurements to microns
            area_um2 = p.area * (microns_per_pixel ** 2)
            
            # Store centroid position in microns
            centroid_x_um = p.centroid[1] * microns_per_pixel
            centroid_y_um = p.centroid[0] * microns_per_pixel
            
            measurements.append({
                "Size": area_um2,  # Area in square microns as the Size metric
                "Aspect_Ratio": p.major_axis_length / p.minor_axis_length,
                "Orientation": abs(np.degrees(p.orientation))
            })
            
            centroids.append((centroid_x_um, centroid_y_um))
    
    # Create DataFrame for impurity measurements
    impurity_df = pd.DataFrame(measurements)
    
    # Calculate centroid spacing (if at least 2 impurities)
    spacing_rows = []
    if len(centroids) > 1:
        centroids_array = np.array(centroids)
        dist_matrix = distance_matrix(centroids_array, centroids_array)
        np.fill_diagonal(dist_matrix, np.inf)
        
        # Find nearest neighbor for each centroid
        nearest_idx = np.argmin(dist_matrix, axis=1)
        nearest_dist = np.min(dist_matrix, axis=1)
        
        # Build rows while avoiding duplicates
        seen_pairs = set()
        for i, (j, d) in enumerate(zip(nearest_idx, nearest_dist)):
            pair = tuple(sorted((i, j)))
            if pair in seen_pairs:
                continue
                
            seen_pairs.add(pair)
            spacing_rows.append({
                "X1_um": centroids_array[i, 0],
                "Y1_um": centroids_array[i, 1],
                "X2_um": centroids_array[j, 0],
                "Y2_um": centroids_array[j, 1],
                "Distance_um": d
            })
    
    spacing_df = pd.DataFrame(spacing_rows)
    
    return impurity_df, spacing_df

def sam_segment_script(filename, physical_width_microns=50):
    """
    Run SAM segmentation on an image and extract impurity measurements.
    
    This function loads the Segment Anything Model, processes the image,
    extracts impurity measurements, and visualizes the results.
    
    Args:
        filename (str): Path to the image file
        physical_width_microns (float): Width of the image in microns
    
    Returns:
        tuple: (impurity_measurements_df, spacing_df) - DataFrames with measurements
    """
    start = time.perf_counter()

    # --- 1. Load Model ---
    print("Loading Segment Anything Model (SAM)...")
    generator = pipeline("mask-generation", model="facebook/sam-vit-huge", device="cpu")

    # --- 2. Load Image ---
    print(f"Processing image: {os.path.basename(filename)}")
    image = Image.open(filename).convert("RGB")
    
    # Calculate conversion factor (microns per pixel)
    image_width_pixels = image.width
    microns_per_pixel = physical_width_microns / image_width_pixels
    print(f"Image width: {image_width_pixels} pixels = {physical_width_microns} microns")
    print(f"Scale factor: {microns_per_pixel:.6f} microns/pixel")

    # --- 3. Run Segmentation ---
    print("Running segmentation...")
    outputs = generator(image, points_per_batch=64)
    masks = outputs["masks"]
    print(f"Found {len(masks)} potential impurities")

    # --- 4. Extract Measurements ---
    print("Extracting measurements...")
    impurity_df, spacing_df = extract_measurements(masks, microns_per_pixel)
    
    # --- 5. Visualize Results ---
    def show_mask(mask, ax, random_color=True):
        """Helper function to display a single mask."""
        if random_color:
            color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
        else:
            color = np.array([1.0, 1.0, 1.0, 0.6])
        h, w = mask.shape[-2:]
        mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
        ax.imshow(mask_image)

    end = time.perf_counter()
    total_time = end - start
    print(f"Total compute time: {total_time:.2f} seconds")

    # Create visualization
    plt.figure(figsize=(12, 8))
    
    # Original Image
    plt.subplot(1, 2, 1)
    plt.title("Original Image")
    plt.imshow(image)
    plt.axis('off')

    # Image with Masks
    plt.subplot(1, 2, 2)
    plt.title(f"Segmented Impurities ({len(masks)} found)")
    plt.imshow(image)
    ax = plt.gca()
    
    # Color each mask differently
    for mask in masks:
        show_mask(mask, ax=ax, random_color=True)
    
    plt.axis('off')
    
    # Save the visualization
    output_dir = os.path.join(os.path.expanduser("~/Desktop"), "Script3")
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(filename))[0]
    vis_path = os.path.join(output_dir, f"{base_name}_visualization.png")
    plt.savefig(vis_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return impurity_df, spacing_df

def process_files(files, physical_width_microns):
    """
    Process multiple files and save results to Desktop/Script3 folder.
    
    This function iterates through a list of files, runs the SAM segmentation
    on each one, and saves individual and combined results.
    
    Args:
        files (list): List of file paths to process
        physical_width_microns (float): Width of the images in microns
    """
    if not files:
        print("No files to process. Exiting.")
        return
    
    # Create output directory
    output_dir = os.path.join(os.path.expanduser("~/Desktop"), "Script3")
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each file
    all_impurity_data = []
    all_spacing_data = []
    
    for file_path in files:
        print(f"\nProcessing {os.path.basename(file_path)}...")
        try:
            impurity_df, spacing_df = sam_segment_script(file_path, physical_width_microns)
            
            # Add filename column
            filename = os.path.basename(file_path)
            impurity_df['Source_File'] = filename
            spacing_df['Source_File'] = filename
            
            # Append to combined results
            all_impurity_data.append(impurity_df)
            all_spacing_data.append(spacing_df)
            
            # Save individual results
            base_name = os.path.splitext(filename)[0]
            impurity_df.to_csv(os.path.join(output_dir, f"{base_name}_impurities.csv"), index=False)
            spacing_df.to_csv(os.path.join(output_dir, f"{base_name}_spacing.csv"), index=False)
            
            print(f"Found {len(impurity_df)} impurities in {filename}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Combine all results
    if all_impurity_data:
        combined_impurities = pd.concat(all_impurity_data, ignore_index=True)
        combined_impurities.to_csv(os.path.join(output_dir, "combined_impurities.csv"), index=False)
    
    if all_spacing_data:
        combined_spacing = pd.concat(all_spacing_data, ignore_index=True)
        combined_spacing.to_csv(os.path.join(output_dir, "combined_spacing.csv"), index=False)
    
    print(f"\nProcessing complete. Results saved to: {output_dir}")

def main():
    """
    Main function that parses command line arguments and initiates processing.

    """

    files = get_file_paths("/Users/nicholaslopez/Desktop/School Work/Capstone/-wsum-fullstackapp-/src/META_AI_SAM/50 nm 63020B_TP08 Images", True)
    process_files(files, 50)


if __name__ == "__main__":
    main()