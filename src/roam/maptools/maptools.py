from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from roam.maptools.touchtool import TouchMapTool
from roam.api import GPS, RoamEvents

import roam.config

import roam.resources_rc
import roam.utils


class RubberBand(QgsRubberBand):
    def __init__(self, canvas, geometrytype, width=5, iconsize=10):
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
        self.distancearea.setSourceCrs(self.canvas.mapRenderer().destinationCrs().srsid())
        ellispoid = QgsProject.instance().readEntry("Measure", "/Ellipsoid", GEO_NONE)
        self.distancearea.setEllipsoid(ellispoid[0])
        # mode = self.canvas.mapRenderer().hasCrsTransformEnabled()
        # self.distancearea.setEllipsoidalMode(ellispoidemode)

    def paint(self, p, *args):
        super(RubberBand, self).paint(p)

        # Enable to debug the render area

        # p.drawRect(self.boundingRect())
        if not roam.config.settings.get("draw_distance", True):
            return

        offset = QPointF(5, 5)
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
                distance = self.distancearea.measureLine(qgspoint, qgspointbefore)
                if int(distance) == 0:
                    continue
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
        height = rect.size().height()
        m2p = self.canvas.getCoordinateTransform()
        res = m2p.mapUnitsPerPixel()
        new = 50 / res
        top = rect.topLeft() - QPoint(0, new)
        bottom = rect.bottomRight() + QPoint(new, 0)
        return QRectF(top, bottom)


class BaseAction(QAction):
    def __init__(self, icon, name, tool, parent=None):
        super(BaseAction, self).__init__(icon, name, parent)
        self.setCheckable(False)
        self.tool = tool
        self.isdefault = False
        self.ismaptool = False


class UndoAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(UndoAction, self).__init__(QIcon(":/icons/back"),
                                         "Undo",
                                         tool,
                                         parent)
        self.setObjectName("UndoAction")
        self.setText(self.tr("Undo"))


class EndCaptureAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(EndCaptureAction, self).__init__(QIcon(":/icons/stop-capture"),
                                               "End Capture",
                                               tool,
                                               parent)
        self.setObjectName("EndCaptureAction")
        self.setText(self.tr("End Capture"))


class CaptureAction(BaseAction):
    def __init__(self, tool, geomtype, parent=None, text="Digitize"):
        self._defaulticon = QIcon(":/icons/capture-{}".format(geomtype))
        self._defaulttext = text
        super(CaptureAction, self).__init__(self._defaulticon,
                                            self._defaulttext,
                                            tool,
                                            parent)
        self.setObjectName("CaptureAction")
        self.setCheckable(True)
        self.isdefault = True
        self.ismaptool = True

    def setEditMode(self, enabled):
        if enabled:
            self.setText(self.tr("Edit"))
        else:
            self.setText(self._defaulttext)


class GPSTrackingAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(GPSTrackingAction, self).__init__(QIcon(":/icons/record"),
                                                "Track",
                                                tool,
                                                parent)
        self.setObjectName("GPSTrackingAction")
        self.setCheckable(True)

    def set_text(self, tracking):
        if tracking:
            self.setText(self.tr("Tracking"))
        else:
            self.setText(self.tr("Track"))


class GPSCaptureAction(BaseAction):
    def __init__(self, tool, geomtype, parent=None):
        super(GPSCaptureAction, self).__init__(QIcon(":/icons/gpsadd-{}".format(geomtype)),
                                               "GPS Capture",
                                               tool,
                                               parent)
        self.setObjectName("GPSCaptureAction")
        self.setText(self.tr("GPS Point"))
        self.setEnabled(False)

        GPS.gpsfixed.connect(self.setstate)
        GPS.gpsdisconnected.connect(lambda: self.setEnabled(False))

    def setstate(self, fixed, *args):
        self.setEnabled(fixed)


