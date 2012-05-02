from qgis.core import *
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from PyQt4.QtCore import pyqtSignal, QVariant, Qt
from PyQt4.QtGui import QAction, QCursor, QPixmap
from utils import log

class SelectFeatureTool(QgsMapToolEmitPoint):
    foundFeature = pyqtSignal(QgsFeature, QVariant, str)
    
    def __init__(self, canvas, layer, column, bindto, radius ):
        QgsMapToolEmitPoint.__init__(self, canvas)
        self.layer = layer
        self.column = column
        self.bindto = bindto
        self.canvas = canvas
        self.bindto = bindto
        self.searchradius = radius
        self.canvasClicked.connect(self.findFeature)
        self.canvas.setMapTool(self)
        self.band = QgsRubberBand(self.canvas)
        self.band.setColor(Qt.blue)
        self.band.setWidth(3)
        self.cursor = QCursor(QPixmap(["16 16 3 1",
            "      c None",
            ".     c #32CD32",
            "+     c #32CD32",
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

            

    def findFeature(self, point, button):
        searchRadius = self.canvas.extent().width() * ( self.searchradius / 100.0)
        rect = QgsRectangle()
        rect.setXMinimum( point.x() - searchRadius );
        rect.setXMaximum( point.x() + searchRadius );
        rect.setYMinimum( point.y() - searchRadius );
        rect.setYMaximum( point.y() + searchRadius );

        self.layer.select( self.layer.pendingAllAttributesList(), rect, True, True)
        feature = QgsFeature()
        self.layer.nextFeature(feature)
        try:
            index = self.layer.fieldNameIndex(self.column)
            value = feature.attributeMap()[index].toString()
            self.foundFeature.emit(feature, value, self.bindto)
        except KeyError:
            return
    
    def canvasMoveEvent(self, event):
        point = self.toMapCoordinates( event.pos() )
        searchRadius = self.canvas.extent().width() * ( self.searchradius / 100.0)
        rect = QgsRectangle()
        rect.setXMinimum( point.x() - searchRadius );
        rect.setXMaximum( point.x() + searchRadius );
        rect.setYMinimum( point.y() - searchRadius );
        rect.setYMaximum( point.y() + searchRadius );

        self.layer.select( self.layer.pendingAllAttributesList(), rect, True, True)
        feature = QgsFeature()
        self.layer.nextFeature(feature)

        if not feature.isValid():
            log("Not a vaild feature")
            return
        
        self.band.setToGeometry(feature.geometry(), None)


    def setActive(self):
        self.canvas.setMapTool(self)
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        self.band.hide()