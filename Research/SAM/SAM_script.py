import torch
#import pretrained_microscopy_models as pmm
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time 

#image_path = "/Users/nicholaslopez/Desktop/School Work/Capstone/-wsum-fullstackapp-/src/res/Impurity_SEM_Images/61620A_IP_09_53x35/61620A_IP_09_53x35_05.tif"

#image_path = "/Users/nicholaslopez/Desktop/Screenshot 2025-09-01 at 8.33.19 PM.png"

#image_path = "/Users/nicholaslopez/Desktop/Screenshot 2025-09-09 at 9.30.16 PM.png"

#image_path = "/Users/nicholaslopez/Desktop/Screenshot 2025-09-09 at 9.31.39 PM.png"

image_path = "Research/UNET/test/images/test_image.png"


from transformers import pipeline
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

from PyQt5.QtCore import QRect

def sam_segment_script(filename:str,  saved_crop_rect: QRect = None):

    start = time.perf_counter()


    # --- 1. Load Model ---
    print("Loading Segment Anything Model (SAM)...")
    generator = pipeline("mask-generation", model="facebook/sam-vit-huge", device="cpu")

    image_path = filename

    # --- 2. Load Image ---
    # Replace with the path to your image
    image = Image.open(image_path).convert("RGB")

    # --- 3. Run Segmentation ---
    print("Running segmentation...")
    outputs = generator(image, points_per_batch=64)
    masks = outputs["masks"]

    # --- 4. Visualize Results ---
    def show_mask(mask, ax, random_color=False):
        """Helper function to display a single mask."""
        if random_color:
            color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
        else:
            color = np.array([1.0, 1.0, 1.0, 0.6])  # This gives the white transparency, can change it to anything

        h, w = mask.shape[-2:]
        mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
        ax.imshow(mask_image)

    end = time.perf_counter()

    total_time = end - start

    print(f"Total compute time: {total_time}")

    plt.figure(figsize=(12, 6))

    # Original Image
    plt.subplot(1, 2, 1)
    plt.title("Original Image")
    plt.imshow(image)
    plt.axis('off')

    # Image with Masks
    plt.subplot(1, 2, 2)
    plt.title("Segmented Impurities (SAM)")
    plt.imshow(image)
    ax = plt.gca()
    for mask in masks:
        show_mask(mask, ax=ax, random_color=False)
    plt.axis('off')

    plt.show()