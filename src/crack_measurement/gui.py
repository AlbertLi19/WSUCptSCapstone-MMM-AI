"""Qt desktop UI; all measurements live in original image pixel coordinates."""
import math
from pathlib import Path

# Load PyTorch before NumPy and Qt. On Windows, importing those first can make
# c10.dll fail to initialize.
from .corrections import correction_record, save_correction
from .paths import (resource_root, default_checkpoint, training_checkpoint,
                    reviewed_measurements_dir)
from .model import (train, predict, estimate_indentation_measurements, clip_guide,
                    load_grayscale)

import numpy as np
import torch
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QPainter
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QInputDialog,
    QGraphicsView, QGraphicsScene, QDialog, QFormLayout, QSpinBox, QDoubleSpinBox,
    QLineEdit, QDialogButtonBox, QRadioButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QAbstractItemView, QSizePolicy)

ROOT = resource_root()
DEFAULT_SCALE_UM = 10 / 100

STYLE = """
QMainWindow, QWidget {
    background-color: #1e2329;
    color: #e8edf2;
    font-size: 12px;
}
QPushButton {
    background-color: #2f3842;
    border: 1px solid #46515c;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e8edf2;
}
QPushButton:hover { background-color: #3a4552; }
QPushButton:disabled { color: #7a8691; background-color: #262c33; }
QLabel { color: #d7dee6; }
QTableWidget {
    background-color: #171b20;
    alternate-background-color: #1f252c;
    gridline-color: #343c45;
    border: 1px solid #343c45;
    selection-background-color: #35506b;
}
QHeaderView::section {
    background-color: #2a3139;
    color: #d7dee6;
    border: 0px;
    padding: 6px;
}
QDoubleSpinBox, QSpinBox, QLineEdit {
    background-color: #171b20;
    border: 1px solid #46515c;
    border-radius: 3px;
    padding: 3px;
    color: #e8edf2;
}
QStatusBar { color: #aeb8c2; }
"""


def anchor_to_center(pairs):
    """Make every measurement start at one shared indentation center."""
    if not pairs:
        return None, []
    points = np.vstack([np.asarray(point, float) for pair in pairs for point in pair])
    centroid = points.mean(axis=0)
    inners, tips = [], []
    for start, end in pairs:
        start, end = np.asarray(start, float), np.asarray(end, float)
        if np.linalg.norm(start-centroid) <= np.linalg.norm(end-centroid):
            inners.append(start)
            tips.append(end)
        else:
            inners.append(end)
            tips.append(start)
    center = np.mean(inners, axis=0)
    return center, [[center.copy(), tip.copy()] for tip in tips]


def scale_from_fov(width_px, height_px, fov_width_um, fov_height_um):
    """Micrometers per pixel from the field of view printed on an image."""
    scales = []
    if fov_width_um > 0:
        scales.append(float(fov_width_um)/float(width_px))
    if fov_height_um > 0:
        scales.append(float(fov_height_um)/float(height_px))
    if not scales:
        raise ValueError('Enter the FOV width, height, or both, in micrometers.')
    return float(sum(scales)/len(scales))


def _default_meta(index, start, end, role='crack_chord', source='manual', confidence=None, label=None):
    start, end = np.asarray(start, float), np.asarray(end, float)
    angle = math.atan2(float(end[1]-start[1]), float(end[0]-start[0]))
    if label is None:
        prefix = 'Inner' if role == 'half_diagonal' else 'Outer'
        from .model import direction_label
        label = direction_label(angle, prefix) if source == 'estimated' else f'Line {index + 1}'
    return {
        'role': role,
        'label': label,
        'source': source,
        'confidence': confidence,
        'status': 'Estimated' if source == 'estimated' else 'Manual',
    }


class Job(QThread):
    progress = pyqtSignal(str)
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, function):
        super().__init__()
        self.function = function

    def run(self):
        try:
            self.result.emit(self.function(self))
        except Exception as exc:
            self.error.emit(str(exc))


