import json
import os
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import cv2
import numpy as np
import pytest
import torch
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from src.crack_measurement.model import (read_records, masks_for, UNet, train,
    predict, estimate_four, clip_guide)
from src.crack_measurement.gui import ImageView, Window, _suggested_pairs, anchor_to_center, scale_from_fov


def test_actual_dataset():
    records = read_records('data/Indentation_Image_Labels/per_image', 'data/Indentation Images')
    assert len(records) == 88
    path, item, names = records[0]
    image = cv2.imread(str(path), 0)
    target = masks_for(item, names, image.shape)
    assert target.shape == (2, *image.shape)
    assert target[0].sum() > 0 and target[1].sum() > 0


def test_duplicate_records_are_not_double_counted(tmp_path):
    source = json.loads(Path('data/Indentation_Image_Labels/Labels.json').read_text())
    (tmp_path/'all.json').write_text(json.dumps(source))
    (tmp_path/'duplicate.json').write_text(json.dumps({**source, 'items': source['items'][:1]}))
    assert len(read_records(tmp_path, 'data/Indentation Images')) == 88


def test_training_and_checkpoint_roundtrip(tmp_path):
    torch.set_num_threads(1)
    items = []
    for i in range(4):
        image = np.full((64, 80), 160, np.uint8)
        cv2.line(image, (10, 32), (70, 32), 0, 2)
        cv2.imwrite(str(tmp_path/f'{i}.png'), image)
        items.append({'id': str(i), 'image': {'path': f'{i}.png'}, 'annotations': [
            {'type': 'polyline', 'label_id': 0, 'points': [10, 32, 70, 32]},
            {'type': 'bbox', 'label_id': 1, 'bbox': [30, 22, 20, 20]}]})
    labels = tmp_path/'labels.json'
    labels.write_text(json.dumps({'categories': {'label': {'labels': [{'name': 'Crack'},
                          {'name': 'Indentation'}]}}, 'items': items}))
    output = tmp_path/'model.pt'
    messages = []
    assert train(labels, tmp_path, output, 1, 64, messages.append, lambda: False) == str(output)
    saved = torch.load(output, weights_only=True)
    assert set(saved['train_ids']).isdisjoint(saved['validation_ids'])
    maps = predict(image, output)
    assert maps.shape == (2, 64, 80)
    assert np.isfinite(maps).all()
    assert messages


def test_four_endpoint_chords_and_rotated_diamond():
    for angle in (0, .35, -.5):
        maps = np.zeros((2, 240, 240), np.float32)
        maps[1, 95:145, 95:145] = 1
        for i in range(4):
            direction = np.array([np.cos(angle+i*np.pi/2), np.sin(angle+i*np.pi/2)])
            a, b = np.rint(120+direction*30).astype(int), np.rint(120+direction*90).astype(int)
            cv2.line(maps[0], tuple(a), tuple(b), 1, 3)
        result = estimate_four(maps)
        assert len(result) == 4
        for a, b in result:
            assert np.linalg.norm(b-a) == pytest.approx(60, abs=5)


def test_partial_crack_evidence_returns_available_lines():
    maps = np.zeros((2, 240, 240), np.float32)
    maps[1, 95:145, 95:145] = 1
    cv2.line(maps[0], (150, 120), (210, 120), 1, 3)
    found = _suggested_pairs(maps)
    # Half-diagonals from the indentation plus any resolvable outer cracks.
    assert len(found) >= 1
    assert any(np.linalg.norm(end - start) > 20 for start, end in found)


def test_missing_evidence_rejected():
    with pytest.raises(ValueError, match='indentation'):
        estimate_four(np.zeros((2, 100, 100), np.float32))


def test_perpendicular_guides_reach_image_bounds():
    endpoint = np.array([40., 30.])
    direction = np.array([.6, .8])
    a, b = clip_guide(endpoint, direction, 100, 80)
    assert np.dot(b-a, direction) == pytest.approx(0)
    for p in (a, b):
        assert any(np.isclose([p[0], p[1], p[0]-100, p[1]-80], 0))
        assert 0 <= p[0] <= 100 and 0 <= p[1] <= 80


@pytest.fixture(scope='module')
def qt_app():
    return QApplication.instance() or QApplication([])


def test_measurements_share_one_center():
    center, lines = anchor_to_center([
        [np.array([0., 0.]), np.array([10., 0.])],
        [np.array([1., 1.]), np.array([0., 12.])],
    ])
    assert len(lines) == 2
    assert np.allclose(lines[0][0], center)
    assert np.allclose(lines[1][0], center)
    assert np.linalg.norm(lines[0][1]-lines[1][1]) > 5


def test_fov_scale_uses_printed_width_and_height():
    assert scale_from_fov(1280, 1024, 17.1, 12.8) == pytest.approx((17.1/1280 + 12.8/1024)/2)
    assert scale_from_fov(1000, 800, 10, 0) == pytest.approx(.01)
    with pytest.raises(ValueError):
        scale_from_fov(100, 100, 0, 0)


