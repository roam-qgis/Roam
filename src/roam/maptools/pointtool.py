from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *
from qgis.gui import *

from qgis.core import QgsWkbTypes
from roam.api import GPS

from roam.maptools.actions import CaptureAction, GPSCaptureAction
from roam.maptools.rubberband import RubberBand
from roam.maptools.touchtool import TouchMapTool


class PointTool(TouchMapTool):
    """
    A basic point tool that can be connected to actions in order to handle
    point based actions.
    """
    geometryComplete = pyqtSignal(QgsGeometry)
    error = pyqtSignal(str)

    def __init__(self, canvas, config=None):
        super(PointTool, self).__init__(canvas)
        self.canvas = canvas
        if not config:
            self.config = {}
        else:
            self.config = config
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                       "      c None",
                                       ".     c #FF0000",
                                       "+     c #FFFFFF",
                                       "                ",
                                       "       +.+      ",
                                       "      ++.++     ",
                                       "     +.....+    ",
                                       "    +.     .+   ",
                                       "   +.   .   .+  ",
                                       "  +.    .    .+ ",
                                       " ++.    .    .++",
                                       " ... ...+... ...",
                                       " ++.    .    .++",
                                       "  +.    .    .+ ",
                                       "   +.   .   .+  ",
                                       "   ++.     .+   ",
                                       "    ++.....+    ",
                                       "      ++.++     ",
                                       "       +.+      "]))

        self.captureaction = CaptureAction(self, 'point')
        self.gpscapture = GPSCaptureAction(self, 'point')
        self.gpscapture.triggered.connect(self.addatgps)
        self.snapper = self.canvas.snappingUtils()
        self.pointband = RubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.startcolour = QColor.fromRgb(0, 0, 255, 100)
        self.pointband.setColor(self.startcolour)
        self.pointband.setIconSize(20)
        self.pointband.addPoint(QgsPointXY(0, 0))
        self.pointband.hide()

    @property
    def actions(self):
        return [self.captureaction, self.gpscapture]

    def canvasPressEvent(self, event):
        self.startpoint = event.pos()

    def canvasReleaseEvent(self, event: QgsMapMouseEvent):
        if self.pinching:
            return

        if self.dragging:
            diff = self.startpoint - event.pos()
            if not abs(diff.x()) < 10 and not abs(diff.y()) < 10:
                super(PointTool, self).canvasReleaseEvent(event)
                return

        point = event.snapPoint()
        self.geometryComplete.emit(QgsGeometry.fromPointXY(point))

    def canvasMoveEvent(self, event: QgsMapMouseEvent):
        point = event.snapPoint()
        self.pointband.movePoint(point)
        self.pointband.show()

    def addatgps(self):
        location = GPS.position
        self.geometryComplete.emit(QgsGeometry.fromPointXY(location))

    def activate(self):
        """
        Set the tool as the active tool in the canvas.

        @note: Should be moved out into qmap.py
               and just expose a cursor to be used
        """
        self.pointband.reset(QgsWkbTypes.PointGeometry)
        self.pointband.addPoint(QgsPointXY(0, 0))
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        self.clearBand()

    def clearBand(self):
        self.pointband.reset(QgsWkbTypes.PointGeometry)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False

    def setEditMode(self, enabled, geom, feature):
        self.captureaction.setEditMode(enabled)
