from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from roam.maptools.touchtool import TouchMapTool
from roam.api import GPS

import roam.resources_rc
from roamgeometry import RoamGeometry


class RubberBand(QgsRubberBand):
    def __init__(self, canvas, geometrytype, width=5, iconsize=20):
        super(RubberBand, self).__init__(canvas, geometrytype)
        self.canvas = canvas
        self.setIconSize(iconsize)
        self.setWidth(width)
        self.iconsize = iconsize
        self.font = QFont()
        self.font.setStyleHint(QFont.Times, QFont.PreferAntialias)
        self.font.setPointSize(20)
        self.font.setBold(True)

        self.blackpen = QPen(Qt.black)
        self.blackpen.setWidth(0.5)
        self.whitebrush = QBrush(Qt.white)
        self.distancearea = QgsDistanceArea()
        self.createdistancearea()
        self.unit = self.canvas.mapRenderer().destinationCrs().mapUnits()

    def createdistancearea(self):
        self.distancearea.setSourceCrs( self.canvas.mapRenderer().destinationCrs().srsid())
        ellispoid = QgsProject.instance().readEntry("Measure", "/Ellipsoid", GEO_NONE)
        self.distancearea.setEllipsoid(ellispoid[0])
        #mode = self.canvas.mapRenderer().hasCrsTransformEnabled()
        #self.distancearea.setEllipsoidalMode(ellispoidemode)

    def paint(self, p, *args):
        super(RubberBand, self).paint(p)

        offset = QPointF(5,5)
        nodescount = self.numberOfVertices()
        for index in xrange(nodescount, -1, -1):
            if index == 0:
                return

            qgspoint = self.getPoint(0, index)
            qgspointbefore = self.getPoint(0, index - 1)
            # No point before means we are the first index and there is nothing
            # before us.
            if not qgspointbefore:
                return

            if qgspoint and qgspointbefore:
                distance = self.distancearea.measureLine( qgspoint, qgspointbefore)
                text = QgsDistanceArea.textUnit(distance, 3, self.unit, False)
                linegeom = QgsGeometry.fromPolyline([qgspoint, qgspointbefore])
                midpoint = linegeom.centroid().asPoint()
                midpoint = self.toCanvasCoordinates(midpoint) - self.pos()
                midpoint += offset
                path = QPainterPath()
                path.addText(midpoint, self.font, text)
                p.setPen(self.blackpen)
                p.setRenderHints(QPainter.Antialiasing)
                p.setFont(self.font)
                p.setBrush(self.whitebrush)
                p.drawPath(path)

    def boundingRect(self):
        rect = super(RubberBand, self).boundingRect()
        width = rect.size().width()
        rect.setWidth(width + 200)
        return rect


class BaseAction(QAction):
    def __init__(self, icon, name, tool, parent=None):
        super(BaseAction, self).__init__(icon, name, parent)
        self.setCheckable(False)
        self.tool = tool
        self.isdefault = False
        self.ismaptool = False


class EndCaptureAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(EndCaptureAction, self).__init__(QIcon(":/icons/stop-capture"),
                                                "End Capture",
                                               tool,
                                               parent)
        self.setObjectName("EnaCaptureAction")
        self.setText(self.tr("End Capture"))


class CaptureAction(BaseAction):
    def __init__(self, tool, geomtype, parent=None):
        super(CaptureAction, self).__init__(QIcon(":/icons/capture-{}".format(geomtype)),
                                               "Capture",
                                               tool,
                                               parent)
        self.setObjectName("CaptureAction")
        self.setText(self.tr("Capture"))
        self.setCheckable(True)
        self.isdefault = True
        self.ismaptool = True


class GPSCaptureAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(GPSCaptureAction, self).__init__(QIcon(":/icons/gpsadd"),
                                                "GPS Capture",
                                                tool,
                                                parent)
        self.setObjectName("GPSCaptureAction")
        self.setText(self.tr("GPS Capture"))
        self.setEnabled(False)

        GPS.gpsfixed.connect(self.setstate)

    def setstate(self, fixed, *args):
        self.setEnabled(fixed)


