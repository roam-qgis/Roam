from collections import OrderedDict

from PyQt4.QtCore import pyqtSignal, QRect, Qt, QRectF
from PyQt4.QtGui import QCursor, QPixmap, QColor
from qgis.core import (QgsRectangle, QgsTolerance,
                       QgsFeatureRequest, QgsFeature,
                       QgsVectorLayer, QGis, QgsMapLayer)
from qgis.gui import QgsMapTool, QgsRubberBand

from roam.maptools.maptool import MapTool
from roam.maptools.touchtool import TouchMapTool
from roam.maptools import maptoolutils
from roam.api.events import RoamEvents
from roam.utils import log


class InfoTool(QgsMapTool):
    def __init__(self, canvas, snapradius = 2):
        super(InfoTool, self).__init__(canvas)
        self.canvas = canvas
        self.radius = snapradius

        self.selectband = QgsRubberBand(self.canvas, QGis.Polygon )
        self.selectrect = QRect()
        self.dragging = False
        self.selectionlayers = []

    def getFeatures(self, rect, firstonly=False):
        # The MS SQL driver seems to crash with a empty rectangle.
        # Need to check QGIS to patch issue
        if rect.isEmpty():
            return

        for layer in self.selectionlayers.itervalues():
            if (not layer.type() == QgsMapLayer.VectorLayer or
                    layer.geometryType() == QGis.NoGeometry):
                continue

            rect = self.toLayerCoordinates(layer, rect)
            rq = QgsFeatureRequest().setFilterRect(rect) \
                .setFlags(QgsFeatureRequest.ExactIntersect)
            features = []
            for feature in layer.getFeatures(rq):
                if feature.isValid():
                    features.append(feature)

            yield layer, features

    def toSearchRect(self, point):
        size = 20
        rect = QRectF()
        rect.setLeft(point.x() - size)
        rect.setRight(point.x() + size)
        rect.setTop(point.y() - size)
        rect.setBottom(point.y() + size)

        transform = self.canvas.getCoordinateTransform()
        ll = transform.toMapCoordinates(rect.left(), rect.bottom())
        ur = transform.toMapCoordinates(rect.right(), rect.top())

        rect = QgsRectangle(ur, ll)
        return rect

    def canvasPressEvent(self, event):
        self.dragging = False
        self.selectrect.setRect(0, 0, 0, 0)

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
            firstonly = False
        else:
            firstonly = True
            rect = self.toSearchRect(event.pos())

        self.dragging = False
        self.selectband.reset()

        results = OrderedDict((l,f) for l, f in self.getFeatures(rect))

        RoamEvents.selectioncleared.emit()
        RoamEvents.selectionchanged.emit(results)
