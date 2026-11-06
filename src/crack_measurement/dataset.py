"""Label audit, calibration, and image-level splits for crack measurement."""
import csv
import json
from pathlib import Path

import numpy as np

from .model import chord_from_group, radial_groups, read_records

SCALE_PIXELS = 100
SCALE_UNIT_ASSUMPTION = (
    'Length.csv column Length is treated as micrometers per 100 pixels. '
    'The file has no unit field. This matches the application default of 10 µm per 100 pixels '
    'when Length is 10, and the team description of a 100-pixel scale, but it is not independently verified.'
)


def load_calibration(path):
    """Map image file name to the Length.csv value."""
    path = Path(path)
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or 'ImageName' not in reader.fieldnames or 'Length' not in reader.fieldnames:
            raise ValueError('Length.csv must contain ImageName and Length columns.')
        return {row['ImageName']: float(row['Length']) for row in reader}


def micrometers_per_pixel(length_value):
    return float(length_value) / SCALE_PIXELS


def _annotation_counts(item, names):
    counts = {'crack_polylines': 0, 'scratch_polylines': 0, 'indentation_boxes': 0, 'other': 0}
    for annotation in item['annotations']:
        name = names[annotation['label_id']]
        kind = annotation['type']
        if kind == 'polyline' and name == 'crack':
            counts['crack_polylines'] += 1
        elif kind == 'polyline' and name == 'misc. scratches':
            counts['scratch_polylines'] += 1
        elif kind == 'bbox' and name == 'indentation':
            counts['indentation_boxes'] += 1
        else:
            counts['other'] += 1
    return counts


def audit_records(records, calibration):
    """Summarize annotation coverage. Does not decide that an image is blurry or off-frame."""
    per_image = []
    missing_scale = []
    for path, item, names in records:
        counts = _annotation_counts(item, names)
        scale = calibration.get(path.name)
        if scale is None:
            missing_scale.append(path.name)
        per_image.append({'image': path.name, **counts, 'scale_length': scale})
    crack_counts = [row['crack_polylines'] for row in per_image]
    return {
        'images': len(per_image),
        'annotation_kinds': {
            'crack_polylines': int(sum(crack_counts)),
            'scratch_polylines': int(sum(row['scratch_polylines'] for row in per_image)),
            'indentation_boxes': int(sum(row['indentation_boxes'] for row in per_image)),
            'point_landmarks': 0,
        },
        'crack_polylines_per_image': {
            'min': int(min(crack_counts) if crack_counts else 0),
            'max': int(max(crack_counts) if crack_counts else 0),
            'mean': float(np.mean(crack_counts) if crack_counts else 0),
        },
        'images_without_cracks': [row['image'] for row in per_image if row['crack_polylines'] == 0],
        'images_without_indentation': [row['image'] for row in per_image if row['indentation_boxes'] == 0],
        'images_with_multiple_indentations': [
            row['image'] for row in per_image if row['indentation_boxes'] > 1],
        'images_with_exactly_four_crack_polylines': int(sum(count == 4 for count in crack_counts)),
        'calibration': {
            'mapped_images': int(sum(row['scale_length'] is not None for row in per_image)),
            'missing_images': missing_scale,
            'scale_pixels': SCALE_PIXELS,
            'unit_assumption': SCALE_UNIT_ASSUMPTION,
            'distinct_length_values': sorted({row['scale_length'] for row in per_image if row['scale_length'] is not None}),
        },
        'label_limitations': [
            'Annotations are Datumaro crack polylines, miscellaneous-scratch polylines, and indentation boxes.',
            'There are no indentation-corner points, crack-tip points, or suitability flags.',
            'Crack polylines are fragmented. No image is stored as the eight-measurement half-diagonal protocol.',
            'Branching, off-image cracks, blur, and heavy damage are not marked, so they cannot be excluded automatically.',
            'Image names do not identify a specimen or experiment, so splits are by image only.',
            'No researcher-approved crack-length reference exists. Held-out scores use mask overlap and a radial-span proxy.',
            'Whether crack length starts at the indentation corner or center is not recorded.',
        ],
        'per_image': per_image,
    }


