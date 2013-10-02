from PyQt4.QtCore import pyqtSignal, QRect, Qt
from PyQt4.QtGui import QCursor, QPixmap, QColor
from qgis.core import (QgsRectangle, QgsTolerance, 
                       QgsFeatureRequest, QgsFeature,
                       QgsVectorLayer, QGis)
from qgis.gui import QgsMapTool, QgsRubberBand

from maptool import MapTool
import maptoolutils

class EditTool(MapTool):
    """
        Inspection tool which copies the feature to a new layer
        and copies selected data from the underlying feature.
    """
    
    finished = pyqtSignal(QgsVectorLayer, QgsFeature)
    featuresfound = pyqtSignal(list)

    def __init__(self, canvas, layers, snapradius = 2):
        MapTool.__init__(self, canvas, layers)
        self.canvas = canvas
        self.radius = snapradius
        
        self.band = QgsRubberBand(self.canvas)
        self.band.setColor(QColor.fromRgb(224,162,16))
        self.band.setWidth(3)
        
        self.selectband = None
        
        self.selectrect = QRect()
        self.dragging = False

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
        
    def getFeatures(self, rect):
        rq = QgsFeatureRequest().setFilterRect(rect)

        self.band.reset()
        for layer in self.layers:
            rq = QgsFeatureRequest().setFilterRect(rect) 
            for feature in layer.getFeatures(rq):
                if feature.isValid():
                    yield feature, layer
                    
    def toSearchRect(self, point):
        searchRadius =  self.canvas.extent().width() * ( self.radius / 100.0 )

        point = self.toMapCoordinates(point)

        rect = QgsRectangle()                                                 
        rect.setXMinimum(point.x() - searchRadius)
        rect.setXMaximum(point.x() + searchRadius)
        rect.setYMinimum(point.y() - searchRadius)
        rect.setYMaximum(point.y() + searchRadius)
        return rect

    def canvasPressEvent(self, event):
        self.selectrect.setRect( 0, 0, 0, 0 )
        
        self.selectband = QgsRubberBand(self.canvas, QGis.Polygon )
        self.selectband.setColor(QColor.fromRgb(0,0,255, 65))
        self.selectband.setWidth(5)
        
    def canvasMoveEvent(self, event):
        if not event.buttons() == Qt.LeftButton:
            return
        
        if not self.dragging:
            self.dragging = True
            self.selectrect.setTopLeft(event.pos())
        self.selectrect.setBottomRight(event.pos())
        
        maptoolutils.setRubberBand(self.canvas, self.selectrect, self.selectband)  
                     
    def canvasReleaseEvent(self, event):
        if self.dragging:
            geometry = self.selectband.asGeometry()
            rect = geometry.boundingBox()            
        else:
            rect = self.toSearchRect(event.pos())
            
        self.dragging = False
        self.selectband.reset()
            
        features = list(self.getFeatures(rect))
            
        if len(features) == 1:
            feature = features[0]
            self.finished.emit(feature[1], feature[0])
        elif len(features) > 0:
            self.featuresfound.emit(features)


    def activate(self):
        """
        Set the tool as the active tool in the canvas. 

        @note: Should be moved out into qmap.py 
               and just expose a cursor to be used
        """
        self.canvas.setCursor(self.cursor)
        super(EditTool, self).activate()

    def deactivate(self):
        """
        Deactive the tool.
        """
        super(EditTool, self).deactivate()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True