from PyQt4.QtCore import pyqtSignal, QRect, Qt
from PyQt4.QtGui import QCursor, QPixmap, QColor
from qgis.core import (QgsRectangle, QgsTolerance, 
                       QgsFeatureRequest, QgsFeature,
                       QgsVectorLayer, QGis)
from qgis.gui import QgsMapTool, QgsRubberBand

from roam.maptools.maptool import MapTool
from roam.maptools import maptoolutils


class EditTool(MapTool):
    """
        Inspection tool which copies the feature to a new layer
        and copies selected data from the underlying feature.
    """
    
    finished = pyqtSignal(object, QgsFeature)
    featuresfound = pyqtSignal(dict)

    def __init__(self, canvas, forms, snapradius = 2):
        MapTool.__init__(self, canvas, [])
        self.canvas = canvas
        self.radius = snapradius
        self.forms = forms
        
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

    def addForm(self, form):
        self.forms.append(form)
        self.layersupdated.emit(True)

    def layers(self):
        """
        Return a set of layers that this edit tool can work on
        """
        return set([form.QGISLayer for form in self.forms])

    def formsforlayer(self, layer):
        for form in self.forms:
            if form.QGISLayer == layer:
                yield form

    def reset(self):
        self.forms = []
        self.layersupdated.emit(False)

    def getFeatures(self, rect):
        rq = QgsFeatureRequest().setFilterRect(rect)

        self.band.reset()
        for layer in self.layers():
            forms = list(self.formsforlayer(layer))
            rq = QgsFeatureRequest().setFilterRect(rect)
            for feature in layer.getFeatures(rq):
                if feature.isValid():
                    yield feature, forms
                    
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
            if not geometry:
                return

            rect = geometry.boundingBox()            
        else:
            rect = self.toSearchRect(event.pos())
            
        self.dragging = False
        self.selectband.reset()
            
        features = dict(self.getFeatures(rect))

        if len(features) == 1:
            feature = features.keys()[0]
            forms = features.values()[0]
            if len(forms) == 1:
                self.finished.emit(forms[0], feature)
            else:
                self.featuresfound.emit(features)
        elif len(features) > 0:
            self.featuresfound.emit(features)

    def isEditTool(self):
        return True