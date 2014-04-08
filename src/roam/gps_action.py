import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSvg import QSvgRenderer

from qgis.core import *
from qgis.gui import *

from roam import resources_rc, utils
from roam.utils import log
from roam.api import RoamEvents, GPS

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
        self.settings = settings
        self.triggered.connect(self.connectGPS)
        GPS.gpsfixed.connect(self.fixed)
        GPS.gpsfailed.connect(self.failed)

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
            GPS.connectGPS(portname)
        else:
            self.disconnectGPS(portname)
            
    def disconnectGPS(self):
        GPS.disconnectGPS()
        self.setIcon(QIcon(":/icons/gps"))
        self.setIconText("Enable GPS")
        self.setEnabled(True)

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

    def fixed(self, fixed, gpsInfo):
        if fixed:
            self.setIcon(QIcon(':/icons/gps_failed'))
            self.setIconText("No fix yet")
        else:
            self.setIcon(QIcon(':/icons/gps_on'))
            self.setIconText("GPS Fixed")


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


        
