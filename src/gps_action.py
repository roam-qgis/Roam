
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSvg import QSvgRenderer
from qgis.core import *
from qgis.gui import *
import resources_rc
import utils
from utils import log
import power

class GPSAction(QAction):
    def __init__(self, icon, canvas, parent):
        QAction.__init__(self, icon, "Enable GPS", parent)
        self.canvas = canvas
        self.triggered.connect(self.connectGPS)
        self.gpsConn = None
        self.isConnected = False
        self.NMEA_FIX_BAD = 1
        self.NMEA_FIX_2D = 2
        self.NMEA_FIX_3D = 3
        self.marker = GPSMarker(self.canvas)
        self.marker.hide()
        self.lastposition = QgsPoint(0.0,0.0)
        self.wgs84CRS = QgsCoordinateReferenceSystem(4326)
        self.power = power.PowerState(self.parent())
        self.power.poweroff.connect(self.disconnectGPS)

    def connectGPS(self):
        if not self.isConnected:
            #Enable GPS
            self.setIcon(QIcon(":/icons/gps"))
            self.setIconText("Connecting")
            self.setEnabled(False)
            
            portname = utils.settings.value("gps/port").toString()
            log("Connecting to:" + portname)
            self.detector = QgsGPSDetector( portname )
            self.detector.detected.connect(self.connected)
            self.detector.detectionFailed.connect(self.failed)
            self.isConnectFailed = False
            self.detector.advance()
        else:
            self.disconnectGPS()
                
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
        
    def connected(self, gpsConnection):
        self.setIcon(QIcon(':/icons/gps_looking'))
        self.setIconText("Searching")
        self.gpsConn = gpsConnection
        self.power = power.PowerState(self.canvas)
        self.power.poweroff.connect(self.disconnectGPS)
        self.power.poweron.connect(self.connectGPS)
        self.gpsConn.stateChanged.connect(self.gpsStateChanged)
        self.isConnected = True
        self.setEnabled(True)
        
    def failed(self):
        self.setEnabled(True)
        log("GPS Failed to connect")
        self.setIcon(QIcon(':/icons/gps_failed'))
        self.setIconText("GPS Failed. Click to retry")

    def gpsStateChanged(self, gpsInfo):
        fixed = False
        if gpsInfo.fixType == self.NMEA_FIX_BAD or gpsInfo.status == 0 or gpsInfo.quality == 0:
            self.setIcon(QIcon(':/icons/gps_failed'))
            self.setIconText("No fix yet")
        elif gpsInfo.fixType == self.NMEA_FIX_3D or self.NMEA_FIX_2D:
            self.setIcon(QIcon(':/icons/gps_on'))
            self.setIconText("GPS Fixed")
            fixed = True

        myPoistion = self.lastposition
        if fixed:
            myPoistion = QgsPoint(gpsInfo.longitude, gpsInfo.latitude)

        # Recenter map if we go outside of the 95% of the area
        transform = QgsCoordinateTransform(self.wgs84CRS, self.canvas.mapRenderer().destinationCrs())
        try:
            map_pos = transform.transform(myPoistion)
        except QgsCsException:
            return

        if not self.lastposition == map_pos:
            self.lastposition == map_pos
            rect = QgsRectangle( map_pos, map_pos )
            extentlimt = QgsRectangle( self.canvas.extent() )
            extentlimt.scale(0.95)

            if not extentlimt.contains(  map_pos ):
                self.canvas.setExtent( rect )
                self.canvas.refresh()

        self.marker.show()
        self.marker.setCenter( map_pos )

class GPSMarker(QgsMapCanvasItem):
        def __init__(self, canvas):
            QgsMapCanvasItem.__init__(self, canvas)
            self.canvas = canvas
            self.size = 24
            self.map_pos = QgsPoint(0.0,0.0)
            self.svgrender = QSvgRenderer(":/icons/gps_marker")
            
        def setSize( self, size ):
            self.size = size

        def paint(self, painter, xxx, xxx2):
            self.setPos(self.toCanvasCoordinates(self.map_pos))
            
            halfSize = self.size / 2.0
            self.svgrender.render( painter, QRectF(0 - halfSize, 0 - halfSize, self.size, self.size ) )

        def boundingRect(self):
            halfSize = self.size / 2.0
            return QRectF( -halfSize, -halfSize, 2.0 * halfSize, 2.0 * halfSize )

        def setCenter(self, map_pos):
            self.map_pos = map_pos
            self.setPos(self.toCanvasCoordinates(self.map_pos))

        def updatePosition(self):
            self.setCenter(self.map_pos)


        