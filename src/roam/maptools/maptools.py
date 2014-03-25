from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from roam.maptools.touchtool import TouchMapTool

import roam.resources_rc


class EndCaptureAction(QAction):
    def __init__(self, tool, parent=None):
        super(EndCaptureAction, self).__init__(QIcon(), "End Capture", parent)
        self.setObjectName("endcapture")
        self.setCheckable(False)
        self.tool = tool
        self.isdefault = False
        self.ismaptool = False


class CaptureAction(QAction):
    def __init__(self, tool, geomtype, parent=None):
        super(CaptureAction, self).__init__(QIcon(":/icons/capture-{}".format(geomtype)), "Capture", parent)
        self.setObjectName("capture")
        self.setCheckable(True)
        self.tool = tool
        self.isdefault = True
        self.ismaptool = True


class PolylineTool(QgsMapTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(PolylineTool, self).__init__(canvas)
        self.points = []
        self.canvas = canvas
        self.band = QgsRubberBand(self.canvas, QGis.Line)
        self.band.setColor(QColor.fromRgb(224,162,16, 75))
        self.band.setWidth(5)
        self.capturing = False
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

        self.captureaction = CaptureAction(self, "line")
        self.endcaptureaction = EndCaptureAction(self)

        self.captureaction.toggled.connect(self.endcaptureaction.setEnabled)
        self.endcaptureaction.setEnabled(False)

        self.endcaptureaction.triggered.connect(self.endcapture)

    @property
    def actions(self):
        return [self.captureaction, self.endcaptureaction]

    def canvasPressEvent(self, event):
        # TODO Add node dragging support.
        pass

    def getPointFromEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
        return point

    def canvasMoveEvent(self, event):
        point = self.getPointFromEvent(event)
        if self.capturing:
            self.band.movePoint(point)
        
    def canvasReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.endcapture()
        else:
            point = self.getPointFromEvent(event)
            qgspoint = QgsPoint(point)
            self.points.append(qgspoint)
            self.band.addPoint(point)
            self.capturing = True

    def endcapture(self):
        self.capturing = False
        self.band.removeLastPoint()
        geometry = self.band.asGeometry()
        if not geometry:
            return

        self.geometryComplete.emit(geometry)

    def clearBand(self):
        self.reset()

    def reset(self):
        self.band.reset(QGis.Line)
        self.points = []

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        self.reset()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True


class PolygonTool(PolylineTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(PolygonTool, self).__init__(canvas)
        self.captureaction = CaptureAction(self, "polygon")
        self.reset()

    def reset(self):
        self.band.reset(QGis.Polygon)
        self.points = []


class PointTool(TouchMapTool):
    """
    A basic point tool that can be connected to actions in order to handle
    point based actions.
    """
    geometryComplete = pyqtSignal(QgsGeometry)
    
    def __init__(self, canvas):
        super(PointTool, self).__init__(canvas)
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

    @property
    def actions(self):
        return [self.captureaction]

    def canvasReleaseEvent(self, event):
        if self.pinching:
            return

        if self.dragging:
            super(PointTool, self).canvasReleaseEvent(event)
            return

        point = self.toMapCoordinates(event.pos())
        self.geometryComplete.emit(QgsGeometry.fromPoint(point))
        
    def activate(self):
        """
        Set the tool as the active tool in the canvas. 

        @note: Should be moved out into qmap.py 
               and just expose a cursor to be used
        """
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        pass

    def clearBand(self):
        self.band.reset()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False
