import pynmea2

from PyQt4.QtCore import QObject, pyqtSignal, QDate, QDateTime, QTime, Qt

from qgis.core import (QgsGPSDetector, QgsGPSConnectionRegistry, QgsPoint, \
                        QgsCoordinateTransform, QgsCoordinateReferenceSystem, \
                        QgsGPSInformation, QgsCsException)
from roam.utils import log

NMEA_FIX_BAD = 1
NMEA_FIX_2D = 2
NMEA_FIX_3D = 3

KNOTS_TO_KM = 1.852

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class GPSService(QObject):
    gpsfixed = pyqtSignal(bool, object)
    gpsfailed = pyqtSignal()
    gpsdisconnected = pyqtSignal()

    # Connect to listen to GPS status updates.
    gpsposition = pyqtSignal(QgsPoint, object)
    firstfix = pyqtSignal(QgsPoint, object)


    def __init__(self):
        super(GPSService, self).__init__()
        self.isConnected = False
        self._currentport = None
        self.postion = None
        self.elevation = None
        self.info = QgsGPSInformation()
        self.wgs84CRS = QgsCoordinateReferenceSystem(4326)
        self.crs = None

    def gpsinfo(self, attribute):
        """
        Return information about the GPS postion.
        :param attribute:
        :return:
        """
        if attribute.lower() == 'x':
            return self.postion.x()
        if attribute.lower() == 'y':
            return self.postion.y()
        if attribute.lower() == 'z':
            return self.elevation
        if attribute.lower() == 'portname':
            return self.currentport
        else:
            return getattr(self.info, attribute)

    @property
    def currentport(self):
        return 'scan' if not self._currentport else self._currentport

    @currentport.setter
    def currentport(self, value):
        self._currentport = value

    def connectGPS(self, portname):
        if not self.isConnected:
            self._currentport = portname
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
        self.gpsConn.nmeaSentenceReceived.connect(self.parse_data)
        # self.gpsConn.stateChanged.connect(self.gpsStateChanged)
        self.isConnected = True
        QgsGPSConnectionRegistry.instance().registerConnection(self.gpsConn)

    def parse_data(self, datastring):
        data = pynmea2.parse(datastring)
        mappings = {"RMS": self.extract_rmc,
                    "GGA": self.extract_gga,
                    "GSV": self.extract_gsv,
                    "VTG": self.extract_vtg,
                    "GSA": self.extract_gsa}
        try:
            mappings[data.sentence_type](data)
            self.gpsStateChanged(self.info)
        except KeyError:
            log("{} not currently handled".format(data.sentence_type))
            pass

    def extract_vtg(self, data):
        self.info.speed = safe_float(data.spd_over_grnd_kmph)
        return self.info

    def extract_gsa(self, data):
        self.info.hdop = safe_float(data.hdop)
        self.info.pdop = safe_float(data.pdop)
        self.info.vdop = safe_float(data.vdop)
        self.info.fixMode = data.mode
        self.info.fixType = safe_int(data.mode_fix_type)
        return self.info

    def extract_gsv(self, data):
        pass

    def extract_gga(self, data):
        self.info.latitude = data.latitude
        self.info.longitude = data.longitude
        self.info.elevation = safe_float(data.altitude)
        self.info.quality = int(data.gps_qual)
        self.info.satellitesUsed = int(data.num_sats)
        return self.info

    def extract_rmc(self, data):
        self.info.latitude = data.latitude
        self.info.longitude = data.longitude
        self.info.speed = KNOTS_TO_KM * safe_float(data.spd_over_grnd)
        self.info.status = data.data_validity
        self.info.direction = safe_float(data.true_course)
        date = QDate(data.datestamp.year, data.datestamp.month, data.datestamp.day)
        time = QTime(data.timestamp.hour, data.timestamp.minute, data.timestamp.second)
        dt = QDateTime()
        self.info.utcDateTime.setTimeSpec(Qt.UTC)
        self.info.utcDateTime.setDate(date)
        self.info.utcDateTime.setTime(time)
        return self.info


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

            self.info = gpsInfo
            self.gpsposition.emit(map_pos, gpsInfo)
            self.postion = map_pos
            self.elevation = gpsInfo.elevation


GPS = GPSService()
