# Load images and generate calculated indentation and cracks, allowing
# user to manipulate as needed
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from PIL import Image, ImageOps
from PyQt5.QtCore import QPoint, QPointF, QRectF, QRunnable, Qt, QThreadPool, pyqtSignal, QObject
from PyQt5.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QImage, QPainter,
                        QPen, QPixmap, QPolygonF)
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGraphicsEllipseItem,
                             QGraphicsItem, QGraphicsLineItem, QGraphicsScene,
                             QGraphicsView, QHBoxLayout, QInputDialog, QLabel,
                             QMainWindow, QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)


Point = tuple[float, float]
DIRECTIONS = ("top", "right", "bottom", "left")
INNER_NUMBERS = {"top": 1, "right": 2, "bottom": 3, "left": 4}
CRACK_NUMBERS = {"top": 5, "right": 6, "bottom": 7, "left": 8}
DEFAULT_UM_PER_PIXEL = 10.0 / 100.0
ANALYSIS_MAX_DIMENSION = 1500


@dataclass
class Estimate:
    center: Point
    corners: dict[str, Point]
    crack_ends: dict[str, Point]
    corner_confidence: dict[str, float]
    crack_confidence: dict[str, float]
    focus_score: float
    center_confident: bool


@dataclass
class LineDefinition:
    number: int
    name: str
    start_key: str
    end_key: str
    kind: str
    direction: str


def _point_segment_distance(point: np.ndarray, start: np.ndarray,
                            end: np.ndarray) -> float:
    segment = end - start
    denominator = float(np.dot(segment, segment))
    if denominator <= 1e-12:
        return float(np.linalg.norm(point - start))
    amount = float(np.dot(point - start, segment) / denominator)
    amount = min(1.0, max(0.0, amount))
    return float(np.linalg.norm(point - (start + amount * segment)))


def _line_intersection(first: tuple[np.ndarray, np.ndarray, np.ndarray, float],
                       second: tuple[np.ndarray, np.ndarray, np.ndarray, float]
                       ) -> Optional[np.ndarray]:
    matrix = np.column_stack((first[2], -second[2]))
    if abs(float(np.linalg.det(matrix))) < 0.2:
        return None
    try:
        amount, _ = np.linalg.solve(matrix, second[0] - first[0])
    except np.linalg.LinAlgError:
        return None
    return first[0] + amount * first[2]


def _estimate_center(segments: list[tuple[np.ndarray, np.ndarray, np.ndarray, float]],
                     width: int, height: int) -> tuple[np.ndarray, bool]:
    expected = np.array([width * 0.5, height * 0.5], dtype=np.float64)
    central_radius = min(width, height) * 0.34
    nearby = []
    for segment in segments:
        p0, p1, direction, length = segment
        angle = math.degrees(math.atan2(direction[1], direction[0])) % 90.0
        midpoint = (p0 + p1) * 0.5
        if length >= 16.0 and min(angle, 90.0 - angle) <= 28.0 \
                and float(np.linalg.norm(midpoint - expected)) <= central_radius:
            nearby.append(segment)

    candidates: list[tuple[float, np.ndarray]] = []
    limit_x, limit_y = width * 0.12, height * 0.12
    for index, first in enumerate(nearby):
        for second in nearby[index + 1:]:
            if abs(float(np.dot(first[2], second[2]))) > 0.45:
                continue
            intersection = _line_intersection(first, second)
            if intersection is None:
                continue
            offset = intersection - expected
            if abs(float(offset[0])) > limit_x or abs(float(offset[1])) > limit_y:
                continue
            d1 = _point_segment_distance(intersection, first[0], first[1])
            d2 = _point_segment_distance(intersection, second[0], second[1])
            if max(d1, d2) > min(width, height) * 0.16:
                continue
            support = math.sqrt(min(first[3], 220.0) * min(second[3], 220.0))
            score = (support * math.exp(-float(np.linalg.norm(offset)) / 130.0)
                     * math.exp(-(d1 + d2) / 150.0))
            candidates.append((score, intersection))

    if not candidates:
        return expected, False
    best_score, best_point = max(candidates, key=lambda item: item[0])
    cluster = [(score, point) for score, point in candidates
               if float(np.linalg.norm(point - best_point)) <= 14.0]
    weights = np.array([score * math.exp(-float(np.linalg.norm(point - best_point)) / 12.0)
                        for score, point in cluster], dtype=np.float64)
    locations = np.array([point for _score, point in cluster], dtype=np.float64)
    center = np.average(locations, axis=0, weights=weights)
    return center, best_score >= 10.0

# creates conventional shi-tomasi corner response map
def _corner_map(gray: np.ndarray) -> np.ndarray:
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    smooth = cv2.GaussianBlur(enhanced, (3, 3), 0.8)
    response = cv2.cornerMinEigenVal(smooth, blockSize=5, ksize=3)
    response = cv2.dilate(response, np.ones((3, 3), dtype=np.uint8))
    response = cv2.GaussianBlur(response, (0, 0), 1.1)
    positive = response[response > 0]
    scale = float(np.percentile(positive, 99.5)) if positive.size else 0.0
    if scale > 1e-12:
        response = np.clip(response / scale, 0.0, 1.0)
    return response.astype(np.float32)


