from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Vertex Finder Tool class
class PointTool(QgsMapTool):
    mouseClicked = pyqtSignal(QgsPoint)

    def __init__(self, canvas, form):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.form = form
        self.m1 = None #QgsVertexMarker(self.canvas)
        self.p1 = QgsPoint()
        #our own fancy cursor
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

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()

        layer = self.canvas.currentLayer()

        if layer <> None:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
            self.p1.setX(point.x())
            self.p1.setY(point.y())
                
        self.m1 = QgsVertexMarker(self.canvas)
        self.m1.setIconType(1)
        self.m1.setColor(QColor(255, 0, 0))
        self.m1.setIconSize(12)
        self.m1.setPenWidth (3)
        self.m1.setCenter(self.p1)
        self.mouseClicked.emit(point)

        # Open the form
        self.form.init()

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        self.canvas.scene().removeItem(self.m1)
        self.m1 = None #QgsVertexMarker(self.canvas)
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