class PolylineTool(QgsMapToolEdit):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)
    error = pyqtSignal(str)

    def __init__(self, canvas, config=None):
        super(PolylineTool, self).__init__(canvas)
        self.logger = roam.utils.logger
        if not config:
            self.config = {}
        else:
            self.config = config
        self.minpoints = 2
        self.editmode = False
        self.editvertex = None
        self.points = []
        self.is_tracking = False
        self.canvas = canvas
        # TODO These are no good for colour blind
        self.valid_color = QColor.fromRgb(0, 0, 255, 100)
        # TODO These are no good for colour blind
        self.invalid_color = QColor.fromRgb(255, 0, 0, 100)

        self.startcolour = self.valid_color
        self.editcolour = QColor.fromRgb(0, 255, 0, 150)
        self.band = RubberBand(self.canvas, QGis.Line, width=5, iconsize=20)
        self.band.setColor(self.startcolour)

        self.errorband = RubberBand(self.canvas, QGis.Line, width=5, iconsize=20)
        self.errorband.setColor(QColor.fromRgb(153, 153, 153, 90))
        self.errorlocations = QgsRubberBand(self.canvas, QGis.Point)
        self.errorlocations.setColor(self.invalid_color)
        self.errorlocations.setIconSize(20)
        self.errorlocations.setIcon(QgsRubberBand.ICON_BOX)

        self.pointband = QgsRubberBand(self.canvas, QGis.Point)
        self.pointband.setColor(self.startcolour)
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

        self.captureaction = CaptureAction(self, "line", text="Digitize")
        self.captureaction.toggled.connect(self.update_state)
        self.trackingaction = GPSTrackingAction(self)
        self.endcaptureaction = EndCaptureAction(self)

        self.undoaction = UndoAction(self)
        self.undoaction.setEnabled(False)
        self.undoaction.triggered.connect(self.undo)

        self.trackingaction.setEnabled(False)

        self.trackingaction.toggled.connect(self.set_tracking)

        self.captureaction.toggled.connect(self.update_end_capture_state)
        self.trackingaction.toggled.connect(self.update_end_capture_state)
        self.endcaptureaction.setEnabled(False)

        self.endcaptureaction.triggered.connect(self.endcapture)

        self.gpscapture = GPSCaptureAction(self, "line")
        self.gpscapture.setText("Add Vertex")
        self.gpscapture.triggered.connect(self.add_vertex)

        self.timer = QTimer()

        GPS.gpsfixed.connect(self.update_tracking_button)
        GPS.gpsdisconnected.connect(self.update_tracking_button_disconnect)
        RoamEvents.selectioncleared.connect(self.selection_updated)
        RoamEvents.selectionchanged.connect(self.selection_updated)

        self.snapping = True

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reset()
        if event.key() == Qt.Key_S:
            self.toggle_snapping()
            RoamEvents.snappingChanged.emit(self.snapping)

    def setSnapping(self, snapping):
        self.snapping = snapping

    def toggle_snapping(self):
        self.snapping = not self.snapping

    def selection_updated(self, *args):
        if self.editmode:
            self.reset()
            self.setEditMode(False, None)

    def update_end_capture_state(self, *args):
        if self.trackingaction.isChecked() and self.captureaction.isChecked():
            self.endcaptureaction.setEnabled(self.capturing)
            self.undoaction.setEnabled(self.capturing)

    def update_tracking_button_disconnect(self):
        self.trackingaction.setEnabled(False)
        self.captureaction.toggle()

    def update_tracking_button(self, gps_fixed, info):
        self.trackingaction.setEnabled(gps_fixed)

    def update_state(self, toggled):
        if self.is_tracking:
            self.set_tracking(False)

    def set_tracking(self, enable_tracking):
        if not enable_tracking and not self.captureaction.isChecked():
            # Some other tool is grabbing us so we will keep trakcing
            return

        if enable_tracking:
            self.captureaction.setIcon(QIcon(":/icons/pause"))
            self.captureaction.setText("Pause")
            gpsettings = roam.config.settings.get("gps", {})
            config = gpsettings.get('tracking', {"time", 1})
            if "time" in config:
                self.band.removeLastPoint()
                self.timer.timeout.connect(self.add_vertex)
                value = config['time']
                value *= 1000
                self.timer.start(value)
                self.capturing = True
            elif "distance" in config:
                self.band.removeLastPoint()
                value = config['distance']
                self.add_point(GPS.postion)
                GPS.gpsposition.connect(self.track_gps_location_changed)
        else:
            self.captureaction.setIcon(self.captureaction._defaulticon)
            self.captureaction.setText("Digitize")

            if self.capturing:
                point = self.pointband.getPoint(0, self.pointband.numberOfVertices() - 1)
                if point:
                    self.band.addPoint(point)
            try:
                self.timer.stop()
                self.timer.timeout.disconnect(self.add_vertex)
            except TypeError:
                pass

            try:
                GPS.gpsposition.disconnect(self.track_gps_location_changed)
            except TypeError:
                pass
        self.is_tracking = enable_tracking
        self.trackingaction.set_text(enable_tracking)

    @property
    def max_distance(self):
        gpsettings = roam.config.settings.get("gps", {})
        config = gpsettings.get('tracking', {"time", 1})
        value = config['distance']
        return value

    def track_gps_location_changed(self, point, info):
        lastpoint = self.pointband.getPoint(0, self.pointband.numberOfVertices() - 1)
        distance = point.sqrDist(lastpoint)
        if distance >= self.max_distance:
            self.add_point(point)

    @property
    def actions(self):
        return [self.captureaction, self.trackingaction, self.gpscapture, self.endcaptureaction, self.undoaction]

    def add_vertex(self):
        location = GPS.postion
        self.add_point(location)
        # Add an extra point for the move band
        self.band.addPoint(location)

    def remove_last_vertex(self):
        self.remove_last_point()
        self.band.removeLastPoint(doUpdate=True)

    def canvasPressEvent(self, event):
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        geom = self.band.asGeometry()
        if not geom:
            return

        close, at, before, after, dist = geom.closestVertex(point)
        if dist < 30:
            vinfo = geom.vertexIdFromVertexNr(at)
            self.editpart = vinfo[1].part
            self.editvertex = vinfo[1].vertex
        else:
            self.editvertex = None
            self.editpart = 0

    def getPointFromEvent(self, event):
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        return point

    def canvasMoveEvent(self, event):
        if self.is_tracking:
            return

        if self.capturing:
            point = self.snappoint(event)
            self.band.movePoint(point)

        if self.editmode and self.editvertex is not None:
            at = self.editvertex
            point = self.snappoint(event)
            lastvertex = self.band.numberOfVertices() - 1
            if isinstance(self, PolygonTool) and at == lastvertex:
                self.band.movePoint(0, point, self.editpart)
                self.pointband.movePoint(0, point)
            elif isinstance(self, PolygonTool) and at == 0:
                self.band.movePoint(lastvertex, point, self.editpart)
                self.pointband.movePoint(lastvertex, point)

            self.band.movePoint(at, point, self.editpart)
            self.pointband.movePoint(at, point)

        self.update_valid_state()

    def update_valid_state(self):
        geom = self.band.asGeometry()
        if geom and self.band.numberOfVertices() > 0:
            if self.has_errors():
                self.band.setColor(self.invalid_color)
                self.pointband.setColor(self.invalid_color)
            else:
                self.band.setColor(self.valid_color)
                self.pointband.setColor(self.valid_color)

    def has_errors(self):
        geom = self.band.asGeometry()
        if not geom:
            return False

        errors = geom.validateGeometry()

        skippable = ["duplicate node", "Geometry has"]
        othererrors = []

        def is_safe(message):
            for safe in skippable:
                if safe in message:
                    return True
            return False

        # We need to remove errors that are "ok" and not really that bad

        ## We are harder on what is considered valid for polygons.
        if isinstance(self, PolygonTool):
            for error in errors:
                if not is_safe(error.what()):
                    othererrors.append(error)

        if self.node_count < self.minpoints:
            error = QgsGeometry.Error("Number of nodes < {0}".format(self.minpoints))
            othererrors.append(error)

        return othererrors

    @property
    def node_count(self):
        return self.band.numberOfVertices()

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.endcapture()
            return

        if not self.editmode:
            point = self.snappoint(event)
            qgspoint = QgsPoint(point)
            self.add_point(qgspoint)
        else:
            self.editvertex = None

    def add_point(self, point):
        self.points.append(point)
        self.band.addPoint(point)
        self.pointband.addPoint(point)
        self.capturing = True
        self.endcaptureaction.setEnabled(True)
        self.undoaction.setEnabled(True)

    def remove_last_point(self):
        if len(self.points) > 1:
            del self.points[-1]
            self.band.removeLastPoint(doUpdate=True)
            self.pointband.removeLastPoint(doUpdate=True)

    def endinvalidcapture(self, errors):
        geometry = self.band.asGeometry()
        if geometry:
            self.errorband.setToGeometry(geometry, None)
        for error in errors:
            if error.hasWhere():
                self.errorlocations.addPoint(error.where())

        self.capturing = False
        self.set_tracking(False)
        self.captureaction.setChecked(True)
        self.undoaction.setEnabled(False)
        self.endcaptureaction.setEnabled(False)
        self.reset()

    def undo(self):
        self.remove_last_point()

    def endcapture(self):
        if not self.editmode:
            self.band.removeLastPoint()
        errors = self.has_errors()
        if errors and self.config.get("geometry_validation", True):
            self.error.emit("Invalid geometry. <br>"
                            "Please recapture. Last capture shown in grey <br>"
                            "<h2>Errors</h2> {0}".format("<br>".join(error.what() for error in errors)))
            self.endinvalidcapture(errors)
            return

        self.capturing = False
        self.set_tracking(False)
        self.captureaction.setChecked(True)
        self.undoaction.setEnabled(False)
        self.endcaptureaction.setEnabled(False)
        geometry = self.band.asGeometry()
        if not geometry:
            return

        self.clearErrors()
        self.geometryComplete.emit(geometry)

    def clearErrors(self):
        self.errorband.reset(QGis.Line)
        self.errorlocations.reset(QGis.Point)

    def clearBand(self):
        self.reset()

    def reset(self, *args):
        self.band.reset(QGis.Line)
        self.pointband.reset(QGis.Point)
        self.capturing = False
        self.set_tracking(False)
        self.undoaction.setEnabled(False)
        self.endcaptureaction.setEnabled(False)

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def snappoint(self, event):
        if not self.snapping:
            return event.originalMapPoint()

        point = event.snapPoint(QgsMapMouseEvent.SnapProjectConfig)
        return point

    def setEditMode(self, enabled, geom):
        self.reset()
        self.editmode = enabled
        if self.editmode:
            self.band.setColor(self.editcolour)
            self.pointband.setColor(self.editcolour)
            geomtype = geom.type()
            if geomtype == QGis.Polygon:
                nodes = geom.asPolygon()[0]
            else:
                if geom.isMultipart():
                    nodes = [item for sublist in geom.asMultiPolyline() for item in sublist]
                else:
                    nodes = geom.asPolyline()
            for node in nodes:
                self.pointband.addPoint(node)
            self.band.setToGeometry(geom, None)
        else:
            self.band.setColor(self.startcolour)
            self.pointband.setColor(self.startcolour)

        self.endcaptureaction.setEnabled(self.editmode)
        self.captureaction.setEditMode(enabled)


