from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from roam.maptools.touchtool import TouchMapTool

class PolygonTool(QgsMapTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self):
        QgsMapTool.__init__(self)
        raise NotImplementedError
    
        self.points = []
        self.band = QgsRubberBand(self.canvas(), True)
        self.band.setColor(QColor.fromRgb(224,162,16))
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

    def canvasPressEvent(self, event):
        # TODO Add node dragging support.
        pass

    def getPointFromEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas().getCoordinateTransform().toMapCoordinates(x, y)
        return point

    def canvasMoveEvent(self, event):
        point = self.getPointFromEvent(event)
        if self.capturing:
            self.band.movePoint(point)
        
    def canvasReleaseEvent(self, event):
        point = self.getPointFromEvent(event)
        qgspoint = QgsPoint(point)
        self.points.append(qgspoint)
        self.band.addPoint(point)
        self.capturing = True

    def reset(self):
        self.band.reset()
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

    def canvasReleaseEvent(self, event):
        if self.pinching or self.dragging:
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

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False