class ImageView(QGraphicsView):
    calibration = pyqtSignal(float)
    changed = pyqtSignal()
    zoom_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setBackgroundBrush(QColor('#252a30'))
        self.image = None
        self.image_path = None
        self.measurements = []
        self.measurement_meta = []
        self.center = None
        self.overlays = []
        self.scale_um = DEFAULT_SCALE_UM
        self.scale_set = False
        self.calibrating = False
        self.adding = False
        self.drag = None
        self.pan = None
        self.setMouseTracking(True)

    def load(self, path):
        data = load_grayscale(path)
        self.scene().clear()
        self.overlays = []
        self.image = data
        self.image_path = Path(path)
        self.measurements = []
        self.measurement_meta = []
        self.center = None
        self.scale_um = DEFAULT_SCALE_UM
        self.scale_set = False
        self.calibrating = False
        self.adding = False
        self.drag = None
        h, w = data.shape
        qimage = QImage(data.data, w, h, data.strides[0], QImage.Format_Grayscale8).copy()
        self.scene().addPixmap(QPixmap.fromImage(qimage))
        self.scene().setSceneRect(0, 0, w, h)
        self.fit()
        self.changed.emit()

    def fit(self):
        if self.image is not None:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
            self.zoom_changed.emit(self.transform().m11())
            self.refresh()

    def set_zoom_factor(self, factor):
        if self.image is None:
            return
        current = self.transform().m11()
        target = max(.02, min(40., current * factor))
        self.scale(target / current, target / current)
        self.zoom_changed.emit(self.transform().m11())
        self.refresh()

    def wheelEvent(self, event):
        factor = 1.2 if event.angleDelta().y() > 0 else 1/1.2
        if .02 < self.transform().m11()*factor < 40:
            self.scale(factor, factor)
            self.zoom_changed.emit(self.transform().m11())
            self.refresh()
        event.accept()

    def point(self, position):
        p = self.mapToScene(position)
        h, w = self.image.shape
        return np.array([np.clip(p.x(), 0, w-1), np.clip(p.y(), 0, h-1)])

    def _add_item(self, item):
        item.setAcceptedMouseButtons(Qt.NoButton)
        self.overlays.append(item)
        return item

    def draw_line(self, a, b, color, width=1):
        pen = QPen(QColor(color), width)
        pen.setCosmetic(True)
        self._add_item(self.scene().addLine(*a, *b, pen))

    def _sync_meta(self):
        while len(self.measurement_meta) < len(self.measurements):
            index = len(self.measurement_meta)
            start, end = self.measurements[index]
            self.measurement_meta.append(_default_meta(index, start, end))
        self.measurement_meta = self.measurement_meta[:len(self.measurements)]

    def refresh(self):
        for item in self.overlays:
            self.scene().removeItem(item)
        self.overlays = []
        if self.image is None:
            return
        self._sync_meta()
        h, w = self.image.shape
        for i, (a, b) in enumerate(self.measurements):
            meta = self.measurement_meta[i]
            vector = b-a
            length = np.linalg.norm(vector)
            direction = vector/max(length, 1e-9)
            line_color = '#7fd0ff' if meta.get('role') == 'half_diagonal' else '#ffcf40'
            self.draw_line(a, b, line_color, 3)
            tip_radius = self._pixel_tolerance(5)
            tip_pen = QPen(QColor('#ff5b5b'), 1)
            tip_pen.setCosmetic(True)
            tip_brush = QColor('#ff5b5b')
            inner_pen = QPen(QColor('#38d6ff'), 1)
            inner_pen.setCosmetic(True)
            inner_brush = QColor('#38d6ff')
            for endpoint, is_tip in ((a, False), (b, True)):
                lo, hi = clip_guide(endpoint, direction, w-1, h-1)
                self.draw_line(lo, hi, '#4ea1ff', 1)
                pen = tip_pen if is_tip else inner_pen
                brush = tip_brush if is_tip else inner_brush
                self._add_item(self.scene().addEllipse(
                    endpoint[0]-tip_radius, endpoint[1]-tip_radius,
                    2*tip_radius, 2*tip_radius, pen, brush))
            text = f'[{i+1}] {length*self.scale_um:.2f} µm'
            item = self.scene().addSimpleText(text)
            item.setBrush(QColor('#ffe786'))
            item.setFlag(item.ItemIgnoresTransformations)
            item.setAcceptedMouseButtons(Qt.NoButton)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            midpoint = (a+b)/2
            item.setPos(float(midpoint[0]) + 4, float(midpoint[1]) - 10)
            self.overlays.append(item)
        if self.center is not None:
            radius = self._pixel_tolerance(6)
            pen = QPen(QColor('#ffffff'), 2)
            pen.setCosmetic(True)
            self._add_item(self.scene().addEllipse(
                self.center[0]-radius, self.center[1]-radius,
                2*radius, 2*radius, pen, QColor('#ffffff')))
        if (self.calibrating or self.adding) and self.drag is not None and isinstance(self.drag[0], np.ndarray):
            self.draw_line(self.drag[0], self.drag[1], '#38e5aa', 2)
        self.changed.emit()

    def _pixel_tolerance(self, screen_pixels):
        return screen_pixels/max(self.transform().m11(), .02)

    def hit_center(self, point):
        if self.center is None:
            return False
        return float(np.linalg.norm(point-self.center)) <= self._pixel_tolerance(18)

    def hit_guide(self, point):
        """Endpoint dots. Shared-center mode only exposes the outer tip."""
        tolerance = self._pixel_tolerance(18)
        best = None
        for i, (a, b) in enumerate(self.measurements):
            endpoints = ((1, b),) if self.center is not None else ((0, a), (1, b))
            for endpoint_index, endpoint in endpoints:
                distance = float(np.linalg.norm(point-endpoint))
                if distance <= tolerance and (best is None or distance < best[0]):
                    best = (distance, i, endpoint_index)
        return best

    def hit_line(self, point):
        """Colored measurement line. Dragging rotates around center or midpoint."""
        tolerance = self._pixel_tolerance(22)
        best = None
        for i, (a, b) in enumerate(self.measurements):
            span = b-a
            span_length = float(np.dot(span, span))
            if span_length < 1:
                continue
            placed = float(np.clip(np.dot(point-a, span)/span_length, 0, 1))
            distance = float(np.linalg.norm(point-(a+placed*span)))
            if distance <= tolerance and (best is None or distance < best[0]):
                best = (distance, i)
        return best

    def hit_blue(self, point):
        """Blue guide through the outer endpoint."""
        tolerance = self._pixel_tolerance(14)
        reach = self._pixel_tolerance(90)
        best = None
        for i, (a, b) in enumerate(self.measurements):
            direction = b-a
            length = float(np.linalg.norm(direction))
            if length < 1:
                continue
            direction = direction/length
            normal = np.array([-direction[1], direction[0]])
            distance = abs(float(np.dot(point-b, direction)))
            along = abs(float(np.dot(point-b, normal)))
            if distance <= tolerance and along <= reach and (best is None or distance < best[0]):
                best = (distance, i)
        return best

    def mousePressEvent(self, event):
        if self.image is None:
            return super().mousePressEvent(event)
        if event.button() == Qt.MiddleButton:
            self.pan = event.pos()
            return
        if event.button() == Qt.LeftButton:
            point = self.point(event.pos())
            if self.calibrating:
                self.drag = (point, point)
                return
            if self.adding:
                self.drag = (point, point)
                return
            if self.hit_center(point):
                self.drag = ('center', self.center.copy(), [pair[1].copy() for pair in self.measurements])
                return
            hit = self.hit_guide(point)
            if hit:
                _, i, endpoint = hit
                self.drag = ('tip', i) if self.center is not None and endpoint == 1 else (
                    i, endpoint, point, [p.copy() for p in self.measurements[i]],
                    bool(event.modifiers() & Qt.ShiftModifier))
                return
            line = self.hit_line(point)
            if line:
                self.drag = ('rotate', line[1], point, [p.copy() for p in self.measurements[line[1]]])
                return
            blue = self.hit_blue(point)
            if blue:
                self.drag = ('tip', blue[1]) if self.center is not None else (
                    'rotate', blue[1], point, [p.copy() for p in self.measurements[blue[1]]])
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.pan is not None:
            delta = event.pos()-self.pan
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()-delta.y())
            self.pan = event.pos()
            return
        if self.drag is not None:
            point = self.point(event.pos())
            if self.calibrating or self.adding:
                self.drag = (self.drag[0], point)
            elif self.drag[0] == 'center':
                self.center = point.copy()
                for index, tip in enumerate(self.drag[2]):
                    self.measurements[index][0] = self.center.copy()
                    self.measurements[index][1] = tip
            elif self.drag[0] == 'tip':
                index = self.drag[1]
                self.measurements[index][0] = self.center.copy()
                self.measurements[index][1] = point.copy()
                if index < len(self.measurement_meta):
                    self.measurement_meta[index]['status'] = 'Adjusted'
            elif self.drag[0] == 'rotate':
                _, index, initial, original = self.drag
                anchor = self.center if self.center is not None else (original[0]+original[1])/2
                start, current = initial-anchor, point-anchor
                if np.linalg.norm(start) < 5:
                    start = original[1]-anchor
                if np.linalg.norm(current) < 1 or np.linalg.norm(start) < 1:
                    return
                angle = math.atan2(current[1], current[0])-math.atan2(start[1], start[0])
                rotation = np.array([[math.cos(angle), -math.sin(angle)],
                                     [math.sin(angle), math.cos(angle)]])
                if self.center is not None:
                    tip = anchor+rotation@(original[1]-anchor)
                    h, w = self.image.shape
                    if 0 <= tip[0] <= w-1 and 0 <= tip[1] <= h-1:
                        self.measurements[index] = [anchor.copy(), tip]
                        if index < len(self.measurement_meta):
                            self.measurement_meta[index]['status'] = 'Adjusted'
                else:
                    pair = [anchor+rotation@(endpoint-anchor) for endpoint in original]
                    h, w = self.image.shape
                    if all(0 <= endpoint[0] <= w-1 and 0 <= endpoint[1] <= h-1 for endpoint in pair):
                        self.measurements[index] = pair
                        if index < len(self.measurement_meta):
                            self.measurement_meta[index]['status'] = 'Adjusted'
            else:
                i, endpoint, initial, original, rotate = self.drag
                anchor = original[1-endpoint]
                vector = original[endpoint]-anchor
                length = np.linalg.norm(vector)
                if rotate:
                    u, v = initial-anchor, point-anchor
                    angle = math.atan2(v[1], v[0])-math.atan2(u[1], u[0])
                    c, s = math.cos(angle), math.sin(angle)
                    candidate = anchor + np.array([[c, -s], [s, c]]) @ vector
                else:
                    candidate = point.copy()
                h, w = self.image.shape
                if (0 <= candidate[0] <= w-1 and 0 <= candidate[1] <= h-1
                        and np.linalg.norm(candidate-anchor) >= 1):
                    pair = [p.copy() for p in original]
                    pair[endpoint] = candidate
                    self.measurements[i] = pair
                    if i < len(self.measurement_meta):
                        self.measurement_meta[i]['status'] = 'Adjusted'
            self.refresh()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.pan = None
            return
        if event.button() == Qt.LeftButton and self.drag is not None:
            self.mouseMoveEvent(event)
            if self.calibrating:
                distance = float(np.linalg.norm(self.drag[1]-self.drag[0]))
                self.drag = None
                self.calibrating = False
                self.refresh()
                if distance > 1:
                    self.calibration.emit(distance)
            elif self.adding:
                start, end = self.drag
                distance = float(np.linalg.norm(end-start))
                self.drag = None
                self.adding = False
                if distance > 1:
                    self.center = None
                    self.measurements.append([start.copy(), end.copy()])
                    self.measurement_meta.append(_default_meta(
                        len(self.measurements)-1, start, end, source='manual'))
                self.refresh()
            else:
                self.drag = None
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.calibrating, self.adding, self.drag = False, False, None
            self.refresh()
            return
        super().keyPressEvent(event)


