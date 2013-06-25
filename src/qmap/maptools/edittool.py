from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QCursor, QPixmap, QColor
from qgis.core import (QgsRectangle, QgsTolerance, 
                       QgsFeatureRequest, QgsFeature,
                       QgsVectorLayer)
from qgis.gui import QgsMapTool, QgsRubberBand
from qmap.listfeatureform import ListFeaturesForm

class EditTool(QgsMapTool):
    """
        Inspection tool which copies the feature to a new layer
        and copies selected data from the underlying feature.
    """
    
    finished = pyqtSignal(QgsVectorLayer, QgsFeature)
    
    def __init__(self, canvas, layers, snapradius = 2):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.layers = layers
        self.radius = snapradius
        
        self.band = QgsRubberBand(self.canvas)
        self.band.setColor(QColor.fromRgb(224,162,16))
        self.band.setWidth(3)

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
        
    def getFeatures(self, point):
        searchRadius = (QgsTolerance.toleranceInMapUnits( self.radius, self.layers[0],
                                                        self.canvas.mapRenderer(), 
                                                        QgsTolerance.Pixels))
        point = self.toMapCoordinates(point)

        rect = QgsRectangle()                                                 
        rect.setXMinimum(point.x() - searchRadius)
        rect.setXMaximum(point.x() + searchRadius)
        rect.setYMinimum(point.y() - searchRadius)
        rect.setYMaximum(point.y() + searchRadius)
        
        rq = QgsFeatureRequest().setFilterRect(rect)

        self.band.reset()
        for layer in self.layers:
            rq = QgsFeatureRequest().setFilterRect(rect) 
            for feature in layer.getFeatures(rq):
                if feature.isValid():
                    yield feature, layer
        
    def canvasMoveEvent(self, event):
        for feature, _ in self.getFeatures(point = event.pos()):
            self.band.addGeometry(feature.geometry(), None)
                     
    def canvasReleaseEvent(self, event):
        features = list(self.getFeatures(point = event.pos()))
            
        if len(features) == 1:
            feature = features[0]
            self.finished.emit(feature[1], feature[0])
        elif len(features) > 0:
            listUi = ListFeaturesForm()
            listUi.loadFeatureList(features)
            listUi.openFeatureForm.connect(self.finished)
            listUi.exec_()
        
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
        return True