def _best_corner_layout(center: np.ndarray, response: np.ndarray,
                        width: int, height: int
                        ) -> tuple[float, float, dict[str, tuple[np.ndarray, float]]]:
    def sample(x: float, y: float) -> float:
        ix, iy = int(round(x)), int(round(y))
        if ix < 3 or iy < 3 or ix >= width - 3 or iy >= height - 3:
            return 0.0
        return float(np.max(response[iy - 2:iy + 3, ix - 2:ix + 3]))

    best = (-1.0, 0.0, 34.0)
    for angle in np.arange(-20.0, 20.01, 2.0):
        for radius in np.arange(12.0, 82.01, 2.0):
            score = 0.0
            valid = True
            for offset in (-90.0, 0.0, 90.0, 180.0):
                theta = math.radians(angle + offset)
                point = center + radius * np.array([math.cos(theta), math.sin(theta)])
                if not (3 <= point[0] < width - 3 and 3 <= point[1] < height - 3):
                    valid = False
                    break
                score += sample(float(point[0]), float(point[1]))
            if valid and score > best[0]:
                best = (score, float(angle), float(radius))

    coarse_score, coarse_angle, coarse_radius = best
    refined = best
    for angle in np.arange(coarse_angle - 2.1, coarse_angle + 2.01, 0.35):
        for radius in np.arange(max(10.0, coarse_radius - 4.1),
                                min(90.0, coarse_radius + 4.01), 0.75):
            score = 0.0
            valid = True
            for offset in (-90.0, 0.0, 90.0, 180.0):
                theta = math.radians(angle + offset)
                point = center + radius * np.array([math.cos(theta), math.sin(theta)])
                if not (3 <= point[0] < width - 3 and 3 <= point[1] < height - 3):
                    valid = False
                    break
                score += sample(float(point[0]), float(point[1]))
            if valid and score > refined[0]:
                refined = (score, float(angle), float(radius))

    _score, angle, radius = refined
    directions = {
        "top": angle - 90.0,
        "right": angle,
        "bottom": angle + 90.0,
        "left": angle + 180.0,
    }
    points: dict[str, tuple[np.ndarray, float]] = {}
    for name, degrees in directions.items():
        theta = math.radians(degrees)
        point = center + radius * np.array([math.cos(theta), math.sin(theta)])
        confidence = sample(float(point[0]), float(point[1]))
        points[name] = (point, confidence)
    return angle, radius, points


def _refine_outline_corner(
    expected: np.ndarray,
    radial_direction: np.ndarray,
    segments: list[tuple[np.ndarray, np.ndarray, np.ndarray, float]],
    radius: float,
) -> tuple[np.ndarray, bool]:
    radial_angle = math.degrees(math.atan2(radial_direction[1], radial_direction[0]))
    side_angles = (radial_angle - 45.0, radial_angle + 45.0)

    def axial_distance(first: float, second: float) -> float:
        return abs((first - second + 90.0) % 180.0 - 90.0)

    search_radius = max(22.0, radius * 0.9)
    local = [segment for segment in segments
             if (min(segment[0][0], segment[1][0]) <= expected[0] + search_radius
                 and max(segment[0][0], segment[1][0]) >= expected[0] - search_radius
                 and min(segment[0][1], segment[1][1]) <= expected[1] + search_radius
                 and max(segment[0][1], segment[1][1]) >= expected[1] - search_radius)]

    candidates: list[tuple[float, np.ndarray]] = []
    for index, first in enumerate(local):
        first_angle = math.degrees(math.atan2(first[2][1], first[2][0]))
        first_side = min(range(2), key=lambda side: axial_distance(
            first_angle, side_angles[side]))
        first_error = axial_distance(first_angle, side_angles[first_side])
        if first_error > 30.0 or first[3] < 5.0:
            continue
        for second in local[index + 1:]:
            second_angle = math.degrees(math.atan2(second[2][1], second[2][0]))
            second_side = min(range(2), key=lambda side: axial_distance(
                second_angle, side_angles[side]))
            second_error = axial_distance(second_angle, side_angles[second_side])
            if second_side == first_side or second_error > 30.0 or second[3] < 5.0:
                continue
            intersection = _line_intersection(first, second)
            if intersection is None:
                continue
            distance = float(np.linalg.norm(intersection - expected))
            if distance > max(20.0, radius * 0.75):
                continue
            first_t = float(np.dot(intersection - first[0], first[2]))
            second_t = float(np.dot(intersection - second[0], second[2]))
            first_extension = max(0.0, -first_t, first_t - first[3])
            second_extension = max(0.0, -second_t, second_t - second[3])
            extension_limit = max(20.0, radius * 0.7)
            if first_extension > extension_limit or second_extension > extension_limit:
                continue
            score = (distance + 0.35 * (first_error + second_error)
                     + 0.20 * (first_extension + second_extension)
                     - 0.012 * min(first[3], second[3]))
            candidates.append((score, intersection))

    if not candidates:
        return expected, False
    return min(candidates, key=lambda candidate: candidate[0])[1], True


def _outer_diamond_center(corners: dict[str, np.ndarray]) -> Optional[np.ndarray]:
    top = corners["top"]
    bottom = corners["bottom"]
    left = corners["left"]
    right = corners["right"]
    first = bottom - top
    second = right - left
    denominator = float(first[0] * second[1] - first[1] * second[0])
    if abs(denominator) < 1e-8:
        return None
    delta = left - top
    amount = float((delta[0] * second[1] - delta[1] * second[0]) / denominator)
    return top + amount * first


