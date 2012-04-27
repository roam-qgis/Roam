from form_binder import FormBinder
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from utils import log

# Vertex Finder Tool class
class PointTool(QgsMapTool):
    mouseClicked = pyqtSignal(QgsPoint)

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.m1 = None
        self.p1 = QgsPoint()
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
        pass

    def setAsMapTool(self):
        self.canvas.setMapTool(self)

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.p1.setX(point.x())
        self.p1.setY(point.y())

        self.mouseClicked.emit(self.p1)
        

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        self.canvas.scene().removeItem(self.m1)
        self.m1 = None
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
