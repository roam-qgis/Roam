from PyQt4.QtCore import QObject, pyqtSignal

from qgis.core import QgsGPSDetector, QgsGPSConnectionRegistry, QgsPoint, QgsCoordinateTransform, QgsCoordinateReferenceSystem
from roam.utils import log

NMEA_FIX_BAD = 1
NMEA_FIX_2D = 2
NMEA_FIX_3D = 3


class GPSService(QObject):
    gpsfixed = pyqtSignal(bool, object)
    gpsfailed = pyqtSignal()
    gpsdisconnected = pyqtSignal()

    # Connect to listen to GPS status updates.
    gpspostion = pyqtSignal(QgsPoint, object)
    firstfix = pyqtSignal(QgsPoint, object)


    def __init__(self):
        super(GPSService, self).__init__()
        self.isConnected = False
        self.currentport = None
        self.postion = None
        self.elevation = None
        self.wgs84CRS = QgsCoordinateReferenceSystem(4326)
        self.crs = None

    def connectGPS(self, portname):
        if not self.isConnected:
            self.currentport = portname
            if portname == 'scan' or portname == '':
                log("Auto scanning for GPS port")
                portname = ''

            self.detector = QgsGPSDetector(portname)
            log("Connecting to:{}".format(portname or 'scan'))
            self.detector.detected.connect(self._gpsfound)
            self.detector.detectionFailed.connect(self.gpsfailed)
            self.isConnectFailed = False
            self.detector.advance()

    def disconnectGPS(self):
        if self.isConnected:
            self.gpsConn.stateChanged.disconnect(self.gpsStateChanged)
            self.gpsConn.close()

        log("GPS disconnect")
        self.isConnected = False
        self.postion = None
        QgsGPSConnectionRegistry.instance().unregisterConnection(self.gpsConn)
        self.gpsdisconnected.emit()

    def _gpsfound(self, gpsConnection):
        log("GPS found")
        self.gpsConn = gpsConnection
        self.gpsConn.stateChanged.connect(self.gpsStateChanged)
        self.isConnected = True
        QgsGPSConnectionRegistry.instance().registerConnection(self.gpsConn)

    def gpsStateChanged(self, gpsInfo):
        if gpsInfo.fixType == NMEA_FIX_BAD or gpsInfo.status == 0 or gpsInfo.quality == 0:
            self.gpsfixed.emit(False, gpsInfo)
            return

        elif gpsInfo.fixType == NMEA_FIX_3D or NMEA_FIX_2D:
            self.gpsfixed.emit(True, gpsInfo)


        map_pos = QgsPoint(gpsInfo.longitude, gpsInfo.latitude)

        if self.crs:
            transform = QgsCoordinateTransform(self.wgs84CRS, self.crs)
            try:
                map_pos = transform.transform(map_pos)
            except QgsCsException:
                log("Transform exception")
                return

            if self.postion is None:
                self.firstfix.emit(map_pos, gpsInfo)

            self.gpspostion.emit(map_pos, gpsInfo)
            self.postion = map_pos
            self.elevation = gpsInfo.elevation


GPS = GPSService()
