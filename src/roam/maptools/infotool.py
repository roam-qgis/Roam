from collections import OrderedDict

from PyQt4.QtCore import pyqtSignal, QRect, Qt
from PyQt4.QtGui import QCursor, QPixmap, QColor
from qgis.core import (QgsRectangle, QgsTolerance,
                       QgsFeatureRequest, QgsFeature,
                       QgsVectorLayer, QGis, QgsMapLayer)
from qgis.gui import QgsMapTool, QgsRubberBand

from roam.maptools.maptool import MapTool
from roam.maptools import maptoolutils

class InfoTool(QgsMapTool):
    infoResults = pyqtSignal(dict)

    def __init__(self, canvas, snapradius = 2):
        super(InfoTool, self).__init__(canvas)
        self.canvas = canvas
        self.radius = snapradius

        self.band = QgsRubberBand(self.canvas)
        self.band.setColor(QColor.fromRgb(224,162,16))
        self.band.setWidth(3)

        self.selectband = None
        self.selectrect = QRect()
        self.dragging = False
        self.selectionlayers = []

    def getFeatures(self, rect):
        self.band.reset()
        for layer in self.selectionlayers:
            if (not layer.type() == QgsMapLayer.VectorLayer
                or layer.geometryType() == QGis.NoGeometry):
                continue

            rect = self.toLayerCoordinates(layer, rect)

            rq = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
            features = []
            for feature in layer.getFeatures(rq):
                if feature.isValid():
                    features.append(feature)

            yield layer, features

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
        self.dragging = False
        self.selectrect.setRect( 0, 0, 0, 0 )

        self.selectband = QgsRubberBand(self.canvas, QGis.Polygon )
        self.selectband.setColor(QColor.fromRgb(0,0,255, 65))
        self.selectband.setWidth(5)

    def canvasMoveEvent(self, event):
        if not event.buttons() == Qt.LeftButton:
            return

        if not self.dragging:
            self.selectrect.setTopLeft(event.pos())
            self.dragging = True
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

        results = OrderedDict((l,f) for l, f in self.getFeatures(rect))
        print results
        self.infoResults.emit(results)