class PolylineTool(QgsMapTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(PolylineTool, self).__init__(canvas)
        self.points = []
        self.canvas = canvas
        self.band = RubberBand(self.canvas, QGis.Line, width=5, iconsize=20)
        self.band.setColor(QColor.fromRgb(0,0,255, 100))
        self.pointband = QgsRubberBand(self.canvas, QGis.Point)
        self.pointband.setColor(QColor.fromRgb(0,0,255, 100))
        self.pointband.setIconSize(20)
        self.snapper = QgsMapCanvasSnapper(self.canvas)
        self.capturing = False
        self.cursor = QCursor(QPixmap(["16 16 3 1",
            "      c None",
            ".     c #FF0000",
            "+     c #FFFFFF",
            "                ",
            "       +.+      ",
            "      ++.++     ",
            "     +.....+    ",
            "    +.     .+   ",
            "   +.   .   .+  ",
            "  +.    .    .+ ",
            " ++.    .    .++",
            " ... ...+... ...",
            " ++.    .    .++",
            "  +.    .    .+ ",
            "   +.   .   .+  ",
            "   ++.     .+   ",
            "    ++.....+    ",
            "      ++.++     ",
            "       +.+      "]))

        self.captureaction = CaptureAction(self, "line")
        self.endcaptureaction = EndCaptureAction(self)

        self.captureaction.toggled.connect(self.endcaptureaction.setEnabled)
        self.endcaptureaction.setEnabled(False)

        self.endcaptureaction.triggered.connect(self.endcapture)

    @property
    def actions(self):
        return [self.captureaction, self.endcaptureaction]

    def canvasPressEvent(self, event):
        # TODO Add node dragging support.
        pass

    def getPointFromEvent(self, event):
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        return point

    def canvasMoveEvent(self, event):
        if self.capturing:
            point = self.snappoint(event.pos())
            self.band.movePoint(point)
        
    def canvasReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.endcapture()
        else:
            point = self.snappoint(event.pos())
            qgspoint = QgsPoint(point)
            self.points.append(qgspoint)
            self.band.addPoint(point)
            self.pointband.addPoint(point)
            self.capturing = True
            self.endcaptureaction.setEnabled(True)

    def endcapture(self):
        self.capturing = False
        self.band.removeLastPoint()
        geometry = self.band.asGeometry()
        if not geometry:
            return

        self.geometryComplete.emit(geometry)

    def clearBand(self):
        self.reset()

    def reset(self):
        self.band.reset(QGis.Line)
        self.pointband.reset(QGis.Point)
        self.points = []

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        self.reset()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def snappoint(self, point):
        try:
            _, results = self.snapper.snapToBackgroundLayers(point)
            point = results[0].snappedVertex
            return point
        except IndexError:
            return self.canvas.getCoordinateTransform().toMapCoordinates(point)


class PolygonTool(PolylineTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(PolygonTool, self).__init__(canvas)
        self.captureaction = CaptureAction(self, "polygon")
        self.reset()

    def reset(self):
        super(PolygonTool, self).reset()
        self.band.reset(QGis.Polygon)


class PointTool(TouchMapTool):
    """
    A basic point tool that can be connected to actions in order to handle
    point based actions.
    """
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(PointTool, self).__init__(canvas)
        self.cursor = QCursor(QPixmap(["16 16 3 1",
            "      c None",
            ".     c #FF0000",
            "+     c #FFFFFF",
            "                ",
            "       +.+      ",
            "      ++.++     ",
            "     +.....+    ",
            "    +.     .+   ",
            "   +.   .   .+  ",
            "  +.    .    .+ ",
            " ++.    .    .++",
            " ... ...+... ...",
            " ++.    .    .++",
            "  +.    .    .+ ",
            "   +.   .   .+  ",
            "   ++.     .+   ",
            "    ++.....+    ",
            "      ++.++     ",
            "       +.+      "]))

        self.captureaction = CaptureAction(self, 'point')
        self.gpscapture = GPSCaptureAction(self)
        self.gpscapture.triggered.connect(self.addatgps)

    @property
    def actions(self):
        return [self.captureaction, self.gpscapture]

    def canvasReleaseEvent(self, event):
        if self.pinching:
            return

        if self.dragging:
            super(PointTool, self).canvasReleaseEvent(event)
            return

        point = self.toMapCoordinates(event.pos())
        self.geometryComplete.emit(QgsGeometry.fromPoint(point))

    def addatgps(self):
        location = GPS.postion
        elevation = GPS.elevation
        self.geometryComplete.emit(RoamGeometry.fromPointZ(location, elevation))

        
    def activate(self):
        """
        Set the tool as the active tool in the canvas. 

        @note: Should be moved out into qmap.py 
               and just expose a cursor to be used
        """
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        pass

    def clearBand(self):
        self.band.reset()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False