def eligible(record):
    _path, item, names = record
    counts = _annotation_counts(item, names)
    return counts['crack_polylines'] > 0 and counts['indentation_boxes'] > 0


def split_records(records, seed=42, test_fraction=.2, validation_fraction=.2):
    """Hold out a test set, then split the remainder into validation and training.

    Related patches cannot leak because each record is one full image. Specimen
    leakage is still possible: the file names do not identify specimens.
    """
    included = [record for record in records if eligible(record)]
    excluded = [record[0].name for record in records if not eligible(record)]
    if len(included) < 3:
        raise ValueError('At least three images with both cracks and an indentation box are required.')
    order = np.random.default_rng(seed).permutation(len(included))
    test_count = max(1, round(len(included) * test_fraction))
    remaining = len(included) - test_count
    validation_count = max(1, round(remaining * validation_fraction))
    if test_count + validation_count >= len(included):
        raise ValueError('Split fractions leave no training images.')
    test_index = order[:test_count]
    validation_index = order[test_count:test_count + validation_count]
    train_index = order[test_count + validation_count:]
    groups = {
        'test': [included[i] for i in test_index],
        'validation': [included[i] for i in validation_index],
        'train': [included[i] for i in train_index],
    }
    description = {
        'split_level': 'image',
        'specimen_ids_available': False,
        'seed': seed,
        'test_fraction': test_fraction,
        'validation_fraction_of_remainder': validation_fraction,
        'excluded_missing_crack_or_indentation': excluded,
        'test': [record[0].name for record in groups['test']],
        'validation': [record[0].name for record in groups['validation']],
        'train': [record[0].name for record in groups['train']],
    }
    return groups, description


def proxy_radial_chords(item, names, min_points=10):
    """Straight radial spans of labeled crack points around the largest indentation box.

    This is an evaluation proxy derived from fragmented polylines. It is not a
    researcher-approved half-diagonal or crack length, and empty directions are omitted.
    """
    boxes = []
    points = []
    for annotation in item['annotations']:
        name = names[annotation['label_id']]
        if annotation['type'] == 'bbox' and name == 'indentation':
            x, y, width, height = annotation['bbox']
            boxes.append((width * height, np.array([x + width / 2, y + height / 2], float)))
        elif annotation['type'] == 'polyline' and name == 'crack':
            points.append(np.asarray(annotation['points'], float).reshape(-1, 2))
    if not boxes or not points:
        return []
    center = max(boxes, key=lambda box: box[0])[1]
    points = np.vstack(points)
    chords = []
    for _sector, group in radial_groups(points, center):
        if len(group) < min_points:
            continue
        start, end, angle, length = chord_from_group(group, center)
        chords.append({'start': start, 'end': end, 'angle': angle, 'length_px': length})
    return chords


def binary_dice(prediction, target, threshold=.5):
    predicted = prediction > threshold
    truth = target > .5
    intersection = np.logical_and(predicted, truth).sum()
    total = predicted.sum() + truth.sum()
    if total == 0:
        return 1.
    return float(2 * intersection / total)


def match_chords(references, predictions, tolerance=np.pi / 5):
    """Match chords by direction. Unmatched references are misses; unmatched predictions are invalid suggestions."""
    used = set()
    pairs = []
    invalid = 0
    for prediction in predictions:
        best = None
        best_delta = tolerance
        for index, reference in enumerate(references):
            if index in used:
                continue
            delta = abs(np.angle(np.exp(1j * (prediction['angle'] - reference['angle']))))
            delta = min(delta, abs(np.pi - delta))
            if delta <= best_delta:
                best, best_delta = index, delta
        if best is None:
            invalid += 1
        else:
            used.add(best)
            pairs.append((references[best], prediction))
    return pairs, len(references) - len(used), invalid


def length_summary(lengths_um):
    values = [float(value) for value in lengths_um]
    if not values:
        return {'count': 0, 'each_um': [], 'longest_um': None, 'total_um': 0.}
    return {'count': len(values), 'each_um': values,
            'longest_um': max(values), 'total_um': float(sum(values))}


def load_dataset(labels, images):
    return read_records(labels, images)


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
