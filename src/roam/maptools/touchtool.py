from PyQt4.QtCore import Qt, QRect
from PyQt4.QtGui import QColor

from qgis.core import QGis
from qgis.gui import QgsMapToolTouch, QgsRubberBand, QgsMapToolPan

from roam.utils import log
from roam.maptools import maptoolutils


class TouchMapTool(QgsMapToolTouch):
    def __init__(self, canvas):
        super(TouchMapTool, self).__init__(canvas)
        self.pinching = False
        self.canvas = canvas
        self.dragging = False

    def canvasMoveEvent(self, event):
        if not self.pinching:
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