def _boundary_distance(point: np.ndarray, direction: np.ndarray,
                       width: int, height: int) -> float:
    values = []
    if direction[0] > 1e-9:
        values.append((width - 1.0 - point[0]) / direction[0])
    elif direction[0] < -1e-9:
        values.append((0.0 - point[0]) / direction[0])
    if direction[1] > 1e-9:
        values.append((height - 1.0 - point[1]) / direction[1])
    elif direction[1] < -1e-9:
        values.append((0.0 - point[1]) / direction[1])
    nonnegative = [value for value in values if value >= 0.0]
    return max(0.0, min(nonnegative)) if nonnegative else 0.0


def _estimate_crack_end(corner: np.ndarray, direction: np.ndarray,
                        segments: list[tuple[np.ndarray, np.ndarray, np.ndarray, float]],
                        width: int, height: int, radius: float
                        ) -> tuple[np.ndarray, float]:
    edge_distance = _boundary_distance(corner, direction, width, height)
    if edge_distance <= 1.0:
        return corner + direction * edge_distance, 0.0
    tolerance = max(12.0, min(24.0, radius * 0.42))
    candidates = []
    for p0, p1, line_direction, length in segments:
        alignment = abs(float(np.dot(line_direction, direction)))
        if alignment < math.cos(math.radians(24.0)):
            continue
        projections = [float(np.dot(point - corner, direction)) for point in (p0, p1)]
        perpendiculars = [float(np.linalg.norm((point - corner) - along * direction))
                          for point, along in zip((p0, p1), projections)]
        along_start, along_end = min(projections), max(projections)
        close_distance = min(perpendiculars)
        if close_distance > tolerance or along_start > max(38.0, radius * 0.8) \
                or along_end < 12.0:
            continue
        if along_start > edge_distance + 1.0:
            continue
        score = (min(length, 220.0) * alignment
                 * math.exp(-close_distance / max(5.0, tolerance * 0.65))
                 * math.exp(-max(along_start, 0.0) / max(30.0, radius)))
        candidates.append((along_start, along_end, score, close_distance, alignment))

    if not candidates:
        default_length = min(edge_distance, max(65.0, radius * 3.0))
        return corner + direction * default_length, 0.0

    ordered = sorted(candidates, key=lambda item: (item[0], -item[2]))
    seed_limit = max(35.0, radius * 0.7)
    seed_indices = [index for index, item in enumerate(ordered)
                    if item[0] <= seed_limit and item[1] >= 10.0]
    if not seed_indices:
        seed_indices = [max(range(len(ordered)), key=lambda index: ordered[index][2])]

    # Crack edges are often fragmented by debris and uneven contrast. Grow a
    # chain from each plausible near-corner segment, permitting wider gaps and
    # selecting the continuation that reaches furthest along the same corridor.
    max_gap = max(28.0, min(100.0, radius * 0.85))
    traced_paths = []
    for seed_index in seed_indices:
        seed = ordered[seed_index]
        chain_start, chain_end = seed[0], seed[1]
        used = {seed_index}
        total_gap = 0.0
        distances = [seed[3]]
        alignments = [seed[4]]
        while True:
            adjacent = [(index, candidate) for index, candidate in enumerate(ordered)
                        if index not in used
                        and candidate[0] <= chain_end + max_gap
                        and candidate[1] > chain_end + 2.0]
            if not adjacent:
                break
            following_index, following = max(
                adjacent,
                key=lambda pair: (pair[1][1]
                                  - 0.35 * max(pair[1][0] - chain_end, 0.0)
                                  + 0.15 * min(pair[1][2], 35.0)
                                  - 0.5 * pair[1][3]),
            )
            total_gap += max(0.0, following[0] - chain_end)
            used.add(following_index)
            chain_start = min(chain_start, following[0])
            chain_end = max(chain_end, following[1])
            distances.append(following[3])
            alignments.append(following[4])

        observed_length = max(0.0, chain_end - max(chain_start, 0.0))
        chain_distance = float(np.mean(distances))
        chain_alignment = float(np.mean(alignments))
        confidence = (min(1.0, observed_length / 70.0)
                      * math.exp(-chain_distance / max(7.0, tolerance))
                      * max(0.0, (chain_alignment - 0.75) / 0.25)
                      * math.exp(-total_gap / max(100.0, radius * 2.0)))
        path_score = chain_end - total_gap * 0.12 + confidence * 8.0
        traced_paths.append((path_score, chain_start, chain_end,
                             chain_distance, chain_alignment, confidence))

    _path_score, chain_start, chain_end, chain_distance, chain_alignment, confidence = max(
        traced_paths, key=lambda path: path[0])

    reaches_edge = edge_distance - chain_end <= max(12.0, edge_distance * 0.03)
    endpoint_distance = edge_distance if reaches_edge else min(chain_end, edge_distance)
    return corner + direction * endpoint_distance, float(np.clip(confidence, 0.0, 1.0))