class PolygonTool(PolylineTool):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)

    def __init__(self, canvas, config=None):
        super(PolygonTool, self).__init__(canvas, config)
        self.minpoints = 3
        self.captureaction = CaptureAction(self, "polygon", text="Digitize")
        self.captureaction.toggled.connect(self.update_state)
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
    error = pyqtSignal(str)

    def __init__(self, canvas, config=None):
        super(PointTool, self).__init__(canvas)
        if not config:
            self.config = {}
        else:
            self.config = config
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
        self.gpscapture = GPSCaptureAction(self, 'point')
        self.gpscapture.triggered.connect(self.addatgps)
        self.snapper = QgsMapCanvasSnapper(self.canvas)
        self.pointband = RubberBand(self.canvas, QGis.Point)
        self.startcolour = QColor.fromRgb(0, 0, 255, 100)
        self.pointband.setColor(self.startcolour)
        self.pointband.setIconSize(20)
        self.pointband.addPoint(QgsPoint(0, 0))
        self.pointband.hide()

    @property
    def actions(self):
        return [self.captureaction, self.gpscapture]

    def canvasPressEvent(self, event):
        self.startpoint = event.pos()

    def snappoint(self, event):
        if not self.snapping:
            return False, event.originalMapPoint()

        point = event.snapPoint(QgsMapMouseEvent.SnapProjectConfig)
        return event.isSnapped(), point

    def canvasReleaseEvent(self, event):
        if self.pinching:
            return

        if self.dragging:
            diff = self.startpoint - event.pos()
            if not abs(diff.x()) < 10 and not abs(diff.y()) < 10:
                super(PointTool, self).canvasReleaseEvent(event)
                return

        hassnap, point = self.snappoint(event)
        self.geometryComplete.emit(QgsGeometry.fromPoint(point))

    def canvasMoveEvent(self, event):
        hassnap, point = self.snappoint(event)
        if hassnap:
            self.pointband.movePoint(point)
            self.pointband.show()
        else:
            self.pointband.hide()

    def addatgps(self):
        location = GPS.postion
        self.geometryComplete.emit(QgsGeometry.fromPoint(location))

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

    def setEditMode(self, enabled, geom):
        self.captureaction.setEditMode(enabled)
