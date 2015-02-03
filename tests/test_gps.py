import pynmea2
import pytest

import roam.api.gps as gps

from PyQt4.QtCore import QDateTime, Qt
from roam.api.gps import GPSService
from qgis.core import QgsPoint, QgsGPSInformation

@pytest.fixture
def gpsservice():
    positon = QgsPoint(100, 200)
    info = QgsGPSInformation()
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