#estimate indentation centers, corners, and crack endpoints
def estimate_indentation(rgb: np.ndarray) -> Estimate:
    original_height, original_width = rgb.shape[:2]
    resize_factor = min(1.0, ANALYSIS_MAX_DIMENSION / max(original_width, original_height))
    width = max(1, int(round(original_width * resize_factor)))
    height = max(1, int(round(original_height * resize_factor)))
    work_rgb = (cv2.resize(rgb, (width, height), interpolation=cv2.INTER_AREA)
                if (width, height) != (original_width, original_height) else rgb)
    gray = cv2.cvtColor(work_rgb, cv2.COLOR_RGB2GRAY)
    smooth = cv2.GaussianBlur(gray, (0, 0), 1.1)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(smooth)
    detector = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    found = detector.detect(enhanced)[0]
    segments = []
    if found is not None:
        for raw in found.reshape(-1, 4):
            p0 = np.array(raw[:2], dtype=np.float64)
            p1 = np.array(raw[2:], dtype=np.float64)
            delta = p1 - p0
            length = float(np.linalg.norm(delta))
            if length >= 9.0:
                segments.append((p0, p1, delta / length, length))

    # Crack axes provide only a search seed. The final shared center comes
    # from the outer indentation corners and their two diagonal intersection.
    center_seed, axis_seed_confident = _estimate_center(segments, width, height)
    response = _corner_map(gray)
    _angle, radius, corner_estimates = _best_corner_layout(
        center_seed, response, width, height)

    corner_arrays: dict[str, np.ndarray] = {}
    outline_refined: dict[str, bool] = {}
    corner_response_scores: dict[str, float] = {}
    for direction_name in DIRECTIONS:
        proposed, response_score = corner_estimates[direction_name]
        radial = proposed - center_seed
        radial_length = float(np.linalg.norm(radial))
        radial = radial / radial_length if radial_length > 0 else np.array([0.0, -1.0])
        refined, found_outline = _refine_outline_corner(
            proposed, radial, segments, radius)
        corner_arrays[direction_name] = refined
        outline_refined[direction_name] = found_outline
        corner_response_scores[direction_name] = response_score

    center = _outer_diamond_center(corner_arrays)
    if center is None:
        # If the two pairs of tips do not define crossing diagonals, use their
        # average as the most stable center fallback.
        center = np.mean(np.array(list(corner_arrays.values())), axis=0)
    if not (0.0 <= center[0] < width and 0.0 <= center[1] < height):
        center = center_seed
        corner_arrays = {name: estimate[0]
                         for name, estimate in corner_estimates.items()}
        outline_refined = {name: False for name in DIRECTIONS}
    center_confident = axis_seed_confident or sum(outline_refined.values()) >= 3
    radius = float(np.mean([np.linalg.norm(corner_arrays[name] - center)
                            for name in DIRECTIONS]))

    corners: dict[str, Point] = {}
    crack_ends: dict[str, Point] = {}
    corner_confidence: dict[str, float] = {}
    crack_confidence: dict[str, float] = {}
    for direction_name in DIRECTIONS:
        corner_work = corner_arrays[direction_name]
        confidence = corner_response_scores[direction_name]
        if outline_refined[direction_name]:
            confidence = max(confidence, 0.65)
        radial = corner_work - center
        radial_length = float(np.linalg.norm(radial))
        radial = radial / radial_length if radial_length > 0 else np.array([0.0, -1.0])
        endpoint_work, crack_quality = _estimate_crack_end(
            corner_work, radial, segments, width, height, radius)
        corners[direction_name] = (float(corner_work[0] / resize_factor),
                                   float(corner_work[1] / resize_factor))
        crack_ends[direction_name] = (float(endpoint_work[0] / resize_factor),
                                      float(endpoint_work[1] / resize_factor))
        corner_confidence[direction_name] = confidence
        crack_confidence[direction_name] = crack_quality

    focus_roi = gray[max(0, int(center[1] - 100)):min(height, int(center[1] + 100)),
                     max(0, int(center[0] - 100)):min(width, int(center[0] + 100))]
    focus_score = (float(cv2.Laplacian(focus_roi, cv2.CV_32F, ksize=3).var())
                   if focus_roi.size else 0.0)
    return Estimate(
        center=(float(center[0] / resize_factor), float(center[1] / resize_factor)),
        corners=corners,
        crack_ends=crack_ends,
        corner_confidence=corner_confidence,
        crack_confidence=crack_confidence,
        focus_score=focus_score,
        center_confident=center_confident,
    )


class LoadSignals(QObject):
    finished = pyqtSignal(int, object, object)
    failed = pyqtSignal(int, str)


class ImageLoadWorker(QRunnable):
    def __init__(self, request_id: int, path: Path) -> None:
        super().__init__()
        self.request_id = request_id
        self.path = path
        self.signals = LoadSignals()

    def run(self) -> None:
        try:
            with Image.open(self.path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                rgb = np.asarray(image, dtype=np.uint8).copy()
            estimate = estimate_indentation(rgb)
            self.signals.finished.emit(self.request_id, rgb, estimate)
        except Exception as error:  # deliver worker errors to the Qt thread
            self.signals.failed.emit(self.request_id, str(error))

# handles endpoints
class PointHandle(QGraphicsEllipseItem):

    def __init__(self, key: str, point: Point, color: QColor,
                 moved: Callable[[str], None], bounds: QRectF) -> None:
        super().__init__(QRectF(-6.0, -6.0, 12.0, 12.0))
        self.key = key
        self.moved = moved
        self.bounds = bounds
        self.setPos(QPointF(*point))
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#101318"), 1.2))
        self.setZValue(30.0)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag this point. Connected measurements move together.")

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):  # noqa: N802
        if change == QGraphicsItem.ItemPositionChange:
            point = value
            x = min(max(point.x(), self.bounds.left()), self.bounds.right())
            y = min(max(point.y(), self.bounds.top()), self.bounds.bottom())
            return QPointF(x, y)
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.moved(self.key)
        return result