def test_outer_end_moves_freely_around_the_shared_center(qt_app, tmp_path):
    path = tmp_path/'image.png'
    cv2.imwrite(str(path), np.zeros((220, 220), np.uint8))
    view = ImageView(); view.resize(500, 500); view.show(); view.load(path)
    view.center = np.array([100., 100.])
    view.measurements = [[view.center.copy(), np.array([160., 100.])]]
    view.resetTransform(); view.scale(2, 2)
    begin = view.mapFromScene(160, 100)
    end = view.mapFromScene(100, 170)
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=begin)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=end)
    assert np.allclose(view.measurements[0][0], view.center)
    assert np.allclose(view.measurements[0][1], [100, 170], atol=1)
    view.close()


def test_dragging_yellow_line_rotates_around_its_center(qt_app, tmp_path):
    path = tmp_path/'image.png'
    cv2.imwrite(str(path), np.zeros((220, 220), np.uint8))
    view = ImageView(); view.resize(500, 500); view.show(); view.load(path)
    view.measurements = [[np.array([40., 100.]), np.array([140., 100.])]]
    view.resetTransform(); view.scale(2, 2)
    length = np.linalg.norm(view.measurements[0][1]-view.measurements[0][0])
    begin = view.mapFromScene(100, 100)
    end = view.mapFromScene(90, 150)
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=begin)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=end)
    assert np.linalg.norm(view.measurements[0][1]-view.measurements[0][0]) == pytest.approx(length, abs=.5)
    assert abs(view.measurements[0][1][0]-view.measurements[0][0][0]) < 5
    view.close()


def test_zoom_scale_and_drag_are_in_original_pixels(qt_app, tmp_path):
    path = tmp_path/'image.png'
    cv2.imwrite(str(path), np.zeros((200, 300), np.uint8))
    view = ImageView(); view.resize(600, 400); view.show(); view.load(path)
    view.measurements = [[np.array([50., 100.]), np.array([150., 100.])]]
    view.scale_um = .5
    view.refresh()
    view.resetTransform(); view.scale(2, 2)
    assert np.linalg.norm(view.measurements[0][1]-view.measurements[0][0])*.5 == 50
    # Drag the far endpoint guide by 20 original pixels, at a zoomed view.
    begin = view.mapFromScene(150, 100)
    end = view.mapFromScene(170, 100)
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=begin)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=end)
    assert np.linalg.norm(view.measurements[0][1]-view.measurements[0][0]) == pytest.approx(120, abs=1)
    assert any('60.' in item.text() for item in view.overlays if hasattr(item, 'text'))
    # A plain drag follows the cursor, including off the original line.
    begin = view.mapFromScene(170, 100)
    end = view.mapFromScene(170, 140)
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=begin)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=end)
    assert view.measurements[0][1][1] == pytest.approx(140, abs=1)
    assert np.allclose(view.measurements[0][0], [50, 100])
    # Shift-drag rotates around the opposite endpoint without changing length.
    anchor = view.measurements[0][0].copy()
    length = np.linalg.norm(view.measurements[0][1]-anchor)
    begin = view.mapFromScene(*view.measurements[0][1])
    end = view.mapFromScene(float(anchor[0]+length*.8), float(anchor[1]+length*.6))
    QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.ShiftModifier, begin)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.ShiftModifier, end)
    assert np.linalg.norm(view.measurements[0][1]-anchor) == pytest.approx(length, abs=.1)
    assert view.measurements[0][1][1] > 150
    view.close()


def test_calibration_draw_uses_original_pixels(qt_app, tmp_path):
    path = tmp_path/'image.png'
    cv2.imwrite(str(path), np.zeros((200, 300), np.uint8))
    view = ImageView(); view.resize(600, 400); view.show(); view.load(path)
    view.resetTransform(); view.scale(1.7, 1.7)
    lengths = []
    view.calibration.connect(lengths.append)
    view.calibrating = True
    begin, end = view.mapFromScene(50, 50), view.mapFromScene(110, 130)
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=begin)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=end)
    assert lengths[0] == pytest.approx(100, abs=1)
    view.close()


def test_window_smoke(qt_app):
    window = Window()
    window.show()
    qt_app.processEvents()
    assert len(window.actions) >= 8
    assert window.table.columnCount() == 4
    assert 'Estimate accuracy' in window.accuracy_box.text()
    window.close()


def test_estimate_bundle_includes_accuracy_meta():
    from src.crack_measurement.gui import _suggested_bundle
    maps = np.zeros((2, 240, 240), np.float32)
    maps[1, 95:145, 95:145] = 1
    for i in range(4):
        direction = np.array([np.cos(i * np.pi / 2), np.sin(i * np.pi / 2)])
        a = np.rint(120 + direction * 30).astype(int)
        b = np.rint(120 + direction * 90).astype(int)
        cv2.line(maps[0], tuple(a), tuple(b), 1, 3)
    center, pairs, meta = _suggested_bundle(maps)
    assert center is not None
    assert len(pairs) == len(meta) >= 4
    assert any(item['role'] == 'half_diagonal' for item in meta)
    assert any(item['role'] == 'crack_chord' for item in meta)
    assert all(item.get('confidence') is not None for item in meta)