class TrainingDialog(QDialog):
    def __init__(self, checkpoint, parent):
        super().__init__(parent)
        self.setWindowTitle('Train U-Net')
        form = QFormLayout(self)
        labels = ROOT/'data/Indentation_Image_Labels/per_image'
        if not labels.is_dir():
            labels = ROOT/'data/Indentation_Image_Labels/Labels.json'
        self.labels = self.path_row(form, 'Datumaro JSON or folder', labels, 'json')
        self.images = self.path_row(form, 'Training image folder', ROOT/'data/Indentation Images', True)
        self.output = self.path_row(form, 'Save checkpoint', checkpoint, False)
        self.epochs = QSpinBox(); self.epochs.setRange(1, 1000); self.epochs.setValue(50)
        self.size = QSpinBox(); self.size.setRange(128, 2048); self.size.setSingleStep(64); self.size.setValue(512)
        form.addRow('Epochs', self.epochs)
        form.addRow('Training resolution', self.size)
        note = QLabel('Browse shows the JSON files. Choosing one uses every JSON in that folder.\n'
                      'Crack polylines become masks; indentation boxes locate the center.\n'
                      '20% of images are held out. Best validation checkpoint is saved.\n'
                      'Start at 512; higher resolutions preserve finer cracks but use more memory.')
        note.setWordWrap(True); form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def path_row(self, form, label, default, directory):
        row = QWidget(); layout = QHBoxLayout(row); layout.setContentsMargins(0, 0, 0, 0)
        field = QLineEdit(str(default)); button = QPushButton('Browse')
        def browse():
            start = field.text()
            if directory == 'json':
                if start and not Path(start).is_dir():
                    start = str(Path(start).parent)
                path, _ = QFileDialog.getOpenFileName(
                    self, 'Select a JSON file. Training uses every JSON in its folder.',
                    start, 'JSON files (*.json)')
                if path:
                    folder = Path(path).parent
                    field.setText(str(folder if len(list(folder.glob('*.json'))) > 1 else path))
                return
            if directory:
                path = QFileDialog.getExistingDirectory(self, label, start)
            else:
                path, _ = QFileDialog.getSaveFileName(self, label, start, 'PyTorch (*.pt)')
            if path:
                field.setText(path)
        button.clicked.connect(browse)
        layout.addWidget(field); layout.addWidget(button); form.addRow(label, row)
        return field


