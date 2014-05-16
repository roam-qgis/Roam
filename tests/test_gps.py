import pytest

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

