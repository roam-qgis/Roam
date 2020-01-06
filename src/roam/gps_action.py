import os

from qgis.PyQt.QtCore import pyqtSignal, Qt, QRectF, QLine, QPoint
from qgis.PyQt.QtWidgets import QAction, QApplication
from qgis.PyQt.QtGui import QIcon, QColor, QBrush, QPen, QPainter, QPainterPath, QPolygonF

from qgis.core import QgsGpsInformation, QgsPoint, QgsPointXY
from qgis.gui import QgsMapCanvasItem

from roam import resources_rc, utils
from roam.utils import log

import roam.config


class GPSAction(QAction):
    gpsfixed = pyqtSignal(bool)

    def __init__(self, canvas, parent):
        icon = ":/icons/gps"
        self.gps = None
        super(GPSAction, self).__init__(QIcon(icon),
                                        QApplication.translate("GPSAction", "Enable GPS"),
                                        parent)
        self.canvas = canvas
        self.triggered.connect(self.connectGPS)

    def setgps(self, gps):
        self.gps = gps
        self.gps.gpsfixed.connect(self.fixed)
        self.gps.gpsfailed.connect(self.failed)
        self.gps.gpsdisconnected.connect(self.disconnected)

    def updateGPSPort(self):
        if self.gps.connected and not roam.config.settings.get('gpsport', '') == self.gps.currentport:
            self.gps.disconnectGPS()
            self.connectGPS()

    def connectGPS(self):
        if not self.gps.connected:
            self.setIcon(QIcon(":/icons/gps"))
            self.setIconText(self.tr("Connecting.."))
            self.setEnabled(False)
            portname = roam.config.settings.get('gpsport', '')
            self.gps.connectGPS(portname)
        else:
            self.gps.disconnectGPS()

    def disconnected(self):
        self.setEnabled(True)
        self.setIcon(QIcon(":/icons/gps"))
        self.setIconText("Enable GPS")

    def connected(self, gpsConnection):
        self.setEnabled(True)
        self.setIcon(QIcon(':/icons/gps_looking'))
        self.setIconText("Searching")

    def failed(self):
        self.setEnabled(True)
        log("GPS Failed to connect")
        self.setIcon(QIcon(':/icons/gps_failed'))
        self.setIconText("GPS Failed. Click to retry")

    def fixed(self, fixed, gpsInfo):
        self.setEnabled(True)
        if fixed:
            self.setIcon(QIcon(':/icons/gps_on'))
            self.setIconText("GPS Fixed")
        else:
            self.setIcon(QIcon(':/icons/gps_failed'))
            self.setIconText("Acquiring fix")


class GPSMarker(QgsMapCanvasItem):
    def __init__(self, canvas):
        super(GPSMarker, self).__init__(canvas)
        self.canvas = canvas
        self._quaility = 0
        self._heading = 0
        self.size = roam.config.settings.get('gps', {}).get('marker_size', 24)
        self.red = Qt.darkRed
        self.blue = QColor(129, 173, 210)
        self.green = Qt.darkGreen
        self._gpsinfo = QgsGpsInformation()

        self.pointbrush = QBrush(self.red)
        self.pointpen = QPen(Qt.black)
        self.pointpen.setWidth(1)
        self.map_pos = QgsPoint(0.0, 0.0)
        self.gps = None

    def setgps(self, gps):
        self.gps = gps

    def setSize(self, size):
        self.size = size

    def paint(self, painter, xxx, xxx2):
        self.setPos(self.toCanvasCoordinates(self.map_pos))

        halfSize = self.size / 2.0
        rect = QRectF(0 - halfSize, 0 - halfSize, self.size, self.size)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.quality == 0:
            color = self.red
        elif self.quality == 1:
            color = self.green
        elif self.quality >= 2:
            color = self.blue
        else:
            color = self.red

        self.pointpen.setColor(Qt.gray)
        self.pointpen.setWidth(1)
        self.pointbrush.setColor(color)

        painter.setBrush(self.pointbrush)
        painter.setPen(self.pointpen)
        y = 0 - halfSize
        x = rect.width() / 2 - halfSize
        line = QLine(x, y, x, rect.height() - halfSize)
        y = rect.height() / 2 - halfSize
        x = 0 - halfSize
        line2 = QLine(x, y, rect.width() - halfSize, y)

        # Arrow
        p = QPolygonF()
        p.append(QPoint(0 - halfSize, 0))
        p.append(QPoint(0, -self.size))
        x = rect.width() - halfSize
        p.append(QPoint(x, 0))
        p.append(QPoint(0, 0))

        offsetp = QPolygonF()
        offsetp.append(QPoint(0 - halfSize, 0))
        offsetp.append(QPoint(0, -self.size))
        x = rect.width() - halfSize
        offsetp.append(QPoint(x, 0))
        offsetp.append(QPoint(0, 0))

        waypoint = self.gps.waypoint
        if waypoint:
            az = self.map_pos.azimuth(waypoint)

            painter.save()
            painter.rotate(az)
            self.pointbrush.setColor(Qt.red)
            painter.setBrush(self.pointbrush)
            path = QPainterPath()
            path.addPolygon(offsetp)
            painter.drawPath(path)
            painter.restore()

        painter.save()
        painter.rotate(self._heading)
        path = QPainterPath()
        path.addPolygon(p)
        painter.drawPath(path)

        painter.restore()
        painter.drawEllipse(rect)
        painter.drawLine(line)
        painter.drawLine(line2)

    def boundingRect(self):
        halfSize = self.size / 2.0
        size = self.size * 2
        return QRectF(-size, -size, 2.0 * size, 2.0 * size)

    @property
    def quality(self):
        return self._gpsinfo.quality

    @quality.setter
    def quality(self, value):
        self._quaility = value
        self.update()

    def setCenter(self, map_pos, gpsinfo):
        self._heading = gpsinfo.direction
        self._gpsinfo = gpsinfo
        self.map_pos = QgsPointXY(map_pos)
        self.setPos(self.toCanvasCoordinates(self.map_pos))

    def updatePosition(self):
        self.setCenter(self.map_pos, self._gpsinfo)