def _suggested_pairs(probabilities, threshold=.5):
    """Convert model output into editable line pairs, omitting unresolved cracks."""
    _center, found = estimate_indentation_measurements(probabilities, threshold)
    if not found:
        raise ValueError('No crack could be resolved. Lower the threshold or train the model longer.')
    return [[item['start'], item['end']] for item in found]


def _suggested_bundle(probabilities, threshold=.5):
    center, found = estimate_indentation_measurements(probabilities, threshold)
    pairs = [[np.asarray(item['start'], float), np.asarray(item['end'], float)] for item in found]
    meta = [{
        'role': item.get('role', 'crack_chord'),
        'label': item.get('label', f'Line {index + 1}'),
        'source': item.get('source', 'estimated'),
        'confidence': item.get('confidence'),
        'status': 'Estimated',
    } for index, item in enumerate(found)]
    return center, pairs, meta


class CrackMeasurementWidget(QWidget):
    """Embeddable crack-measurement panel for the standalone window or main-app tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        self.checkpoint = default_checkpoint()
        self.measurement_checkpoint = None
        self.measurement_threshold = None
        self.scale_method = None
        self.job = None
        self.estimate_accuracy = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        primary = QHBoxLayout()
        secondary = QHBoxLayout()
        layout.addLayout(primary)
        layout.addLayout(secondary)
        self.actions = []

        for label, callback in [
                ('Open image...', self.load),
                ('Set scale', self.set_scale)]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            primary.addWidget(button)
            self.actions.append(button)

        self.scale_label = QLabel('Scale: 10 µm / 100 px')
        primary.addWidget(self.scale_label)
        primary.addStretch(1)

        self.zoom_out = QPushButton('−')
        self.zoom_out.setFixedWidth(34)
        self.zoom_out.clicked.connect(lambda: self.view.set_zoom_factor(1/1.2))
        self.zoom_label = QLabel('100%')
        self.zoom_label.setMinimumWidth(48)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_in = QPushButton('+')
        self.zoom_in.setFixedWidth(34)
        self.zoom_in.clicked.connect(lambda: self.view.set_zoom_factor(1.2))
        self.fit_button = QPushButton('Fit')
        self.fit_button.clicked.connect(lambda: self.view.fit())
        for widget in (self.zoom_out, self.zoom_label, self.zoom_in, self.fit_button):
            primary.addWidget(widget)
        self.actions.extend([self.zoom_out, self.zoom_in, self.fit_button])

        for label, callback in [
                ('Train U-Net on JSONs', self.training),
                ('Load trained model', self.load_model),
                ('Generate estimated crack lengths', self.generate),
                ('Add crack line', self.add_crack_line),
                ('Export measurements JSON', self.export_measurements)]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            secondary.addWidget(button)
            self.actions.append(button)

        self.cancel = QPushButton('Cancel training')
        self.cancel.setEnabled(False)
        self.cancel.clicked.connect(lambda: self.job.requestInterruption() if self.job else None)
        secondary.addWidget(self.cancel)
        secondary.addWidget(QLabel('Threshold'))
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(.05, .95)
        self.threshold.setSingleStep(.05)
        self.threshold.setValue(.5)
        secondary.addWidget(self.threshold)
        secondary.addStretch(1)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        self.view = ImageView()
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.view)

        side = QFrame()
        side.setMinimumWidth(320)
        side.setMaximumWidth(460)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(8, 0, 0, 0)
        side_layout.setSpacing(10)

        self.info_box = QLabel()
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet(
            'QLabel { background:#243447; border:1px solid #3d5875; border-radius:6px; padding:10px; }')
        side_layout.addWidget(self.info_box)

        self.accuracy_box = QLabel()
        self.accuracy_box.setWordWrap(True)
        self.accuracy_box.setStyleSheet(
            'QLabel { background:#1f3328; border:1px solid #3f6b4f; border-radius:6px; padding:10px; }')
        side_layout.addWidget(self.accuracy_box)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['#', 'Line', 'Length', 'Estimate'])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        side_layout.addWidget(self.table, 1)
        splitter.addWidget(side)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 2)

        self.status_label = QLabel('Open an indentation image to begin.')
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet('QLabel { color:#aeb8c2; padding:2px 4px; }')
        layout.addWidget(self.status_label)

        self.view.calibration.connect(self.calibrate)
        self.view.changed.connect(self.update_summary)
        self.view.zoom_changed.connect(self.update_zoom)
        self.update_summary()
        self.show_status('Open an indentation image to begin.')

    def show_status(self, message):
        if getattr(self, 'status_label', None) is not None:
            self.status_label.setText(message)
        window = self.window()
        if isinstance(window, QMainWindow) and window.statusBar() is not None:
            window.statusBar().showMessage(message)

    def update_zoom(self, factor):
        self.zoom_label.setText(f'{round(factor * 100)}%')

    def update_summary(self):
        self.view._sync_meta()
        scale_text = (f'Scale: {self.view.scale_um * 100:.4g} µm / 100 px'
                      if self.view.scale_set else 'Scale: 10 µm / 100 px (default)')
        self.scale_label.setText(scale_text)

        rows = len(self.view.measurements)
        self.table.setRowCount(rows)
        lengths_um = []
        confidences = []
        for index, (start, end) in enumerate(self.view.measurements):
            meta = self.view.measurement_meta[index]
            length_um = float(np.linalg.norm(end - start) * self.view.scale_um)
            lengths_um.append(length_um)
            if meta.get('confidence') is not None:
                confidences.append(float(meta['confidence']))
            values = [
                str(index + 1),
                meta.get('label', f'Line {index + 1}'),
                f'{length_um:.2f} µm',
                meta.get('status', 'Estimated'),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (0, 2):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(index, column, item)

        if self.view.image is None:
            self.info_box.setText(
                'Open an indentation image, set scale, then generate estimates.\n'
                'Inner diagonals are the indentation half-diagonals (1–4 style).\n'
                'Outer cracks are the radial crack lengths.\n'
                'Drag handles to adjust. Zoom does not change measured lengths.')
        else:
            longest = max(lengths_um) if lengths_um else 0
            total = sum(lengths_um) if lengths_um else 0
            self.info_box.setText(
                'Inner diagonals = indentation half-diagonals. Outer cracks = radial crack lengths.\n'
                'Cyan dots = inner/shared end. Red dots = outer tips. Drag tips or lines to adjust.\n'
                f'Measurements: {rows}   Longest: {longest:.2f} µm   Total: {total:.2f} µm\n'
                'Zoom does not change measured lengths. Export only after review.')

        if confidences:
            accuracy = 100 * float(np.mean(confidences))
            self.estimate_accuracy = accuracy
            self.accuracy_box.setText(
                f'<b>Estimate accuracy: {accuracy:.1f}%</b><br>'
                'Average model-mask confidence along the suggested lines.<br>'
                'This is not researcher-validated ground-truth accuracy.')
        elif rows:
            self.estimate_accuracy = None
            self.accuracy_box.setText(
                '<b>Estimate accuracy: n/a</b><br>'
                'Manual or adjusted lines have no model confidence score yet.')
        else:
            self.estimate_accuracy = None
            self.accuracy_box.setText(
                '<b>Estimate accuracy: —</b><br>'
                'Generate estimates to see model confidence for the suggested lines.')

        if self.view.image is not None:
            height, width = self.view.image.shape
            name = self.view.image_path.name if self.view.image_path else 'image'
            scale_note = (f'scale {self.view.scale_um:.6f} µm/px'
                          if self.view.scale_set else 'default scale is 10 µm per 100 px')
            self.show_status(f'Loaded {name} · {width} × {height} px · {scale_note}')

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open image...', str(ROOT/'data/Indentation Images'),
                                             'Images (*.bmp *.png *.jpg *.jpeg *.tif *.tiff)')
        if path:
            try:
                self.view.load(path)
                self.measurement_checkpoint = None
                self.measurement_threshold = None
                self.scale_method = None
                self.estimate_accuracy = None
                self.show_status('Image loaded. Use Set scale before generating crack estimates.')
            except Exception as exc:
                self.error(str(exc))

    def set_scale(self):
        if self.view.image is None:
            return self.error('Load an image first.')
        height, width = self.view.image.shape
        dialog = QDialog(self)
        dialog.setWindowTitle('Set scale')
        form = QFormLayout(dialog)

        draw_option = QRadioButton('Draw a known length (original)')
        fov_option = QRadioButton('Enter field of view (FOV)')
        draw_option.setChecked(True)
        form.addRow(draw_option)
        form.addRow(fov_option)

        fov_width = QDoubleSpinBox()
        fov_height = QDoubleSpinBox()
        for box in (fov_width, fov_height):
            box.setRange(0, 1e6)
            box.setDecimals(4)
            box.setSingleStep(.1)
            box.setEnabled(False)
        form.addRow('FOV width (µm)', fov_width)
        form.addRow('FOV height (µm)', fov_height)

        def update_fov_fields():
            enabled = fov_option.isChecked()
            fov_width.setEnabled(enabled)
            fov_height.setEnabled(enabled)
        fov_option.toggled.connect(update_fov_fields)

        note = QLabel(f'Image size is {width} × {height} pixels. For FOV, enter the values printed on '
                      'the image, for example 17.1 × 12.8 µm. Either FOV value can be left at 0.')
        note.setWordWrap(True)
        form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec_() != QDialog.Accepted:
            return

        if draw_option.isChecked():
            self.view.adding = False
            self.view.calibrating = True
            self.view.setFocus()
            self.show_status(
                'Click and drag along a known distance, then enter its length in micrometers.')
            return

        try:
            self.view.scale_um = scale_from_fov(width, height, fov_width.value(), fov_height.value())
        except ValueError as exc:
            return self.error(str(exc))
        self.view.scale_set = True
        self.scale_method = 'fov'
        self.view.refresh()
        self.show_status(
            f'Scale set from FOV: {self.view.scale_um:.6f} µm/pixel '
            f'({width}×{height} px, FOV {fov_width.value():g}×{fov_height.value():g} µm).')

    def calibrate(self, pixels):
        micrometers, ok = QInputDialog.getDouble(self, 'Calibrate scale',
            f'Drawn line: {pixels:.2f} original pixels. Known length (µm):', 100, .000001, 1e9, 6)
        if ok:
            self.view.scale_um = micrometers/pixels
            self.view.scale_set = True
            self.scale_method = 'drawn_line'
            self.view.refresh()
            self.show_status(
                f'Scale set by drawn line: {self.view.scale_um:.6f} µm/pixel for this image.')

    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Load trained model (U-Net or ResNet encoder)',
            str(self.checkpoint.parent), 'PyTorch (*.pt)')
        if path:
            self.checkpoint = Path(path)
            try:
                saved = torch.load(path, map_location='cpu', weights_only=True)
                architecture = saved.get('architecture', 'unet')
                note = {
                    'unet': 'scratch U-Net',
                    'encoder_seg': 'pretrained ResNet-18 encoder',
                    'micronet_unet': 'NASA MicroNet ResNet-50',
                }.get(architecture, architecture)
                self.show_status(f'Checkpoint selected ({note}): {path}')
            except Exception:
                self.show_status(f'Checkpoint selected: {path}')

    def start_job(self, function, callback, cancellable=False):
        self.job = Job(function)
        for button in self.actions:
            button.setEnabled(False)
        self.threshold.setEnabled(False)
        self.cancel.setEnabled(cancellable)
        self.job.progress.connect(self.show_status)
        self.job.result.connect(callback)
        self.job.error.connect(self.error)
        self.job.finished.connect(self.job_finished)
        self.job.start()

    def job_finished(self):
        self.job.deleteLater()
        self.job = None
        for button in self.actions:
            button.setEnabled(True)
        self.threshold.setEnabled(True)
        self.cancel.setEnabled(False)

    def training(self):
        dialog = TrainingDialog(training_checkpoint(), self)
        if dialog.exec_() != QDialog.Accepted:
            return
        output = Path(dialog.output.text())
        if output.exists() and QMessageBox.question(self, 'Replace checkpoint?',
                f'Replace {output}?', QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        args = (dialog.labels.text(), dialog.images.text(), output, dialog.epochs.value(), dialog.size.value())
        self.show_status('Training U-Net…')
        def done(path):
            if path:
                self.checkpoint = Path(path)
                self.show_status(f'Training complete. Best checkpoint: {path}')
            else:
                self.show_status('Training cancelled. Any completed best checkpoint remains on disk.')
        self.start_job(lambda job: train(*args, job.progress.emit, job.isInterruptionRequested), done, True)

    def generate(self):
        if self.view.image is None:
            return self.error('Load an image first.')
        if not self.view.scale_set:
            return self.error('Set scale for this image before generating crack estimates. Click Set scale and calibrate a known distance.')
        if not self.checkpoint.is_file():
            return self.error('Train U-Net or load a trained checkpoint first.')
        image = self.view.image.copy()
        threshold = self.threshold.value()
        self.measurement_checkpoint = self.checkpoint
        self.measurement_threshold = threshold
        self.show_status('Estimating cracks…')
        def done(bundle):
            center, measurements, meta = bundle
            self.view.center = None if center is None else np.asarray(center, float)
            self.view.measurements = [[np.asarray(a, float), np.asarray(b, float)] for a, b in measurements]
            self.view.measurement_meta = meta
            self.view.refresh()
            self.show_status(
                f'{len(measurements)} measurement(s) generated. Missing directions were not forced. '
                'Drag red tips or colored lines to adjust.')
        self.start_job(lambda job: _suggested_bundle(predict(image, self.checkpoint), threshold), done)

    def add_crack_line(self):
        if self.view.image is None:
            return self.error('Load an image first.')
        self.view.calibrating = False
        self.view.adding = True
        self.view.setFocus()
        self.show_status(
            'Click at the start of the missed crack, drag to its tip, then release. Press Esc to cancel.')

    def export_measurements(self):
        if self.view.image is None:
            return self.error('Load an image first.')
        if not self.view.measurements:
            return self.error('Generate and adjust crack measurements before exporting.')
        if not self.view.scale_set:
            return self.error('Set scale for this image before exporting measurements.')
        confirmed = QMessageBox.question(
            self, 'Export reviewed measurements',
            'Export the lines now shown as reviewed measurements for future training?\n\n'
            'Only export after you have moved, rotated, or corrected the generated lines.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirmed != QMessageBox.Yes:
            self.show_status('Export cancelled. Measurements were not marked as reviewed.')
            return

        image_path = self.view.image_path
        default_name = f'{image_path.stem}_measurements.json' if image_path else 'measurements.json'
        default_dir = reviewed_measurements_dir()
        default_dir.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(
            self, 'Export measurements JSON', str(default_dir/default_name), 'JSON files (*.json)')
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != '.json':
            destination = destination.with_suffix('.json')

        height, width = self.view.image.shape
        self.view._sync_meta()
        measurements = []
        for index, (start, end) in enumerate(self.view.measurements):
            meta = self.view.measurement_meta[index]
            measurements.append({
                'id': index,
                'role': meta.get('role', 'crack_chord'),
                'label': meta.get('label'),
                'start_xy': [float(start[0]), float(start[1])],
                'end_xy': [float(end[0]), float(end[1])],
                'deleted': False,
                'suitable': True,
                'confidence': meta.get('confidence'),
                'status': meta.get('status'),
            })
        checkpoint = self.measurement_checkpoint or self.checkpoint
        record = correction_record(
            image_path or 'indentation_image',
            measurements,
            calibration_um_per_100_px=self.view.scale_um * 100,
            source_checkpoint=checkpoint,
            scale_um_per_pixel=self.view.scale_um,
            image_path=image_path,
            image_size=(width, height),
            scale_method=self.scale_method,
            details={
                'measurement_source': 'crack_measurement_app',
                'generation_threshold': self.measurement_threshold,
                'estimate_accuracy_percent': self.estimate_accuracy,
            })
        try:
            save_correction(destination, record)
        except (OSError, ValueError) as exc:
            return self.error(f'Could not export measurements: {exc}')
        self.show_status(f'Measurements exported for future training: {destination}')
        QMessageBox.information(self, 'Export complete', f'Measurements saved to:\n{destination}')

    def error(self, message):
        self.show_status(message)
        QMessageBox.warning(self, 'Crack measurement', message)

    def closeEvent(self, event):
        if self.job is not None and self.job.isRunning():
            self.job.requestInterruption()
            self.show_status('Stopping work. Close the window after the current step finishes.')
            event.ignore()
        else:
            event.accept()



class Window(QMainWindow):
    """Standalone desktop window wrapping CrackMeasurementWidget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Indentation Crack Measurement — Qt')
        self.resize(1400, 900)
        self.panel = CrackMeasurementWidget()
        self.setCentralWidget(self.panel)

    def __getattr__(self, name):
        return getattr(self.panel, name)

    def closeEvent(self, event):
        self.panel.closeEvent(event)


def main():
    app = QApplication.instance() or QApplication([])
    window = Window()
    window.show()
    return app.exec_()
