from PyQt5.QtCore import Qt, QPointF, QPoint, QRectF
from PyQt5.QtGui import QFont, QPen, QBrush, QPainterPath, QPainter
from qgis._core import QgsDistanceArea, QgsProject, geoNone, QgsGeometry, QgsPoint
from qgis._gui import QgsRubberBand

import roam.config


class RubberBand(QgsRubberBand):
    def __init__(self, canvas, geometrytype, width=5, iconsize=10):
        super(RubberBand, self).__init__(canvas, geometrytype)
        self.canvas = canvas
        self.setIconSize(iconsize)
        self.setWidth(width)
        self.iconsize = iconsize
        self.font = QFont()
        self.font.setStyleHint(QFont.Times, QFont.PreferAntialias)
        self.font.setPointSize(20)
        self.font.setBold(True)

        self.blackpen = QPen(Qt.black)
        self.blackpen.setWidth(0.5)
        self.whitebrush = QBrush(Qt.white)
        self.unit = self.canvas.mapUnits()

        self.distancearea = self.createdistancearea()

    def createdistancearea(self):
        distancearea = QgsDistanceArea()
        dest = self.canvas.mapSettings().destinationCrs()
        distancearea.setSourceCrs(dest, QgsProject.instance().transformContext())
        ellispoid = QgsProject.instance().readEntry("Measure", "/Ellipsoid", geoNone())
        distancearea.setEllipsoid(ellispoid[0])
        return distancearea

    def paint(self, p, *args):
        super(RubberBand, self).paint(p)

        # p.drawRect(self.boundingRect())
        if not roam.config.settings.get("draw_distance", True):
            return

        offset = QPointF(5, 5)
        nodescount = self.numberOfVertices()
        for index in range(nodescount, -1, -1):
            if index == 0:
                return

            qgspoint = self.getPoint(0, index)
            qgspointbefore = self.getPoint(0, index - 1)
            # No point before means we are the first index and there is nothing
            # before us.
            if not qgspointbefore:
                return

            if qgspoint and qgspointbefore:
                distance = self.distancearea.measureLine(qgspoint, qgspointbefore)
                if int(distance) == 0:
                    continue
                text = QgsDistanceArea.formatDistance(distance, 3, self.unit, keepBaseUnit=False)
                linegeom = QgsGeometry.fromPolyline([QgsPoint(qgspoint), QgsPoint(qgspointbefore)])
                midpoint = linegeom.centroid().asPoint()
                midpoint = self.toCanvasCoordinates(midpoint) - self.pos()
                midpoint += offset
                path = QPainterPath()
                path.addText(midpoint, self.font, text)
                p.setPen(self.blackpen)
                p.setRenderHints(QPainter.Antialiasing)
                p.setFont(self.font)
                p.setBrush(self.whitebrush)
                p.drawPath(path)

    def boundingRect(self):
        rect = super(RubberBand, self).boundingRect()
        width = rect.size().width()
        height = rect.size().height()
        m2p = self.canvas.getCoordinateTransform()
        res = m2p.mapUnitsPerPixel()
        new = 50 / res
        top = rect.topLeft() - QPoint(0, new)
        bottom = rect.bottomRight() + QPoint(new, 0)
        return QRectF(top, bottom)