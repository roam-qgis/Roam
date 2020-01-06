import sip
import os
from datetime import datetime

import pynmea2
from PyQt5.QtSerialPort import QSerialPort
from qgis.PyQt.QtCore import QObject, pyqtSignal, QDate, QDateTime, QTime, Qt, QTimer, QIODevice
from qgis.core import (QgsGpsDetector, QgsPointXY, QgsNmeaConnection, QgsGpsConnection, \
                       QgsCoordinateTransform, QgsCoordinateReferenceSystem, \
                       QgsGpsInformation, QgsCsException, QgsProject)

from roam.config import settings as config
from roam.utils import log

import roam.utils

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


GPSLOGFILENAME = config.get("gpslogfile", None)
GPSLOGGING = not GPSLOGFILENAME is None


class GPSService(QObject):
    gpsfixed = pyqtSignal(bool, object)
    gpsfailed = pyqtSignal()
    gpsdisconnected = pyqtSignal()
    connectionStatusChanaged = pyqtSignal(bool)

    # Connect to listen to GPS status updates.
    gpsposition = pyqtSignal(QgsPointXY, object)
    firstfix = pyqtSignal(QgsPointXY, object)

    def __init__(self):
        super(GPSService, self).__init__()
        self.isConnected = False
        self._currentport = None
        self._position = None
        self.latlong_position = None
        self.elevation = None
        self.info = QgsGpsInformation()
        self.wgs84CRS = QgsCoordinateReferenceSystem(4326)
        self.crs = None
        self.waypoint = None
        self._gpsupdate_frequency = 1.0
        self._gpsupdate_last = datetime.min
        self.gpslogfile = None
        self.gpsConn = None
        self.device = None
        
    def __del__(self):
        if self.gpsConn:
            self.deleteLater()

        if self.device:
            self.deleteLater()

        if not self.gpslogfile is None:
            self.gpslogfile.close()

    @property
    def connected(self):
        """
        Is the GPS connected
        :return: Retruns true if the GPS is connected
        """
        return self.isConnected

    @connected.setter
    def connected(self, value):
        self.isConnected = value

    @property
    def position(self) -> QgsPointXY:
        return self._position

    def log_gps(self, line):
        if not GPSLOGGING:
            # No logging for you.
            return

        if self.gpslogfile is None:
            self.gpslogfile = open(GPSLOGFILENAME, "w")

        self.gpslogfile.write(line + "\n")
        self.gpslogfile.flush()

    def gpsinfo(self, attribute):
        """
        Return information about the GPS position.
        :param attribute:
        :return:
        """
        if attribute.lower() == 'x':
            return self.position.x()
        if attribute.lower() == 'y':
            return self.position.y()
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
        if not self.connected:
            self._currentport = portname
            if portname == 'scan' or portname == '':
                portname = ''
                self.detector = QgsGpsDetector(portname)
                self.detector.detected.connect(self.gpsfound_handler)
                self.detector.detectionFailed.connect(self.gpsfailed)
                self.detector.advance()
            elif portname.startswith("COM"):
                baudrates = [QSerialPort.Baud4800 , QSerialPort.Baud9600 , QSerialPort.Baud38400 , QSerialPort.Baud57600 , QSerialPort.Baud115200]
                flow = config.get("gps", {}).get("flow_control", None)
                rate = config.get("gps", {}).get("rate", None)
                if rate:
                    baudrates = [rate]

                for rate in baudrates:
                    self.device = QSerialPort(portname)
                    self.device.setBaudRate(rate)
                    if flow == "hardware":
                        self.device.setFlowControl(QSerialPort.HardwareControl)
                    elif flow == "software":
                        self.device.setFlowControl(QSerialPort.SoftwareControl)
                    else:
                        self.device.setFlowControl(QSerialPort.NoFlowControl)
                    self.device.setParity(QSerialPort.NoParity)
                    self.device.setDataBits(QSerialPort.Data8)
                    self.device.setStopBits(QSerialPort.OneStop)
                    if self.device.open(QIODevice.ReadWrite):
                        self.gpsConn = QgsNmeaConnection(self.device)
                        self.gpsfound_handler(self.gpsConn)
                        break
                    else:
                        del self.device
                        continue
                else:
                    # If we can't connect to any GPS just error out
                    self.gpsfailed.emit()

    def disconnectGPS(self):
        if self.connected:
            self.gpsConn.close()
            self.gpsConn.stateChanged.disconnect(self.gpsStateChanged)
            # TODO: This doesn't fire for some reason anymore.  Do we need it still?
            self.gpsConn.nmeaSentenceReceived.disconnect(self.parse_data)
            self.gpsConn.deleteLater()

        self.isConnected = False
        self._position = None
        self.gpsdisconnected.emit()

    def gpsfound_handler(self, gpsConnection) -> None:
        """
        Handler for when the GPS signal has been found
        :param gpsConnection:  The connection for the GPS
        :return: None
        """
        if not isinstance(gpsConnection, QgsNmeaConnection):
            # This can be hit if the scan is used as the bindings in QGIS aren't
            # right and will not have the type set correctly
            import sip
            gpsConnection = sip.cast(gpsConnection, QgsGpsConnection)
            self.gpsConn = gpsConnection

        self.gpsConn.stateChanged.connect(self.gpsStateChanged)
        self.gpsConn.nmeaSentenceReceived.connect(self.parse_data)
        self.connected = True

    def parse_data(self, datastring):
        self.log_gps(datastring)
        try:
            data = pynmea2.parse(datastring)
        except AttributeError as er:
            log(er.message)
            return
        except pynmea2.SentenceTypeError as er:
            log(er.message)
            return
        except pynmea2.ParseError as er:
            log(er.message)
            return
        except pynmea2.ChecksumError as er:
            log(er.message)
            return

        mappings = {"RMC": self.extract_rmc,
                    "GGA": self.extract_gga,
                    "GSV": self.extract_gsv,
                    "VTG": self.extract_vtg,
                    "GSA": self.extract_gsa}
        try:
            mappings[data.sentence_type](data)
            self.gpsStateChanged(self.info)
        except KeyError as ex:
            log("Unhandled message type: {}. Message: {}".format(data.sentence_type, datastring))
            return
        except AttributeError as ex:
            log(ex)
            return

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
        self.info.quality = safe_int(data.gps_qual)
        self.info.satellitesUsed = safe_int(data.num_sats)
        return self.info

    def extract_rmc(self, data):
        self.info.latitude = data.latitude
        self.info.longitude = data.longitude
        self.info.speed = KNOTS_TO_KM * safe_float(data.spd_over_grnd)
        self.info.status = data.status
        self.info.direction = safe_float(data.true_course)
        if data.datestamp and data.timestamp:
            date = QDate(data.datestamp.year, data.datestamp.month, data.datestamp.day)
            time = QTime(data.timestamp.hour, data.timestamp.minute, data.timestamp.second)
            dt = QDateTime()
            self.info.utcDateTime.setTimeSpec(Qt.UTC)
            self.info.utcDateTime.setDate(date)
            self.info.utcDateTime.setTime(time)
        return self.info

    def gpsStateChanged(self, gpsInfo: QgsGpsInformation):
        if gpsInfo.fixType == NMEA_FIX_BAD or gpsInfo.status == 0 or gpsInfo.quality == 0:
            self.gpsfixed.emit(False, gpsInfo)
            return

        elif gpsInfo.fixType == NMEA_FIX_3D or NMEA_FIX_2D:
            self.gpsfixed.emit(True, gpsInfo)

        map_pos = QgsPointXY(gpsInfo.longitude, gpsInfo.latitude)
        self.latlong_position = map_pos

        if self.crs:
            transform = QgsCoordinateTransform(self.wgs84CRS, self.crs, QgsProject.instance())
            try:
                map_pos = transform.transform(map_pos)
            except QgsCsException:
                log("Transform exception")
                return

            if self.position is None:
                self.firstfix.emit(map_pos, gpsInfo)

            self.info = gpsInfo

            if (datetime.now() - self._gpsupdate_last).total_seconds() > self._gpsupdate_frequency:
                self.gpsposition.emit(map_pos, gpsInfo)
                self._gpsupdate_last = datetime.now()

            self._position = map_pos
            self.elevation = gpsInfo.elevation


class FileGPSService(GPSService):
    def __init__(self, filename):
        super(FileGPSService, self).__init__()
        self.file = None
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._read_from_file)
        self.filename = filename

    def connectGPS(self, portname):
        # Normally the portname is passed but we will take a filename
        # because it's a fake GPS service  
        if not self.isConnected:
            self.file = open(self.filename, "r")
            self.timer.start()
            self.isConnected = True

    def _read_from_file(self):
        line = self.file.readline()
        if not line:
            self.file.seek(0)
            line = self.file.readline()
        self.parse_data(line)

    def disconnectGPS(self):
        if self.file:
            self.file.close()
        self.timer.stop()
        self.file = None
        self.gpsdisconnected.emit()


try:
    filename = config["gpsfile"]
    if os.path.exists(filename):
        roam.utils.info(f"Using NMEA file for GPS service: {filename}")
        GPS = FileGPSService(filename=filename)
    else:
        GPS = GPSService()
except KeyError:
    GPS = GPSService()
