"""Reviewed measurement files. Unreviewed model output must not be stored as ground truth."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROLES = {'crack_chord', 'half_diagonal', 'unknown'}


def correction_record(image, measurements, calibration_um_per_100_px, source_checkpoint, notes='',
                      scale_um_per_pixel=None, image_path=None, image_size=None,
                      scale_method=None, details=None):
    """Build a researcher-reviewed measurement record.

    ``measurements`` items use original-image pixel coordinates and include
    ``deleted`` when the researcher rejected a suggestion. Predictions are never
    marked reviewed by this function.
    """
    if scale_um_per_pixel is None and calibration_um_per_100_px is not None:
        scale_um_per_pixel = float(calibration_um_per_100_px) / 100
    stored = []
    for index, measurement in enumerate(measurements):
        role = measurement.get('role', 'crack_chord')
        if role not in ROLES:
            raise ValueError(f'Unsupported measurement role: {role}')
        start = [float(measurement['start_xy'][0]), float(measurement['start_xy'][1])]
        end = [float(measurement['end_xy'][0]), float(measurement['end_xy'][1])]
        length_px = math.hypot(end[0] - start[0], end[1] - start[1])
        stored.append({
            'id': int(measurement.get('id', index)),
            'role': role,
            'start_xy': start,
            'end_xy': end,
            'length_px': length_px,
            'length_um': None if scale_um_per_pixel is None else length_px * float(scale_um_per_pixel),
            'deleted': bool(measurement.get('deleted', False)),
            'suitable': bool(measurement.get('suitable', not measurement.get('deleted', False))),
        })
    lengths_um = [item['length_um'] for item in stored
                  if item['length_um'] is not None and item['suitable'] and not item['deleted']]
    record = {
        'schema_version': 1,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'image': Path(image).name,
        'image_path': None if image_path is None else str(image_path),
        'image_size_px': None if image_size is None else {
            'width': int(image_size[0]), 'height': int(image_size[1])},
        'reviewed': True,
        'predictions_are_ground_truth': False,
        'training_ready': bool(stored and scale_um_per_pixel is not None),
        'calibration_um_per_100_px': None if calibration_um_per_100_px is None else float(calibration_um_per_100_px),
        'scale': {
            'um_per_pixel': None if scale_um_per_pixel is None else float(scale_um_per_pixel),
            'method': scale_method,
            'unit': 'micrometers',
        },
        'calibration_unit_assumption': 'micrometers',
        'source_checkpoint': None if source_checkpoint is None else str(source_checkpoint),
        'reference_convention': 'unconfirmed',
        'measurements': stored,
        'summary_um': {
            'count': len(lengths_um),
            'each': lengths_um,
            'longest': None if not lengths_um else max(lengths_um),
            'total': float(sum(lengths_um)),
        },
        'notes': notes,
    }
    if details:
        for key, value in details.items():
            if key not in {'reviewed', 'predictions_are_ground_truth'}:
                record[key] = value
    return record


def save_correction(path, record):
    if not record.get('reviewed'):
        raise ValueError('Only researcher-reviewed corrections can be saved for future training.')
    if record.get('predictions_are_ground_truth'):
        raise ValueError('Model predictions cannot be saved as ground truth.')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding='utf-8')
    return path