def test_add_crack_line_by_dragging(qt_app, tmp_path):
    path = tmp_path/'image.png'
    cv2.imwrite(str(path), np.zeros((200, 300), np.uint8))
    view = ImageView(); view.resize(600, 400); view.show(); view.load(path)
    view.resetTransform(); view.scale(2, 2)
    view.adding = True
    begin = view.mapFromScene(40, 50)
    end = view.mapFromScene(120, 90)
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=begin)
    QTest.mouseMove(view.viewport(), end)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=end)
    assert view.adding is False
    assert len(view.measurements) == 1
    assert np.allclose(view.measurements[0][0], [40, 50], atol=1)
    assert np.allclose(view.measurements[0][1], [120, 90], atol=1)
    view.close()


def test_export_measurements_writes_reviewed_json(qt_app, tmp_path, monkeypatch):
    from PyQt5.QtWidgets import QFileDialog, QMessageBox

    path = tmp_path/'indentation_99.png'
    cv2.imwrite(str(path), np.zeros((200, 300), np.uint8))
    window = Window()
    window.view.load(path)
    window.view.scale_um = .5
    window.view.scale_set = True
    window.scale_method = 'fov'
    window.view.measurements = [[np.array([0., 0.]), np.array([30., 40.])]]
    output = tmp_path/'reviewed.json'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(output), 'JSON files (*.json)'))
    monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: None)

    window.export_measurements()

    data = json.loads(output.read_text())
    assert data['reviewed'] is True
    assert data['predictions_are_ground_truth'] is False
    assert data['training_ready'] is True
    assert data['image'] == 'indentation_99.png'
    assert data['scale']['um_per_pixel'] == pytest.approx(.5)
    assert data['scale']['method'] == 'fov'
    assert data['measurements'][0]['length_px'] == pytest.approx(50)
    assert data['measurements'][0]['length_um'] == pytest.approx(25)
    assert data['summary_um']['longest'] == pytest.approx(25)
    assert data['summary_um']['total'] == pytest.approx(25)
    window.close()


def test_estimation_requires_scale_for_each_image(qt_app, tmp_path, monkeypatch):
    from PyQt5.QtWidgets import QInputDialog, QMessageBox

    path = tmp_path/'image.png'
    cv2.imwrite(str(path), np.zeros((200, 300), np.uint8))
    window = Window()
    window.checkpoint = tmp_path/'model.pt'
    window.checkpoint.touch()
    warnings, jobs = [], []
    monkeypatch.setattr(QMessageBox, 'warning', lambda parent, title, message: warnings.append(message))
    monkeypatch.setattr(window, 'start_job', lambda *args: jobs.append(args))
    assert not window.view.scale_set
    window.view.load(path)
    generate = next(button for button in window.actions if button.text().startswith('Generate'))
    generate.click()
    assert len(warnings) == 1 and 'Set scale' in warnings[-1]
    assert not jobs

    monkeypatch.setattr(QInputDialog, 'getDouble', lambda *args: (10, False))
    window.calibrate(100)
    assert not window.view.scale_set
    window.generate()
    assert len(warnings) == 2 and not jobs

    monkeypatch.setattr(QInputDialog, 'getDouble', lambda *args: (10, True))
    window.calibrate(100)
    assert window.view.scale_set
    assert window.view.scale_um == pytest.approx(.1)
    window.generate()
    assert len(jobs) == 1

    window.view.load(path)
    assert not window.view.scale_set
    window.generate()
    assert len(warnings) == 3 and len(jobs) == 1
    window.close()


def test_microscope_tiffs_load_without_opencv_metadata_warnings(monkeypatch, capfd):
    from PIL import Image
    from src.crack_measurement.model import load_grayscale
    def forbidden(*args, **kwargs):
        raise AssertionError('TIFF should use Pillow rather than OpenCV')
    monkeypatch.setattr(cv2, 'imread', forbidden)
    for path in Path('data/Indentation Images').glob('*.tif'):
        with Image.open(path) as image:
            expected = np.array(image.convert('L'))
        actual = load_grayscale(path)
        np.testing.assert_array_equal(actual, expected)
    assert 'TIFF_Warning' not in capfd.readouterr().err


def test_16_bit_tiff_scaling(tmp_path):
    from PIL import Image
    from src.crack_measurement.model import load_grayscale
    pixels = np.array([[0, 256, 32768, 65535]], dtype=np.uint16)
    path = tmp_path/'test.tiff'
    Image.fromarray(pixels).save(path)
    np.testing.assert_array_equal(load_grayscale(path), [[0, 1, 128, 255]])
