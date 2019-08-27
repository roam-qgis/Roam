import os
import pynmea2
import pytest

import roam.api.gps as gps

from qgis.PyQt.QtCore import QDateTime, Qt
from roam.api.gps import GPSService
from qgis.core import QgsPoint, QgsGpsInformation, QgsCoordinateReferenceSystem


def data(name):
    """
    Return the full path from the data folder with the given name
    :param name: The name of the file to return
    :return: The full path of the given file from the data folder
    """
    f = os.path.join(os.path.dirname(__file__), "data", name)
    return f


@pytest.fixture
def gpsservice():
    positon = QgsPoint(100, 200)
    info = QgsGpsInformation()
    info.speed = 300
    info.direction = 90.0
    info.latitude = 90.0
    gps = GPSService()
    gps.postion = positon
    gps.elevation = 20
    gps.currentport = 'testport'
    gps.info = info
    return gps


def test_gpsinfo_reads_x(gpsservice):
    assert gpsservice.gpsinfo('x') == 100


def test_gpsinfo_reads_y(gpsservice):
    assert gpsservice.gpsinfo('y') == 200


def test_gpsinfo_reads_z(gpsservice):
    assert gpsservice.gpsinfo('z') == 20


def test_gpsinfo_reads_latitude(gpsservice):
    assert gpsservice.gpsinfo('latitude') == 90.0


def test_gpsinfo_reads_speed(gpsservice):
    assert gpsservice.gpsinfo('speed') == 300


def test_gpsinfo_reads_direction(gpsservice):
    assert gpsservice.gpsinfo('direction') == 90.0


def test_gpsinfo_reads_portname(gpsservice):
    assert gpsservice.gpsinfo('portname') == 'testport'


def test_gpsinfo_reads_returns_scan_on_empty_port():
    gps = GPSService()
    gps.currentport = ''
    assert gps.gpsinfo('portname') == 'scan'
    gps.currentport = None
    assert gps.gpsinfo('portname') == 'scan'


def test_extact_rmc_returns_correct_info():
    gps = GPSService()
    msg = "$GNRMC,033615.00,A,3157.10477,S,11549.42965,E,0.120,,270115,,,A*73"
    data = pynmea2.parse(msg)
    info = gps.extract_rmc(data)
    assert info.longitude == 115.8238275
    assert info.latitude == -31.951746166666666
    assert info.speed == 0.22224
    assert info.status == "A"
    assert info.direction == 0
    assert info.utcDateTime == QDateTime(2015, 1, 27, 3, 36, 15, 0, Qt.UTC)


def test_extact_rmc_handles_empty_values():
    gps = GPSService()
    msg = "$GNRMC,033523.00,V,,,,,,,270115,,,N*67"
    data = pynmea2.parse(msg)
    info = gps.extract_rmc(data)
    assert info.longitude == 0.0
    assert info.latitude == 0.0
    assert info.speed == 0.0
    assert info.status == "V"
    assert info.direction == 0
    assert info.utcDateTime == QDateTime(2015, 1, 27, 3, 35, 23, 0, Qt.UTC)
    msg = "$GPRMC,,V,,,,,,,,,,N*53"
    data = pynmea2.parse(msg)
    info = gps.extract_rmc(data)
    assert info.longitude == 0.0
    assert info.latitude == 0.0
    assert info.speed == 0.0
    assert info.status == "V"
    assert info.direction == 0
    assert info.utcDateTime == QDateTime(2015, 1, 27, 3, 35, 23, 0, Qt.UTC)


def test_extact_gga_returns_correct_info():
    gps = GPSService()
    msg = "$GNGGA,033534.00,3157.10551,S,11549.43027,E,1,05,1.69,43.4,M,-30.8,M,,*49"
    data = pynmea2.parse(msg)
    info = gps.extract_gga(data)
    assert info.longitude == 115.82383783333333
    assert info.latitude == -31.9517585
    assert info.elevation == 43.4
    assert info.quality == 1
    assert info.satellitesUsed == 5


def test_extact_gga_handles_empty_values():
    gps = GPSService()
    msg = "$GNGGA,033521.00,,,,,0,03,17.53,,,,,,*7D"
    data = pynmea2.parse(msg)
    info = gps.extract_gga(data)
    assert info.longitude == 0.0
    assert info.latitude == 0.0
    assert info.elevation == 0.0
    assert info.quality == 0
    assert info.satellitesUsed == 3
    msg = "$GPGGA,,,,,,0,,,,,,,,*66"
    data = pynmea2.parse(msg)
    info = gps.extract_gga(data)
    assert info.longitude == 0.0
    assert info.latitude == 0.0
    assert info.elevation == 0.0
    assert info.quality == 0
    assert info.satellitesUsed == 0


def test_extact_vtg_returns_correct_info():
    gps = GPSService()
    msg = "$GNVTG,,T,,M,0.148,N,0.274,K,A*31"
    data = pynmea2.parse(msg)
    info = gps.extract_vtg(data)
    assert info.speed == 0.274


def test_extact_vtg_handles_empty_values():
    gps = GPSService()
    msg = "$GNVTG,,,,,,,,,N*2E"
    data = pynmea2.parse(msg)
    info = gps.extract_vtg(data)
    assert info.speed == 0.0


def test_extact_gsa_returns_correct_info():
    gps = GPSService()
    msg = "$GNGSA,A,3,80,79,73,82,,,,,,,,,1.75,1.09,1.37*1A"
    data = pynmea2.parse(msg)
    info = gps.extract_gsa(data)
    assert info.hdop == 1.09
    assert info.pdop == 1.75
    assert info.vdop == 1.37
    assert info.fixMode == "A"
    assert info.fixType == 3


def test_extact_gsa_handles_empty_values():
    gps = GPSService()
    msg = "$GNGSA,A,1,,,,,,,,,,,,,,,*00"
    data = pynmea2.parse(msg)
    info = gps.extract_gsa(data)
    assert info.hdop == 0.0
    assert info.pdop == 0.0
    assert info.vdop == 0.0
    assert info.fixMode == "A"
    assert info.fixType == 1


def dont_crash_with_strange_gps_string():
    # WAT the heck is the PQXFI message?
    data = "$PQXFI,054109.0,2812.884789,S,15202.046024,E,462.1,2.92,4.14,0.82*73"
    gps = GPSService()
    gps.parse_data(data)


def test_glonass_parse_from_file():
    def update(pos, info):
        pass

    gps = GPSService()
    gps.gpsposition.connect(update)
    wgs84CRS = QgsCoordinateReferenceSystem(4326)
    gps.crs = wgs84CRS
    with open(data("glonass_gps_log.nmea"), "r") as f:
        for line in f:
            line = line.strip("\n")
            gps.parse_data(line)
