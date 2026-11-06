# Indentation crack measurement

Launch from the repository root:

```sh
python crack_measurement.py
```

Or open the **Crack Measurement** tab in the main desktop app:

```sh
python src/app/main.py
```

Use the project's Python environment with `PyQt5`, `torch`, `numpy`, and
`opencv-python`, and `Pillow` installed. These dependencies are already in `requirements.txt`.
The standalone launcher and the main-app tab share the same measurement panel.

## Workflow

1. **Train U-Net on JSONs**: choose the Datumaro JSON file or a folder of individual
   JSONs, the corresponding image folder, a checkpoint destination, and epochs.
   Defaults use `data/Indentation_Image_Labels/per_image` and
   `data/Indentation Images`. You can type the original `Labels.json` path instead.
   Training runs in the background. **Cancel training** stops after the current
   batch. The best completed checkpoint remains available.
2. **Load indentation image**: open a BMP, PNG, JPEG, or TIFF.
3. **Set scale**: choose **Draw a known length (original)** to drag a line across
   a known length and enter that distance in micrometers, or choose **Enter field
   of view (FOV)** and fill in the FOV width and/or height printed on the image.
   Calibration is specific to the current image; loading another image restores
   the default of 10 µm per 100 pixels and clears scale confirmation. Confirm
   calibration for each image before estimating cracks. Escape cancels drawing.
4. **Generate estimated crack lengths**: run the trained U-Net, then fit
   indentation half-diagonals plus radial crack chords when evidence exists.
   Directions without enough model evidence are omitted rather than forced.
   The colored lines are straight endpoint-to-endpoint measurements, not lengths
   along curved paths. The right-hand panel lists each line and shows an
   **estimate accuracy** percentage based on model-mask confidence along the
   suggested lines (not researcher-validated ground truth).
5. Inspect and adjust the overlays. Drag red tip handles freely, drag a colored
   line to rotate it, or **Shift-drag** an endpoint to rotate while keeping length
   fixed. Blue guides stay perpendicular to each measurement. Lengths update while
   dragging and in the measurements table.
6. **Add crack line**: if the model misses a visible crack, click **Add crack line**,
   then click at the start of the crack, drag to its tip, and release. The new line
   can then be moved or rotated like a generated line. Press Escape to cancel.
7. **Export measurements JSON**: after reviewing and correcting the lines, export
   them as a reviewed JSON record for future training. The file stores the image
   name and size, endpoint coordinates in original pixels, pixel and micrometer
   lengths, the scale and how it was set, the source checkpoint, and each,
   longest, and total crack-length summaries. Export asks for confirmation so
   unreviewed model output is not accidentally treated as training ground truth.
   Files default to `data/Indentation_Image_Labels/reviewed_measurements`.

The mouse wheel zooms. Middle-button dragging pans. **Fit image** restores the
full view. Coordinates and calibration always use the original image pixels;
zoom does not change measured length. Crack lengths always display in micrometers.
The initial scale is 10 µm per 100 pixels, but estimation requires completing
**Set scale** for the current image. Clicking estimation before calibration shows a pop-up.
**Load trained model** reuses a checkpoint from an earlier session. This accepts
the scratch U-Net (`models/crack_unet.pt`), the pretrained ResNet-18 encoder
(`models/crack_encoder_resnet18.pt`), or the NASA MicroNet ResNet-50 model
(`models/crack_micronet_resnet50.pt`).

## Model and data

`src/crack_measurement/model.py` implements a compact four-level U-Net trained
from scratch, without downloaded weights. It predicts two independent masks:
crack paths and an approximate indentation region. Crack polylines named `Crack`
are rasterized at five original pixels of thickness. `Misc. Scratches` are excluded
so incidental surface scratches do not become indentation crack targets.
Indentation bounding boxes provide the second target; they do not label the
actual diamond boundary.

Images are resized proportionally into a padded square for training and inference.
Inference removes padding and restores probability maps to the original image
size before computing endpoints. The default 512-pixel resolution is a starting
point; finer cracks may require a higher resolution. Rotation and flip augmentation
are applied to training images and masks together.

The seeded split reserves 20% of source images for validation before augmentation.
Training uses Adam and binary cross-entropy plus Dice loss. Only the checkpoint
with the lowest validation loss is saved. It includes the image split, training
resolution, epoch, and validation loss. Duplicate image paths across JSONs are
loaded only once. If multiple images show the same specimen, create a specimen-level
split before relying on validation scores; the current automatic split is by image.

## What the estimates mean

The postprocessor locates the predicted indentation center, groups crack pixels
into four approximately orthogonal directions, and fits a line to each group.
Endpoints use the second and ninety-eighth percentiles along each fitted axis to
reduce isolated-pixel noise. This is an editable approximation of the endpoints,
not a dedicated endpoint detector. Curvature, branching, separated segments,
incorrect segmentation, or an unusual diamond orientation can affect the estimates.
Insufficient evidence raises a message instead of creating four unsupported lines.
The threshold control allows adjustment of the foreground probability cutoff.

The dataset has 88 images. No production-quality model or validated accuracy is
bundled. Train before generating estimates, inspect the overlays, and evaluate
endpoint-distance errors on held-out specimens. Because indentation labels are
boxes, the model cannot learn an exact diamond boundary from those labels alone.
Adding diamond boundary masks and explicitly labeled four endpoint pairs would
improve crack-to-edge association and measurement evaluation.

The calibration assumes uniform physical scale in the image plane. The displayed
micrometer distance is Euclidean pixel distance multiplied by micrometers per
pixel. A single calibration cannot correct perspective or unequal axis scales.

## Encoder training pipeline

The application dialog still trains the compact U-Net from scratch. That model is the baseline. A separate pipeline trains a ResNet-18 encoder on the same rasterized crack and indentation masks, because the Datumaro files contain polylines and boxes rather than corner or crack-tip landmarks:

```sh
python -m src.crack_measurement.pipeline audit
python -m src.crack_measurement.pipeline train --epochs 5 --freeze-epochs 1 --pretrained
python -m src.crack_measurement.pipeline train --architecture micronet_unet --epochs 12 --freeze-epochs 3 --pretrained --size 512
python -m src.crack_measurement.pipeline evaluate --checkpoint runs/crack_measurement/<run>/best.pt
```

`--pretrained` with `encoder_seg` downloads ImageNet ResNet-18 weights. With
`micronet_unet` it downloads NASA MicroNet ImageNet→MicroNet ResNet-50 encoder
weights into `models/pretrained/`. The first `--freeze-epochs` update only the
decoder. The held-out test split is stored in the checkpoint and is not used for
training. `Load trained model` accepts U-Net, ResNet-18 encoder, and MicroNet
checkpoints.

`Length.csv` is applied as micrometers per 100 pixels. The CSV does not name its unit. Each, longest, and total lengths in the evaluation file describe unreviewed suggestions. Empty crack directions are omitted instead of forcing four measurements. Reviewed corrections use `correction-template` and must set `reviewed` true; the pipeline refuses to store model predictions as ground truth.

Mask Dice and radial-span error are proxy scores. They are not researcher-approved half-diagonal or crack-length references, and image names do not identify specimens.

## Verification

```sh
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_crack_measurement.py -q
```

Checks cover the real 88-image dataset, deduplication, a training/checkpoint/inference
round trip, rotated four-crack geometry, missing detections, perpendicular clipping,
zoom-independent calibration, endpoint dragging, rotation, and Qt window startup.

TIFF images use Pillow for decoding, avoiding OpenCV warnings about microscope-specific metadata tags. The source files are not modified.
