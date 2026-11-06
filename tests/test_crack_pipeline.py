import json
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

from src.crack_measurement.corrections import correction_record, save_correction
from src.crack_measurement.dataset import (audit_records, load_calibration, load_dataset, match_chords,
                                           proxy_radial_chords, split_records)
from src.crack_measurement.encoder import EncoderSeg
from src.crack_measurement.model import predict
from src.crack_measurement.pipeline import evaluate, train_encoder


def test_real_labels_are_polylines_and_boxes_not_landmarks():
    records = load_dataset('data/Indentation_Image_Labels/per_image', 'data/Indentation Images')
    report = audit_records(records, load_calibration('Length.csv'))
    assert report['images'] == 88
    assert report['annotation_kinds']['point_landmarks'] == 0
    assert report['annotation_kinds']['crack_polylines'] > 0
    assert report['annotation_kinds']['indentation_boxes'] >= 88
    assert report['images_with_exactly_four_crack_polylines'] == 0
    assert report['calibration']['mapped_images'] == 88
    groups, description = split_records(records, seed=42)
    names = [name for key in ('train', 'validation', 'test') for name in description[key]]
    assert len(names) == len(set(names))
    assert set(description['test']).isdisjoint(description['train'])
    assert set(description['test']).isdisjoint(description['validation'])
    assert description['specimen_ids_available'] is False
    assert all(record[0].name not in description['test'] for record in groups['train'])


def test_proxy_chord_uses_straight_span_and_can_omit_directions():
    points = []
    for x in range(50, 130):
        points.extend([x, 50])
    item = {'annotations': [
        {'type': 'bbox', 'label_id': 1, 'bbox': [20, 40, 20, 20]},
        {'type': 'polyline', 'label_id': 0, 'points': points},
    ]}
    names = ['crack', 'indentation']
    chords = proxy_radial_chords(item, names, min_points=10)
    assert len(chords) == 1
    assert 60 < chords[0]['length_px'] < 80
    pairs, missed, invalid = match_chords(chords, [{
        'angle': chords[0]['angle'], 'length_px': chords[0]['length_px'] + 3}])
    assert missed == 0 and invalid == 0 and abs(pairs[0][1]['length_px'] - pairs[0][0]['length_px']) == 3


def _synthetic_dataset(folder):
    items = []
    for index in range(4):
        image = np.full((64, 80), 180, np.uint8)
        cv2.line(image, (5, 32), (75, 32), 0, 2)
        cv2.imwrite(str(folder / f'{index}.png'), image)
        points = [value for x in range(5, 76) for value in (x, 32)]
        items.append({'id': str(index), 'image': {'path': f'{index}.png'}, 'annotations': [
            {'type': 'polyline', 'label_id': 0, 'points': points},
            {'type': 'bbox', 'label_id': 1, 'bbox': [30, 22, 20, 20]}]})
    labels = folder / 'labels.json'
    labels.write_text(json.dumps({'categories': {'label': {'labels': [
        {'name': 'Crack'}, {'name': 'Indentation'}]}}, 'items': items}))
    scale = folder / 'scale.csv'
    scale.write_text('ImageName,Length\n' + '\n'.join(f'{i}.png,10.0' for i in range(4)) + '\n')
    return labels, scale


def test_encoder_checkpoint_round_trip_and_held_out_evaluation(tmp_path):
    torch.set_num_threads(1)
    labels, scale = _synthetic_dataset(tmp_path)
    messages = []
    destination = train_encoder(
        labels, tmp_path, scale, tmp_path / 'run', epochs=1, size=64, pretrained=False,
        freeze_epochs=0, seed=1, batch_size=2, progress=messages.append, cancelled=lambda: False)
    assert Path(destination).is_file()
    assert (tmp_path / 'run' / 'config.json').is_file()
    assert (tmp_path / 'run' / 'split.json').is_file()
    split = json.loads((tmp_path / 'run' / 'split.json').read_text())
    assert set(split['test']).isdisjoint(split['train'])
    image = cv2.imread(str(tmp_path / '0.png'), cv2.IMREAD_GRAYSCALE)
    maps = predict(image, destination)
    assert maps.shape == (2, 64, 80)
    metrics = evaluate(destination, labels, tmp_path, scale, split='test')
    assert metrics['predictions_are_ground_truth'] is False
    assert metrics['images'] == len(split['test'])
    assert 'mean_crack_dice' in metrics
    assert messages
    from src.crack_measurement.encoder import EncoderSeg, MicroNetSeg
    model = EncoderSeg(pretrained=False).eval()
    with torch.no_grad():
        logits = model(torch.zeros(1, 1, 64, 64))
    assert logits.shape == (1, 2, 64, 64)
    micronet = MicroNetSeg(pretrained=False).eval()
    with torch.no_grad():
        micronet_logits = micronet(torch.zeros(1, 1, 64, 64))
    assert micronet_logits.shape == (1, 2, 64, 64)


def test_corrections_reject_unreviewed_predictions(tmp_path):
    record = correction_record('indentation_1.bmp', [{
        'start_xy': [1, 2], 'end_xy': [8, 2], 'role': 'crack_chord'}], 10, 'checkpoint.pt',
        image_size=(1280, 1026), scale_method='drawn_line')
    assert record['reviewed'] is True
    assert record['predictions_are_ground_truth'] is False
    assert record['reference_convention'] == 'unconfirmed'
    assert record['training_ready'] is True
    assert record['image_size_px'] == {'width': 1280, 'height': 1026}
    assert record['measurements'][0]['length_px'] == 7
    assert record['measurements'][0]['length_um'] == pytest.approx(0.7)
    assert record['summary_um']['total'] == pytest.approx(0.7)
    save_correction(tmp_path / 'reviewed.json', record)
    record['reviewed'] = False
    try:
        save_correction(tmp_path / 'raw.json', record)
    except ValueError as exc:
        assert 'reviewed' in str(exc)
    else:
        raise AssertionError('unreviewed output was saved')
