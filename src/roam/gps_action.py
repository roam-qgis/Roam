import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSvg import QSvgRenderer

from qgis.core import *
from qgis.gui import *

from roam import resources_rc, utils
from roam.utils import log
from roam.api import RoamEvents

if os.name == 'nt':
    try:
        from power import PowerState
        powerenabled = True
    except ImportError as ex:
        utils.warning("Can't load Power management support {}".format(ex))
        powerenabled = False


class GPSAction(QAction):
    gpsfixed = pyqtSignal(bool)

    def __init__(self, icon, canvas, settings, parent):
        QAction.__init__(self, QIcon(icon), QApplication.translate("GPSAction", "Enable GPS", None, QApplication.UnicodeUTF8), parent)
        self.canvas = canvas
        self._position = None
        self.settings = settings
        self.triggered.connect(self.connectGPS)
        self.gpsConn = None
        self.isConnected = False
        self.NMEA_FIX_BAD = 1
        self.NMEA_FIX_2D = 2
        self.NMEA_FIX_3D = 3
        self.marker = GPSMarker(self.canvas)
        self.marker.hide()
        self.currentport = None
        self.lastposition = QgsPoint(0.0, 0.0)
        self.wgs84CRS = QgsCoordinateReferenceSystem(4326)

        if os.name == 'nt' and powerenabled:
            self.power = PowerState(self.parent())
            self.power.poweroff.connect(self.disconnectGPS)
            
    def updateGPSPort(self):
        if self.isConnected and not self.settings.settings['gpsport'] == self.currentport:
            self.disconnectGPS()
            self.connectGPS()

    def connectGPS(self):
        if not self.isConnected:
            #Enable GPS
            self.setIcon(QIcon(":/icons/gps"))
            self.setIconText(QApplication.translate("GPSAction", "Connecting", None, QApplication.UnicodeUTF8))
            self.setEnabled(False)

            portname = self.settings.settings.get("gpsport", '')
            self.currentport = portname
            if portname == 'scan':
                utils.log("Auto scanning for GPS port")
                portname = ''

            self.detector = QgsGPSDetector(portname)
            utils.log("Connecting to:{}".format(portname))
            self.detector.detected.connect(self.connected)
            self.detector.detectionFailed.connect(self.failed)
            self.isConnectFailed = False
            self.detector.advance()
        else:
            self.disconnectGPS()
            
    @property
    def position(self):
        return self._position

    @property
    def isConnected(self):
        return self._isconnected

    @isConnected.setter
    def isConnected(self, value):
        self._isconnected = value
        self.gpsfixed.emit(value)

    def disconnectGPS(self):
        if self.isConnected:
            self.gpsConn.stateChanged.disconnect(self.gpsStateChanged)
            self.gpsConn.close()

        self.marker.hide()
        log("GPS disconnect")
        self.isConnected = False
        self.setIcon(QIcon(":/icons/gps"))
        self.setIconText("Enable GPS")
        self.setEnabled(True)
        self._position = None
        QgsGPSConnectionRegistry.instance().unregisterConnection(gpsConnection)

    def connected(self, gpsConnection):
        self.setIcon(QIcon(':/icons/gps_looking'))
        self.setIconText("Searching")
        self.gpsConn = gpsConnection
        if os.name == 'nt' and powerenabled:
            self.power = PowerState(self.canvas)
            self.power.poweroff.connect(self.disconnectGPS)
            self.power.poweron.connect(self.connectGPS)
        self.gpsConn.stateChanged.connect(self.gpsStateChanged)
        self.isConnected = True
        self.setEnabled(True)
        QgsGPSConnectionRegistry.instance().registerConnection(gpsConnection)

    def failed(self):
        self.setEnabled(True)
        log("GPS Failed to connect")
        self.setIcon(QIcon(':/icons/gps_failed'))
        self.setIconText("GPS Failed. Click to retry")

    @property
    def zoomtolocation(self):
        return self.settings.settings.get('gpszoomonfix', True)

    def gpsStateChanged(self, gpsInfo):
        if gpsInfo.fixType == self.NMEA_FIX_BAD or gpsInfo.status == 0 or gpsInfo.quality == 0:
            self.setIcon(QIcon(':/icons/gps_failed'))
            self.setIconText("No fix yet")
            self.gpsfixed.emit(False)
            return

        elif gpsInfo.fixType == self.NMEA_FIX_3D or self.NMEA_FIX_2D:
            self.setIcon(QIcon(':/icons/gps_on'))
            self.setIconText("GPS Fixed")
            self.gpsfixed.emit(True)


        myPoistion = QgsPoint(gpsInfo.longitude, gpsInfo.latitude)

        # Recenter map if we go outside of the 95% of the area
        transform = QgsCoordinateTransform(self.wgs84CRS, self.canvas.mapRenderer().destinationCrs())
        try:
            map_pos = transform.transform(myPoistion)
        except QgsCsException:
            return

        RoamEvents.gpspostion.emit(myPoistion, gpsInfo)

        if self._position is None and self.zoomtolocation:
            self.canvas.zoomScale(1000)

        if not self.lastposition == map_pos:
            self.lastposition = map_pos
            rect = QgsRectangle(map_pos, map_pos)
            extentlimt = QgsRectangle(self.canvas.extent())
            extentlimt.scale(0.95)

            if not extentlimt.contains(map_pos):
                self.canvas.setExtent(rect)
                self.canvas.refresh()

        self.marker.show()
        self.marker.setCenter(map_pos)
        self._position = map_pos


class GPSMarker(QgsMapCanvasItem):

        def __init__(self, canvas):
            QgsMapCanvasItem.__init__(self, canvas)
            self.canvas = canvas
            self.size = 24
            self.map_pos = QgsPoint(0.0, 0.0)
            self.svgrender = QSvgRenderer(":/icons/gps_marker")

        def setSize(self, size):
            self.size = size

        def paint(self, painter, xxx, xxx2):
            self.setPos(self.toCanvasCoordinates(self.map_pos))

            halfSize = self.size / 2.0
            self.svgrender.render(painter, QRectF(0 - halfSize, 0 - halfSize, self.size, self.size ) )

        def boundingRect(self):
            halfSize = self.size / 2.0
            return QRectF(-halfSize, -halfSize, 2.0 * halfSize, 2.0 * halfSize)

        def setCenter(self, map_pos):
            self.map_pos = map_pos
            self.setPos(self.toCanvasCoordinates(self.map_pos))

        def updatePosition(self):
            self.setCenter(self.map_pos)


        