class LengthLabel(QGraphicsItem):

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.font = QFont()
        self.font.setPointSize(9)
        self.font.setWeight(QFont.DemiBold)
        self.metrics = QFontMetricsF(self.font)
        self.padding_x = 5.0
        self.padding_y = 3.0
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setZValue(20.0)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self._rect = self._measure()

    def _measure(self) -> QRectF:
        bounds = self.metrics.boundingRect(self.text)
        return QRectF(0.0, 0.0, bounds.width() + self.padding_x * 2.0,
                      bounds.height() + self.padding_y * 2.0)

    def set_text(self, text: str) -> None:
        if text == self.text:
            return
        self.prepareGeometryChange()
        self.text = text
        self._rect = self._measure()
        self.update()

    def boundingRect(self) -> QRectF:  # noqa: N802
        return self._rect

    def paint(self, painter: QPainter, _option, _widget=None) -> None:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#20252b"), 0.8))
        painter.setBrush(QBrush(QColor("#fff34d")))
        painter.drawRoundedRect(self._rect, 2.0, 2.0)
        painter.setPen(QColor("#101318"))
        painter.setFont(self.font)
        painter.drawText(QPointF(self.padding_x,
                                 self.padding_y + self.metrics.ascent()), self.text)


class MeasurementView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, window: "MeasurementWindow") -> None:
        super().__init__(scene)
        self.window = window
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform
                            | QPainter.TextAntialiasing)
        self.setBackgroundBrush(QColor("#20252b"))
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event) -> None:  # noqa: N802
        if self.window.calibration_active:
            event.ignore()
            return
        delta = event.angleDelta().y()
        if delta:
            self.window.zoom_at(1.2 if delta > 0 else (1.0 / 1.2), event.pos())
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self.window.calibration_active and event.button() == Qt.LeftButton:
            point = self.mapToScene(event.pos())
            self.window.begin_calibration(point)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.window.calibration_active and self.window.calibration_start is not None:
            self.window.update_calibration(self.mapToScene(event.pos()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self.window.calibration_active and event.button() == Qt.LeftButton \
                and self.window.calibration_start is not None:
            self.window.finish_calibration(self.mapToScene(event.pos()))
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.window.image_pixmap_item is not None and not self.window.user_zoomed:
            self.fit_to_image()
        self.window.schedule_label_layout()

    def fit_to_image(self) -> None:
        if self.window.image_pixmap_item is None:
            return
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.window.user_zoomed = False
        self.window.update_zoom_label()
        self.window.schedule_label_layout()


class MeasurementWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Indentation Crack Measurement — Qt")
        self.resize(1450, 900)
        self.setMinimumSize(900, 620)

        self.scene = QGraphicsScene(self)
        self.view = MeasurementView(self.scene, self)
        self.image_pixmap_item: Optional[QGraphicsItem] = None
        self.image_rgb: Optional[np.ndarray] = None
        self.image_path: Optional[Path] = None
        self.estimate: Optional[Estimate] = None
        self.points: dict[str, PointHandle] = {}
        self.line_definitions: list[LineDefinition] = []
        self.line_items: dict[int, QGraphicsLineItem] = {}
        self.label_items: dict[int, LengthLabel] = {}
        self.row_index_by_line: dict[int, int] = {}
        self.um_per_pixel = DEFAULT_UM_PER_PIXEL
        self.calibration_active = False
        self.calibration_start: Optional[Point] = None
        self.calibration_item: Optional[QGraphicsLineItem] = None
        self.user_zoomed = False
        self._layout_queued = False
        self._load_id = 0
        self._load_pool = QThreadPool(self)
        self._load_pool.setMaxThreadCount(1)
        self._active_worker: Optional[ImageLoadWorker] = None

        self.open_button = QPushButton("Open image…")
        self.open_button.clicked.connect(self.open_image)
        self.calibrate_button = QPushButton("Set scale by line…")
        self.calibrate_button.clicked.connect(self.start_calibration)
        self.zoom_out_button = QPushButton("−")
        self.zoom_out_button.setFixedWidth(34)
        self.zoom_out_button.clicked.connect(lambda: self.zoom_at(1.0 / 1.25))
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setFixedWidth(34)
        self.zoom_in_button.clicked.connect(lambda: self.zoom_at(1.25))
        self.fit_button = QPushButton("Fit")
        self.fit_button.clicked.connect(self.fit_image)
        self.zoom_label = QLabel("100%")

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.calibrate_button)
        toolbar.addSpacing(14)
        self.scale_label = QLabel(self._scale_text())
        toolbar.addWidget(self.scale_label)
        toolbar.addStretch(1)
        toolbar.addWidget(self.zoom_out_button)
        toolbar.addWidget(self.zoom_label)
        toolbar.addWidget(self.zoom_in_button)
        toolbar.addWidget(self.fit_button)

        self.measurement_table = QTableWidget(8, 4)
        self.measurement_table.setHorizontalHeaderLabels(["#", "Line", "Length", "Estimate"])
        self.measurement_table.verticalHeader().setVisible(False)
        self.measurement_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.measurement_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.measurement_table.setSelectionMode(QTableWidget.SingleSelection)
        self.measurement_table.setAlternatingRowColors(True)
        self.measurement_table.setMinimumWidth(460)
        self.measurement_table.horizontalHeader().setStretchLastSection(True)
        self.measurement_table.setColumnWidth(0, 38)
        self.measurement_table.setColumnWidth(1, 168)
        self.measurement_table.setColumnWidth(2, 112)
        self.measurement_table.itemSelectionChanged.connect(self._table_selection_changed)

        info = QLabel(
            "Inner diagonals: 1–4 · Outer cracks: 5–8\n"
            "Drag any handle to adjust it. Each indentation corner is shared by its "
            "inner diagonal and outer crack; the center is shared by all four inner diagonals.\n"
            "Mouse wheel or +/− zooms the view. Zoom does not change measured lengths."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "color: white; background-color: #414b57; padding: 4px 6px 8px 6px;"
        )

        side = QVBoxLayout()
        side.addWidget(QLabel("Measurements"))
        side.addWidget(info)
        side.addWidget(self.measurement_table, 1)
        side_widget = QWidget()
        side_widget.setLayout(side)
        side_widget.setMinimumWidth(480)

        content = QHBoxLayout()
        content.addWidget(self.view, 1)
        content.addWidget(side_widget)

        outer = QVBoxLayout()
        outer.addLayout(toolbar)
        outer.addLayout(content, 1)
        central = QWidget()
        central.setLayout(outer)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Open a microscope image to estimate the eight lines.")

    def _scale_text(self) -> str:
        return f"Scale: {self.um_per_pixel * 100.0:.4g} μm / 100 px"

    def open_image(self) -> None:
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Open microscope image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All files (*.*)",
        )
        if filename:
            self.load_image(Path(filename))

    def load_image(self, path: Path) -> None:
        self._load_id += 1
        self._pending_path = path
        worker = ImageLoadWorker(self._load_id, path)
        worker.signals.finished.connect(self._image_loaded)
        worker.signals.failed.connect(self._image_load_failed)
        self._active_worker = worker
        self.statusBar().showMessage(f"Loading and analyzing {path.name}…")
        self.open_button.setEnabled(False)
        self._load_pool.start(worker)

    def _image_loaded(self, request_id: int, rgb: np.ndarray, estimate: Estimate) -> None:
        if request_id != self._load_id:
            return
        self.open_button.setEnabled(True)
        self._active_worker = None
        self.image_rgb = rgb
        self.estimate = estimate
        self.image_path = self._pending_path
        self.um_per_pixel = DEFAULT_UM_PER_PIXEL
        self.scale_label.setText(self._scale_text())
        height, width = rgb.shape[:2]
        qimage = QImage(rgb.data, width, height, width * 3, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimage)

        self.scene.clear()
        self.calibration_active = False
        self.calibration_start = None
        self.calibration_item = None
        self.points.clear()
        self.line_items.clear()
        self.label_items.clear()
        self.image_pixmap_item = self.scene.addPixmap(pixmap)
        self.image_pixmap_item.setZValue(-100.0)
        self.scene.setSceneRect(QRectF(0.0, 0.0, float(width), float(height)))

        point_data: dict[str, Point] = {"center": estimate.center}
        for direction in DIRECTIONS:
            point_data[f"corner_{direction}"] = estimate.corners[direction]
            point_data[f"crack_{direction}"] = estimate.crack_ends[direction]
        bounds = QRectF(0.0, 0.0, float(width), float(height))
        for key, position in point_data.items():
            if key == "center":
                color = QColor("#ffffff")
            elif key.startswith("corner_"):
                color = QColor("#3ee0bb")
            else:
                color = QColor("#ff6868")
            handle = PointHandle(key, position, color, self._point_moved, bounds)
            self.scene.addItem(handle)
            self.points[key] = handle

        self._create_measurement_lines(estimate)
        self._fill_measurement_table(estimate)
        self.view.fit_to_image()
        self._update_all_lengths()
        warnings = []
        if not estimate.center_confident:
            warnings.append("center estimate is uncertain")
        weak_corners = [direction for direction, value in estimate.corner_confidence.items()
                        if value < 0.15]
        if weak_corners:
            warnings.append("some indentation corners need review")
        weak_cracks = [direction for direction, value in estimate.crack_confidence.items()
                       if value < 0.25]
        if weak_cracks:
            warnings.append("some crack endpoints need review")
        if estimate.focus_score < 35.0:
            warnings.append("image may be blurry")
        status = (f"Loaded {self.image_path.name} · {width} × {height} px · "
                  "default scale is 10 μm per 100 px")
        if warnings:
            status += " · Review: " + "; ".join(warnings)
        self.statusBar().showMessage(status)

    def _image_load_failed(self, request_id: int, error: str) -> None:
        if request_id != self._load_id:
            return
        self.open_button.setEnabled(True)
        self._active_worker = None
        self.statusBar().showMessage("Image could not be opened.")
        QMessageBox.critical(self, "Could not load image", error)

    def _create_measurement_lines(self, estimate: Estimate) -> None:
        definitions: list[LineDefinition] = []
        for direction in DIRECTIONS:
            number = INNER_NUMBERS[direction]
            definitions.append(LineDefinition(number, f"Inner {direction}", "center",
                                              f"corner_{direction}", "inner", direction))
        for direction in DIRECTIONS:
            number = CRACK_NUMBERS[direction]
            definitions.append(LineDefinition(number, f"{direction.title()} crack",
                                              f"corner_{direction}", f"crack_{direction}",
                                              "crack", direction))
        self.line_definitions = definitions
        for definition in definitions:
            start = self.points[definition.start_key].pos()
            end = self.points[definition.end_key].pos()
            color = QColor("#31d1ae") if definition.kind == "inner" else QColor("#ff6565")
            if definition.kind == "inner":
                color = QColor("#45dfc1")
            pen = QPen(color, 2.0)
            if definition.kind == "crack" and estimate.crack_confidence[definition.direction] < 0.25:
                pen.setStyle(Qt.DashLine)
            line_item = self.scene.addLine(start.x(), start.y(), end.x(), end.y(), pen)
            line_item.setZValue(5.0)
            line_item.setAcceptedMouseButtons(Qt.NoButton)
            self.line_items[definition.number] = line_item
            label = LengthLabel(f"[{definition.number}] 0.00 μm")
            self.scene.addItem(label)
            self.label_items[definition.number] = label

    def _fill_measurement_table(self, estimate: Estimate) -> None:
        self.measurement_table.blockSignals(True)
        self.row_index_by_line.clear()
        for row, definition in enumerate(sorted(self.line_definitions,
                                                key=lambda current: current.number)):
            self.row_index_by_line[definition.number] = row
            quality = (estimate.corner_confidence[definition.direction]
                       if definition.kind == "inner"
                       else estimate.crack_confidence[definition.direction])
            confidence_text = "Review" if quality < 0.25 else "Estimated"
            values = (str(definition.number), definition.name, "0.00 μm", confidence_text)
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter if column in (0, 2, 3)
                                      else Qt.AlignLeft | Qt.AlignVCenter)
                self.measurement_table.setItem(row, column, item)
        self.measurement_table.blockSignals(False)

    def _point_moved(self, _key: str) -> None:
        self._update_all_lengths()
        self.schedule_label_layout()

    def _update_all_lengths(self) -> None:
        if not self.points:
            return
        for definition in self.line_definitions:
            start = self.points[definition.start_key].pos()
            end = self.points[definition.end_key].pos()
            self.line_items[definition.number].setLine(start.x(), start.y(), end.x(), end.y())
            pixels = math.hypot(end.x() - start.x(), end.y() - start.y())
            length_um = pixels * self.um_per_pixel
            self.label_items[definition.number].set_text(
                f"[{definition.number}] {length_um:.2f} μm")
            row = self.row_index_by_line.get(definition.number)
            if row is not None and self.measurement_table.item(row, 2) is not None:
                self.measurement_table.item(row, 2).setText(f"{length_um:.2f} μm")

    def schedule_label_layout(self) -> None:
        if self._layout_queued or not self.label_items:
            return
        self._layout_queued = True
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._layout_labels)

    def _layout_labels(self) -> None:
        self._layout_queued = False
        if not self.points or self.view.viewport().width() <= 1:
            return
        viewport = self.view.viewport().rect()
        placed: list[QRectF] = []
        padding = 8.0
        ordered = sorted(self.line_definitions, key=lambda item: item.number)
        for definition in ordered:
            start_scene = self.points[definition.start_key].scenePos()
            end_scene = self.points[definition.end_key].scenePos()
            start = QPointF(self.view.mapFromScene(start_scene))
            end = QPointF(self.view.mapFromScene(end_scene))
            midpoint = (start + end) * 0.5
            direction = end - start
            length = math.hypot(direction.x(), direction.y()) or 1.0
            tangent = QPointF(direction.x() / length, direction.y() / length)
            normal = QPointF(-tangent.y(), tangent.x())
            label = self.label_items[definition.number]
            width, height = label.boundingRect().width(), label.boundingRect().height()
            candidates: list[QPointF] = []
            for normal_offset in (18.0, -18.0, 34.0, -34.0, 52.0, -52.0):
                for tangent_offset in (0.0, 30.0, -30.0, 58.0, -58.0):
                    center = midpoint + normal * normal_offset + tangent * tangent_offset
                    candidates.append(QPointF(center.x() - width / 2.0,
                                              center.y() - height / 2.0))
            # Last-resort positions stay visible even if the lines converge.
            for radius in (28.0, 48.0, 72.0, 100.0, 132.0):
                for step in range(16):
                    angle = step * math.tau / 16.0
                    center = midpoint + QPointF(math.cos(angle), math.sin(angle)) * radius
                    candidates.append(QPointF(center.x() - width / 2.0,
                                              center.y() - height / 2.0))

            best_rect = None
            best_cost = float("inf")
            for top_left in candidates:
                x = min(max(top_left.x(), padding),
                        max(padding, viewport.width() - width - padding))
                y = min(max(top_left.y(), padding),
                        max(padding, viewport.height() - height - padding))
                rect = QRectF(x, y, width, height)
                overlap = sum(rect.intersected(other).width()
                              * rect.intersected(other).height() for other in placed)
                distance = math.hypot(x + width / 2.0 - midpoint.x(),
                                      y + height / 2.0 - midpoint.y())
                cost = overlap * 1000.0 + distance
                if cost < best_cost:
                    best_cost, best_rect = cost, rect
                if overlap <= 0.0:
                    best_rect = rect
                    break
            if best_rect is None:
                continue
            placed.append(best_rect)
            scene_anchor = self.view.mapToScene(QPoint(round(best_rect.left()),
                                                       round(best_rect.top())))
            label.setPos(scene_anchor)

    def _table_selection_changed(self) -> None:
        indexes = self.measurement_table.selectedIndexes()
        if not indexes:
            return
        number_item = self.measurement_table.item(indexes[0].row(), 0)
        if number_item is None:
            return
        number = int(number_item.text())
        definition = next((line for line in self.line_definitions
                           if line.number == number), None)
        if definition:
            handle = self.points[definition.start_key]
            self.view.centerOn(handle)

    def start_calibration(self) -> None:
        if self.image_rgb is None:
            self.statusBar().showMessage("Open an image before setting its scale.")
            return
        self.calibration_active = True
        self.calibration_start = None
        self.calibrate_button.setText("Draw a known length on the image…")
        self.view.setCursor(Qt.CrossCursor)
        self.statusBar().showMessage(
            "Drag across a known distance on the image, then enter its length in micrometers.")

    def begin_calibration(self, scene_point: QPointF) -> None:
        if self.image_rgb is None:
            return
        width, height = self.image_rgb.shape[1], self.image_rgb.shape[0]
        start = QPointF(min(max(scene_point.x(), 0.0), width - 1.0),
                        min(max(scene_point.y(), 0.0), height - 1.0))
        self.calibration_start = (start.x(), start.y())
        if self.calibration_item is None:
            self.calibration_item = self.scene.addLine(
                start.x(), start.y(), start.x(), start.y(),
                QPen(QColor("#63b7ff"), 2.0, Qt.DashLine))
            self.calibration_item.setZValue(40.0)
            self.calibration_item.setAcceptedMouseButtons(Qt.NoButton)
        else:
            self.calibration_item.setLine(start.x(), start.y(), start.x(), start.y())
            self.calibration_item.show()

    def update_calibration(self, scene_point: QPointF) -> None:
        if self.calibration_start is None or self.image_rgb is None \
                or self.calibration_item is None:
            return
        width, height = self.image_rgb.shape[1], self.image_rgb.shape[0]
        x = min(max(scene_point.x(), 0.0), width - 1.0)
        y = min(max(scene_point.y(), 0.0), height - 1.0)
        self.calibration_item.setLine(self.calibration_start[0], self.calibration_start[1], x, y)

    def finish_calibration(self, scene_point: QPointF) -> None:
        if self.calibration_start is None or self.image_rgb is None:
            return
        self.update_calibration(scene_point)
        if self.calibration_item is not None:
            line = self.calibration_item.line()
            pixels = math.hypot(line.dx(), line.dy())
            self.calibration_item.hide()
        else:
            pixels = 0.0
        self.calibration_start = None
        self.calibration_active = False
        self.calibrate_button.setText("Set scale by line…")
        self.view.unsetCursor()
        if pixels < 2.0:
            self.statusBar().showMessage("Calibration line was too short; scale was unchanged.")
            return
        micrometers, accepted = QInputDialog.getDouble(
            self,
            "Set image scale",
            f"How many micrometers long is this line?\n"
            f"It measures {pixels:.2f} pixels in the original image.",
            10.0,
            0.000001,
            1_000_000_000.0,
            4,
        )
        if accepted and micrometers > 0:
            self.um_per_pixel = micrometers / pixels
            self.scale_label.setText(self._scale_text())
            self._update_all_lengths()
            self.statusBar().showMessage(
                f"Scale set to {micrometers:g} μm over {pixels:.2f} original-image pixels.")
        else:
            self.statusBar().showMessage("Scale unchanged.")
        self.schedule_label_layout()

    def zoom_at(self, factor: float, viewport_point: Optional[QPoint] = None) -> None:
        if self.image_pixmap_item is None or self.calibration_active:
            return
        current = self.view.transform().m11()
        target = min(25.0, max(0.015, current * factor))
        if abs(target - current) < 1e-9:
            return
        actual_factor = target / current
        if viewport_point is not None:
            self.view.setTransformationAnchor(QGraphicsView.NoAnchor)
            before = self.view.mapToScene(viewport_point)
            self.view.scale(actual_factor, actual_factor)
            after = self.view.mapToScene(viewport_point)
            delta = after - before
            self.view.translate(delta.x(), delta.y())
            self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        else:
            self.view.scale(actual_factor, actual_factor)
        self.user_zoomed = True
        self.update_zoom_label()
        self.schedule_label_layout()

    def update_zoom_label(self) -> None:
        if self.image_pixmap_item is None:
            self.zoom_label.setText("100%")
            return
        percent = self.view.transform().m11() * 100.0
        self.zoom_label.setText(f"{percent:.0f}%")

    def fit_image(self) -> None:
        if self.image_pixmap_item is not None:
            self.view.fit_to_image()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape and self.calibration_active:
            self.calibration_active = False
            self.calibration_start = None
            if self.calibration_item is not None:
                self.calibration_item.hide()
            self.calibrate_button.setText("Set scale by line…")
            self.view.unsetCursor()
            self.statusBar().showMessage("Scale unchanged.")
            event.accept()
            return
        super().keyPressEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Indentation Crack Measurement")
    window = MeasurementWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
