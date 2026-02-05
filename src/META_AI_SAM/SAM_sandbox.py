from networkx import edges
from scipy import stats
from transformers import pipeline
import matplotlib.pyplot as plt
from PIL import Image, ImageTk  # Add ImageTk to the import
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os
import shutil
import cv2  # Add this import
import torch
import pandas as pd
from skimage.measure import regionprops, label
from skimage.color import label2rgb
from scipy.spatial import distance_matrix

def file_dialog(folder=False):
    """
    Opens a file dialog window to select an image file or a folder.
    If folder is False (default) returns a single file path (string) or '' if cancelled.
    If folder is True returns a list of image file paths from the selected folder (empty list if cancelled or no images).
    """
    root = tk.Tk()
    root.withdraw()
    if not folder:
        file_path = filedialog.askopenfilename()
        root.destroy()
        return file_path

    folder_path = filedialog.askdirectory()
    root.destroy()
    if not folder_path:
        return []

    # file extensions to include
    exts = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
    files = [
        os.path.join(folder_path, f)
        for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(exts) and os.path.isfile(os.path.join(folder_path, f))
    ]
    return files

def image_preprocessing(image_path):
    '''
    Preprocesses the .tif image by converting it into a png format so it is useable by SAM.
    Also provides a GUI to crop the image if desired.

    Returns the path to the preprocessed png image (saved in the ./temp folder).
    '''
    img_cv = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
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

    # --- Cropping GUI ---
    clone = img_gray.copy()
    cropping = [False]
    refPt = []

    def click_and_crop(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            refPt.clear()
            refPt.append((x, y))
            cropping[0] = True
        elif event == cv2.EVENT_LBUTTONUP:
            refPt.append((x, y))
            cropping[0] = False

    cv2.namedWindow("Crop Image", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Crop Image", click_and_crop)
    temp_img = clone.copy()
    while True:
        display = temp_img.copy()
        if len(refPt) == 1:
            cv2.rectangle(display, refPt[0], (cv2.getWindowImageRect("Crop Image")[2], cv2.getWindowImageRect("Crop Image")[3]), (0,255,0), 2)
        elif len(refPt) == 2:
            cv2.rectangle(display, refPt[0], refPt[1], (0,255,0), 2)
        cv2.imshow("Crop Image", display)
        key = cv2.waitKey(1) & 0xFF
        if key == 13 or key == 32:  # Enter or Space to confirm crop
            break
        elif key == 27:  # ESC to skip cropping
            refPt = []
            break
    cv2.destroyWindow("Crop Image")

    if len(refPt) == 2:
        x0, y0 = refPt[0]
        x1, y1 = refPt[1]
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        img_gray = img_gray[y0:y1, x0:x1]

    os.makedirs("temp", exist_ok=True)
    filename = os.path.basename(image_path)
    name, _ = os.path.splitext(filename)
    png_path = os.path.join("temp", f"{name}.png")
    cv2.imwrite(png_path, img_gray)

    return png_path

def sam_automatic_hardware_optimization(image_path, show_results=True, output_dir="temp"):
    '''
    Runs the SAM model with parameters optimized for the detected hardware (CPU/GPU and memory).
    Saves results in the specified output directory.
    '''
    
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
    if not has_cuda or gpu_memory_gb < 4:
        image_path = _resize_image(image_path, max_size=800 if not has_cuda else 1200)
        if image_path != original_path:
            print(f"Resized image for better performance")
    
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
        print(f"✅ Generated {num_masks} masks successfully!")
        
        # Display results
        if show_results:
            _display_results(image_path, outputs)
        
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
    """Display SAM results with matplotlib and save segmented image to ./temp/<filename>_segmented.png"""
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

    # Ensure temp directory exists and save the figure
    os.makedirs("temp", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join("temp", f"{base_name}_segmented.png")
    plt.savefig(out_path, bbox_inches="tight", pad_inches=0.1, dpi=200)
    plt.show()
    plt.close()


def extract_pore_data(outputs, um_per_pixel):
    '''
    Extracts impurity measurements and centroid spacing from SAM outputs.
    Returns two DataFrames: impurity measurements and centroid spacing.
    '''
    combined_mask = np.zeros_like(outputs['masks'][0], dtype=np.int32)
    combined_bool = np.zeros_like(outputs['masks'][0], dtype=bool)
    for i, m in enumerate(outputs["masks"], start=1):
        seg = m.astype(bool)
        combined_mask[seg] = i
        combined_bool |= seg

    # Display the combined mask as a boolean image
    plt.figure(figsize=(6, 6))
    plt.imshow(combined_bool, cmap='gray')
    plt.title("Combined mask (boolean)")    
    plt.axis('off')
    plt.show()
    
    # --- Extract region properties ---
    props = regionprops(combined_mask)
    
    sizes, aspects, orientations, centroids = [], [], [], []
    for p in props:
        if p.major_axis_length > 0 and p.minor_axis_length > 0:
            size = p.major_axis_length * um_per_pixel
            centroid = (p.centroid[1] * um_per_pixel, p.centroid[0] * um_per_pixel)
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
        coord_spacing_df = pd.DataFrame(columns=["X1", "Y1", "X2", "Y2", "Distance"])

    return impurity_measurements_df, coord_spacing_df

def main():
    # get image file path (or optionally folder of images)
    image_path = file_dialog()
    # preprocessing
    preprocessed_path = image_preprocessing(image_path)  
    # get segmentation results
    results = sam_automatic_hardware_optimization(
        image_path=preprocessed_path,
        show_results=True,
        output_dir="temp"
    )

    '''
    Results object type: <class 'dict'>
    Top-level keys: ['masks', 'scores']
    - masks: <class 'list'>, length=134
    element shape: (797, 800), dtype=bool
    - scores: <class 'torch.Tensor'>, shape=torch.Size([134]), dtype=torch.float32
    '''
    image_width_px = results['masks'][0].shape[1]

    '''
    IMPORTANT: Adjust the view_field_um variable below to match the actual width of your image in micrometers (um).
    '''

    view_field_um = 100
    um_per_pix = view_field_um / image_width_px 
    impurity_measurements, spacing_df = extract_pore_data(results, um_per_pix)

    # Save results to CSV files
    os.makedirs("temp", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(preprocessed_path or image_path))[0]
    imp_path = os.path.join("temp", f"{base_name}_impurity_measurements.csv")
    spacing_path = os.path.join("temp", f"{base_name}_centroid_spacing.csv")
    impurity_measurements.to_csv(imp_path, index=False)
    spacing_df.to_csv(spacing_path, index=False)
    print(f"Saved impurity measurements to {imp_path}")
    print(f"Saved centroid spacing to {spacing_path}")
    
if __name__ == "__main__":
    main()
