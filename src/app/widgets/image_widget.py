from PyQt5.QtWidgets import QWidget, QLabel, QRubberBand
from PyQt5.QtGui import QPixmap, QMouseEvent, QKeyEvent, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect, pyqtSignal, pyqtSlot, QPoint, QTimer
from widgets import ScaleDialog
import math

class ImageWidget(QLabel):
    crop_started = pyqtSignal()
    crop_ended = pyqtSignal()
    scale_started = pyqtSignal()
    scale_ended = pyqtSignal()

    def __init__(self, parent:QWidget = None):
        super().__init__(parent=parent)
        self._filename = None

        # Crop variables
        self._crosshairs:list[QPoint] = [None,None,None,None]
        self._linehairs:list[QPoint] = [None,None,None,None]
        self._selected_crosshair = None
        self._selected_linehair = None
        self._crop_rubberband = None
        self._crop_mode = False
        self.crop_ended.connect(self._crop_ended)
        self._crop_rect = None

        self._scale = None #Pixels per micron.
        self._scale_mode = False
        self._scale_point1 = None  # First point
        self._scale_point2 = None  # Second point
        self._selected_point = None  # Track which point is selected for moving
        self._shift_pressed = False
        self._unit = None
        self._value = None
        self._length_in_pixels = None
        self.scale_ended.connect(self._scale_ended)
        self._initUI()

    def _initUI(self):
        """
        NOTE: the pixmap holds data for the image, while the _crop_rect defines the area of that image to display.
        Since we are using only one image widget class to represent the left/right images, we need to make sure that the 
        internal state of the widget is updated correctly when switching between images by filling it with data from the
        _image_settings list in the main_view.py file.
        """
        self._pixmap = QPixmap()
        self._scaled_pixmap = None

    @property
    def filename(self) -> str:
        return self._filename
    
    @property
    def unit(self) -> str:
        return self._unit
    
    @property
    def scale_value(self) -> float:
        return self._value
    
    @property
    def length_in_pixels(self) -> float:
        return self._length_in_pixels

    @property
    def nm_per_pix(self) -> float:
        value = self._value # this is the number of microns (from the data at the bottom of the image) that the user entered
        if self._unit == 'Microns':
            value *= 1000 # convert to nanometers
        elif self._unit == 'Milimeters':
            # mm should be depreciated since SEM will never be in that scale
            raise ValueError('Unit is not supported')
        
        try:
            return value / self._length_in_pixels  # each pixel is this many nanometers
        except (TypeError, ZeroDivisionError):
            # catch all 
            return None

    def resizeEvent(self, event):
        self._resize()
        super().resizeEvent(event)

    def _resize(self):
        #Get the size of the label
        label_size = self.size()

        #Scale the pixmap to fit the label while keeping aspect ratio
        if not self._pixmap.isNull():
            self._scaled_pixmap = self._pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            #Set the scaled pixmap on the label
            self.setPixmap(self._scaled_pixmap)

            
            # Calculate scaling factor
            self._original_size = self._pixmap.size()
            self._pixmap_size = self._scaled_pixmap.size()

            # Calculate offsets due to aspect ratio scaling
            if self._pixmap_size.width() < label_size.width():
                self._offset_x = (label_size.width() - self._pixmap_size.width()) // 2
            else:
                self._offset_x = 0

            if self._pixmap_size.height() < label_size.height():
                self._offset_y = (label_size.height() - self._pixmap_size.height()) // 2
            else:
                self._offset_y = 0

    def set_image(self, filename: str, saved_rect=None):
        """
        Parameters: filename (path to image file), saved_rect (QRect object)
        Returns: None
        Loads the pixmap from the given filename and sets it on the label.
        If saved_rect is provided, the image is cropped to the saved_rect.
        Finally, the image state is updated with _resize and update.
        """
        self._pixmap.load(filename)
        if saved_rect:
            self._pixmap = self._pixmap.copy(saved_rect)
        self._filename = filename
        self._resize()
        self.update()  # Force widget to redraw with the new image

    def save(self, location:str):
        if not self._pixmap.isNull():
            self._pixmap.save(location,'png',-1)

    @pyqtSlot()
    def crop(self):
        if not self._pixmap.isNull():
            self._crop_mode = True
            self.crop_started.emit()
            QTimer.singleShot(0, self._create_crosshairs) #Single shot timer to allow graphics to refresh before creating crosshairs

    def _create_crosshairs(self):
        if self._crop_mode:
            self._crosshairs[0] = QPoint(self._offset_x, self._offset_y)
            self._crosshairs[1] = QPoint(self._pixmap_size.width() + self._offset_x, self._offset_y)
            self._crosshairs[2] = QPoint(self._offset_x, self._pixmap_size.height() + self._offset_y)
            self._crosshairs[3] = QPoint(self._pixmap_size.width() + self._offset_x, self._pixmap_size.height() + self._offset_y)
            self._linehairs[0] = QPoint(self._offset_x + self._pixmap_size.width()//2, self._offset_y)
            self._linehairs[1] = QPoint(self._offset_x, self._offset_y + self._pixmap_size.height()//2)
            self._linehairs[2] = QPoint(self._offset_x + self._pixmap_size.width(), self._offset_y + self._pixmap_size.height()//2)
            self._linehairs[3] = QPoint(self._offset_x + self._pixmap_size.width()//2, self._offset_y + self._pixmap_size.height())
            self._crop_rubberband = QRubberBand(QRubberBand.Rectangle, self)
            self._crop_rubberband.setGeometry(QRect(self._crosshairs[0],self._crosshairs[3]))
            self._crop_rubberband.show()
            self.update()

    @pyqtSlot()
    def _crop_ended(self):
        currentQRect = self._crop_rubberband.geometry()
        self._crop_rubberband.deleteLater()
        self._crop_rubberband = None

        # Store crop rect for reuse
        self._crop_rect = currentQRect

        # Adjust currentQRect for the offsets
        adjusted_rect = QRect(currentQRect)
        adjusted_rect.translate(-self._offset_x, -self._offset_y)

        # Calculate scaling factors
        scale_factor_w = self._original_size.width() / self._pixmap_size.width()
        scale_factor_h = self._original_size.height() / self._pixmap_size.height()

        # Map the selection rectangle from the scaled image to the original image coordinates
        x = adjusted_rect.x() * scale_factor_w
        y = adjusted_rect.y() * scale_factor_h
        w = adjusted_rect.width() * scale_factor_w
        h = adjusted_rect.height() * scale_factor_h

        # Perform cropping
        self._crop_rect = QRect(int(x), int(y), int(w), int(h))

        self._pixmap = self._pixmap.copy(self._crop_rect)
        self._resize()

    @pyqtSlot()
    def scale(self):
        if not self._pixmap.isNull():
            self._scale_mode = True
            self._scale_point1 = None
            self._scale_point2 = None
            self.scale_started.emit()

    @pyqtSlot()
    def _scale_ended(self):
        self._set_scale()
        self._scale_point1 = None
        self._scale_point2 = None
        self.update()

    def _set_scale(self):
        if self._scale_point1 and self._scale_point2:
            scaled_size = self._scaled_pixmap.size()

            original_size = self._pixmap.size()
            scale_factor_x = original_size.width() / scaled_size.width()
            scale_factor_y = original_size.height() / scaled_size.height()

            origin_x = self._scale_point1.x() * scale_factor_x
            origin_y = self._scale_point1.y() * scale_factor_y
            end_x = self._scale_point2.x() * scale_factor_x
            end_y = self._scale_point2.y() * scale_factor_y

            dx = end_x - origin_x
            dy = end_y - origin_y
            self._length_in_pixels = math.sqrt(dx**2 + dy**2)

            dialog = ScaleDialog(self)
            if dialog.exec() == ScaleDialog.Accepted:
                self._unit, self._value = dialog.get_scale_data()

    def mouseMoveEvent(self, event:QMouseEvent):
        if self._crop_mode:
            pos = event.pos()
            if pos.x() < self._offset_x:
                pos.setX(self._offset_x)
            if pos.x() > self._offset_x + self._pixmap_size.width():
                pos.setX(self._offset_x + self._pixmap_size.width())
            if pos.y() < self._offset_y:
                pos.setY(self._offset_y)
            if pos.y() > self._offset_y + self._pixmap_size.height():
                pos.setY(self._offset_y + self._pixmap_size.height())
            if self._selected_crosshair == 0:
                self._crosshairs[0] = pos
                self._crosshairs[1] = QPoint(self._crosshairs[1].x(), pos.y())
                self._crosshairs[2] = QPoint(pos.x(), self._crosshairs[2].y())
            if self._selected_crosshair == 1:
                self._crosshairs[1] = pos
                self._crosshairs[0] = QPoint(self._crosshairs[0].x(), pos.y())
                self._crosshairs[3] = QPoint(pos.x(), self._crosshairs[3].y())
            if self._selected_crosshair == 2:
                self._crosshairs[2] = pos
                self._crosshairs[3] = QPoint(self._crosshairs[3].x(), pos.y())
                self._crosshairs[0] = QPoint(pos.x(), self._crosshairs[0].y())
            if self._selected_crosshair == 3:
                self._crosshairs[3] = pos
                self._crosshairs[2] = QPoint(self._crosshairs[2].x(), pos.y())
                self._crosshairs[1] = QPoint(pos.x(), self._crosshairs[1].y())
            if self._selected_linehair == 0:
                self._crosshairs[0] = QPoint(self._crosshairs[0].x(), pos.y())
                self._crosshairs[1] = QPoint(self._crosshairs[1].x(), pos.y())
            if self._selected_linehair == 1:
                self._crosshairs[0] = QPoint(pos.x(), self._crosshairs[0].y())
                self._crosshairs[2] = QPoint(pos.x(), self._crosshairs[2].y())
            if self._selected_linehair == 2:
                self._crosshairs[1] = QPoint(pos.x(), self._crosshairs[1].y())
                self._crosshairs[3] = QPoint(pos.x(), self._crosshairs[3].y())
            if self._selected_linehair == 3:
                self._crosshairs[2] = QPoint(self._crosshairs[2].x(), pos.y())
                self._crosshairs[3] = QPoint(self._crosshairs[3].x(), pos.y())
            
            self._linehairs[0] = QPoint((self._crosshairs[0].x() + self._crosshairs[1].x())//2,
                                        self._crosshairs[0].y())
            self._linehairs[1] = QPoint(self._crosshairs[0].x(),
                                        (self._crosshairs[0].y() + self._crosshairs[2].y())//2)
            self._linehairs[2] = QPoint(self._crosshairs[1].x(),
                                        (self._crosshairs[1].y() + self._crosshairs[3].y())//2)
            self._linehairs[3] = QPoint((self._crosshairs[2].x() + self._crosshairs[3].x())//2,
                                        self._crosshairs[2].y())
            
            self._crop_rubberband.setGeometry(QRect(self._crosshairs[0],self._crosshairs[3]).normalized())
            self.update()

        if self._scale_mode and self._selected_point:
            # Update the selected point's position
            if self._selected_point == 1:
                if self._shift_pressed:
                    self._scale_point1 = QPoint(event.pos().x(), self._scale_point2.y())
                else:
                    self._scale_point1 = event.pos()
            elif self._selected_point == 2:
                if self._shift_pressed:
                    self._scale_point2 = QPoint(event.pos().x(), self._scale_point1.y())
                else:
                    self._scale_point2 = event.pos()
            self.update()

    def mouseReleaseEvent(self, event:QMouseEvent):
        if self._crop_mode:
            self._selected_crosshair = None
            self._selected_linehair = None

        if self._scale_mode:
            self._selected_point = None

    def mousePressEvent(self, event:QMouseEvent) -> None:
        if self._crop_mode:
            click_pos = event.pos()

            if self._distance(click_pos, self._crosshairs[0]) < 10:
                self._selected_crosshair = 0
            elif self._distance(click_pos, self._crosshairs[1]) < 10:
                self._selected_crosshair = 1
            elif self._distance(click_pos, self._crosshairs[2]) < 10:
                self._selected_crosshair = 2
            elif self._distance(click_pos, self._crosshairs[3]) < 10:
                self._selected_crosshair = 3
            elif self._distance(click_pos, self._linehairs[0]) < 10:
                self._selected_linehair = 0
            elif self._distance(click_pos, self._linehairs[1]) < 10:
                self._selected_linehair = 1
            elif self._distance(click_pos, self._linehairs[2]) < 10:
                self._selected_linehair = 2
            elif self._distance(click_pos, self._linehairs[3]) < 10:
                self._selected_linehair = 3
            self.update()

        if self._scale_mode:
            click_pos = event.pos()

            # Check if the user clicked near point 1 or point 2
            if self._scale_point1 and (self._distance(click_pos, self._scale_point1) < 10):
                self._selected_point = 1
            elif self._scale_point2 and (self._distance(click_pos, self._scale_point2) < 10):
                self._selected_point = 2
            elif self._scale_point1 is None:  # If no points exist, create the first one
                self._scale_point1 = click_pos
                self._selected_point = 1
            elif self._scale_point2 is None:  # If only one point exists, create the second one
                self._scale_point2 = click_pos
                self._selected_point = 2
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._scale_mode:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw the two points
            pen = QPen(QColor(Qt.red), 3)
            painter.setPen(pen)

            if self._scale_point1:
                painter.drawLine(self._scale_point1.x() - 5, self._scale_point1.y(), self._scale_point1.x() + 5, self._scale_point1.y())
                painter.drawLine(self._scale_point1.x(), self._scale_point1.y() - 5, self._scale_point1.x(), self._scale_point1.y() + 5)

            if self._scale_point2:
                painter.drawLine(self._scale_point2.x() - 5, self._scale_point2.y(), self._scale_point2.x() + 5, self._scale_point2.y())
                painter.drawLine(self._scale_point2.x(), self._scale_point2.y() - 5, self._scale_point2.x(), self._scale_point2.y() + 5)

            # Draw the line connecting the points
            pen = QPen(QColor(Qt.blue), 1)
            painter.setPen(pen)
            if self._scale_point1 and self._scale_point2:
                painter.drawLine(self._scale_point1, self._scale_point2)

        if self._crop_mode:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            pen = QPen(QColor(Qt.red), 3)
            painter.setPen(pen)

            for crosshair in self._crosshairs:
                painter.drawLine(crosshair.x() - 5, crosshair.y(), crosshair.x() + 5, crosshair.y())
                painter.drawLine(crosshair.x(), crosshair.y() - 5, crosshair.x(), crosshair.y() + 5)

            for i, linehair in enumerate(self._linehairs):
                if i == 0 or i == 3:
                    painter.drawLine(linehair.x()-5, linehair.y(), linehair.x()+5, linehair.y())
                elif i == 1 or i == 2:
                    painter.drawLine(linehair.x(), linehair.y()-5, linehair.x(), linehair.y()+5)

    def keyPressEvent(self, event:QKeyEvent) -> None:
        if self._scale_mode and event.key() == Qt.Key_Return:
            self._scale_mode = False
            self.scale_ended.emit()

        if self._crop_mode and event.key() == Qt.Key_Return:
            self._crop_mode = False
            self.crop_ended.emit()

        if event.key() == Qt.Key_Shift:
            self._shift_pressed = True

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event:QKeyEvent):
        if event.key() == Qt.Key_Shift:
            self._shift_pressed = False

        return super().keyReleaseEvent(event)

    def _distance(self, p1:QPoint, p2:QPoint) -> float:
        """Helper method to calculate the distance between two points."""
        return math.sqrt((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2)

    def clear(self):
        """
        Properly clears all image data and resets internal state.
        This overrides the inherited QLabel.clear() to ensure all pixmap data is removed.
        """
        self._pixmap = QPixmap()  # Empty pixmap
        self._scaled_pixmap = None
        self._filename = None
        self._crop_rect = None
        self._crosshairs = [None, None, None, None]
        self._linehairs = [None, None, None, None]
        self._selected_crosshair = None
        self._selected_linehair = None
        self._scale_mode = False
        self._crop_mode = False
        self._scale_point1 = None
        self._scale_point2 = None
        self._selected_point = None
        self._shift_pressed = False
        self._unit = None
        self._value = None
        self._length_in_pixels = None
        
        # Call QLabel's clear() to clear text/pixmap
        super().clear()
        self.update()  # Force redraw