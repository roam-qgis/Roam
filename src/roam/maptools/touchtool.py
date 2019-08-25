from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor

from qgis.core import QGis
from qgis.gui import QgsRubberBand, QgsMapToolPan

from roam.utils import log
from roam.maptools import maptoolutils

from roam.api import RoamEvents

snapping = True

try:
    from qgis.gui import QgsMapToolTouch

    maptooltype = QgsMapToolTouch
except ImportError:
    maptooltype = QgsMapToolPan


class TouchMapTool(maptooltype):
    def __init__(self, canvas):
        super(TouchMapTool, self).__init__(canvas)
        self.pinching = False
        self.canvas = canvas
        self.dragging = False
        self.snapping = True
        RoamEvents.snappingChanged.connect(self.setSnapping)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S:
            self.toggle_snapping()

    def toggle_snapping(self):
        self.snapping = not self.snapping
        global snapping
        snapping = self.snapping
        RoamEvents.snappingChanged.emit(snapping)

    def canvasMoveEvent(self, event):
        if not self.pinching and event.buttons() & Qt.LeftButton:
            self.dragging = True
            super(TouchMapTool, self).canvasMoveEvent(event)

    def canvasReleaseEvent(self, event):
        self.dragging = False
        super(TouchMapTool, self).canvasReleaseEvent(event)

    def gestureEvent(self, event):
        gesture = event.gesture(Qt.PinchGesture)
        if gesture:
            self.pinching = True
            event.accept()
            self.handlegesture(gesture)
        return True

    def handlegesture(self, gesture):
        if gesture.state() == Qt.GestureFinished:
            rect = self.canvas.extent()
            rect.scale(1 / gesture.totalScaleFactor(), self.mappostion(gesture))
            self.canvas.setExtent(rect)
            self.canvas.refresh()
            self.pinching = False

    def mappostion(self, gesture):
        pos = gesture.centerPoint().toPoint()
        pos = self.canvas.mapFromGlobal(pos)
        center = self.canvas.getCoordinateTransform().toMapPoint(pos.x(), pos.y())
        return center

    def setSnapping(self, enabled):
        self.snapping = enabled
