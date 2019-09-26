from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QColor, QCursor, QPixmap, QIcon
from qgis._core import QgsPoint, QgsGeometry, QgsWkbTypes, QgsPointXY, QgsTolerance, QgsPointLocator, QgsMultiPoint
from qgis._gui import QgsMapToolEdit, QgsRubberBand, QgsMapMouseEvent

import roam.config
import roam.utils
from roam.api import GPS, RoamEvents
from roam.maptools.actions import CaptureAction, GPSTrackingAction, EndCaptureAction, UndoAction, GPSCaptureAction
from roam.maptools.maptoolutils import point_from_event
from roam.maptools.rubberband import RubberBand


class PolylineTool(QgsMapToolEdit):
    mouseClicked = pyqtSignal(QgsPoint)
    geometryComplete = pyqtSignal(QgsGeometry)
    error = pyqtSignal(str)
    MODE = "POLYLINE"

    def __init__(self, canvas, config=None):
        super(PolylineTool, self).__init__(canvas)
        self.logger = roam.utils.logger
        if not config:
            self.config = {}
        else:
            self.config = config
        self.geom = None
        self.minpoints = 2
        self.editmode = False
        self.editvertex = None
        self.points = []
        self.is_tracking = False
        self.canvas = canvas
        self.valid_color = QColor.fromRgb(32, 218, 45, 100)
        self.invalid_color = QColor.fromRgb(216, 26, 96, 100)

        self.startcolour = self.valid_color
        self.editcolour = self.valid_color
        self.band = RubberBand(self.canvas, QgsWkbTypes.LineGeometry, width=5, iconsize=20)
        self.band.setColor(self.startcolour)

        self.errorband = RubberBand(self.canvas, QgsWkbTypes.LineGeometry, width=5, iconsize=20)
        self.errorband.setColor(QColor.fromRgb(64, 64, 64, 90))
        self.errorlocations = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.errorlocations.setColor(self.invalid_color)
        self.errorlocations.setIconSize(20)
        self.errorlocations.setIcon(QgsRubberBand.ICON_BOX)

        self.pointband = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.pointband.setColor(self.startcolour)
        self.pointband.setIconSize(20)
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

        self.active_color = self.startcolour

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
            self.setEditMode(False, None, None)

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
                self.add_point(GPS.position)
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
        location = GPS.position
        self.remove_last_point()
        self.add_point(location)
        # Add an extra point for the move band
        self.band.addPoint(location)

    def remove_last_vertex(self):
        self.remove_last_point()
        self.band.removeLastPoint(doUpdate=True)

    def canvasPressEvent(self, event):
        geom = self.band.asGeometry()
        if not geom:
            return

        point = point_from_event(event, self.snapping)
        if self.editmode:
            layer = self.currentVectorLayer()
            event.snapToGrid(layer.geometryOptions().geometryPrecision(), layer.crs())
            tol = QgsTolerance.vertexSearchRadius(self.canvas.mapSettings())
            loc = self.canvas.snappingUtils().locatorForLayer(layer)
            matches = loc.verticesInRect(point, tol)
            if matches:
                for match in matches:
                    if match.featureId() != self.feature.id():
                        continue

                    self.editpart = 0
                    self.editvertex = match.vertexIndex()
                    break
            else:
                self.editvertex = None
                self.editpart = 0

    def vertex_at_point(self, point):
        layer = self.currentVectorLayer()
        tol = QgsTolerance.vertexSearchRadius(self.canvas.mapSettings())
        loc = self.canvas.snappingUtils().locatorForLayer(layer)
        matches = loc.verticesInRect(point, tol)
        return matches

    def canvasReleaseEvent(self, event: QgsMapMouseEvent):
        if event.button() == Qt.RightButton:
            self.endcapture()
            return

        if not self.editmode:
            point = event.snapPoint()
            self.add_point(point)
        else:
            self.editvertex = None

    def canvasMoveEvent(self, event: QgsMapMouseEvent):
        if self.is_tracking:
            return

        point = point_from_event(event, self.snapping)
        if not self.editmode:
            self.pointband.movePoint(point)

        if self.capturing:
            self.band.movePoint(point)

        if self.editmode and self.editvertex is not None:
            found, vertexid = self.geom.vertexIdFromVertexNr(self.editvertex)
            self.geom.get().moveVertex(vertexid, QgsPoint(point))
            self.currentVectorLayer().triggerRepaint()
            self.feature.setGeometry(self.geom)
            self.currentVectorLayer().updateFeature(self.feature)
            self.pointband.setToGeometry(self.toMultiPoint(self.geom), self.currentVectorLayer())
            self.band.setToGeometry(self.geom, self.currentVectorLayer())

        self.update_valid_state()

    @property
    def is_polygon_mode(self):
        """
        Returns true if this tool is in polygon mode
        :note: This is a gross hack to avoid a import issue until it's refactored
        :return:
        """
        return self.MODE == "POLYGON"

    def update_valid_state(self):
        geom = self.band.asGeometry()
        if geom and self.band.numberOfVertices() > 0:
            if self.has_errors():
                self.set_band_color(self.invalid_color)
            else:
                if not self.editmode:
                    self.set_band_color(self.startcolour)
                else:
                    self.set_band_color(self.editcolour)

    @property
    def active_color(self):
        return self._active_color

    @active_color.setter
    def active_color(self, color):
        self._active_color = color

    def has_errors(self):
        if self.geom is None:
            geom = self.band.asGeometry()
        else:
            geom = self.geom

        errors = geom.validateGeometry()

        skippable = ["duplicate node", "Geometry has"]
        othererrors = []

        def is_safe(message):
            for safe in skippable:
                if safe in message:
                    return True
            return False

        # We need to remove errors that are "ok" and not really that bad
        # We are harder on what is considered valid for polygons.
        if self.is_polygon_mode:
            for error in errors:
                if not is_safe(error.what()):
                    othererrors.append(error)

        if self.node_count < self.minpoints:
            error = QgsGeometry.Error("Number of nodes < {0}".format(self.minpoints))
            othererrors.append(error)

        return othererrors

    @property
    def node_count(self):
        if self.editmode:
            return self.band.numberOfVertices()
        else:
            return self.band.numberOfVertices() - 1

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

    def get_geometry(self):
        if self.geom is None:
            return self.band.asGeometry()
        else:
            return self.geom

    def endinvalidcapture(self, errors):
        self.errorband.setToGeometry(self.get_geometry(), self.currentVectorLayer())
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
        self.clearErrors()
        self.geometryComplete.emit(self.get_geometry())

    def clearErrors(self):
        self.errorband.reset(QgsWkbTypes.LineGeometry)
        self.errorlocations.reset(QgsWkbTypes.PointGeometry)

    def clearBand(self):
        self.reset()

    def reset(self, *args):
        self.band.reset(QgsWkbTypes.LineGeometry)
        self.pointband.reset(QgsWkbTypes.PointGeometry)
        self.capturing = False
        self.set_tracking(False)
        self.undoaction.setEnabled(False)
        self.endcaptureaction.setEnabled(False)

    def activate(self):
        self.pointband.reset(QgsWkbTypes.PointGeometry)
        self.pointband.addPoint(QgsPointXY(0, 0))
        self.canvas.setCursor(self.cursor)

    def deactivate(self):
        """
        Deactive the tool.
        """
        self.clearBand()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def set_band_color(self, color):
        self.active_color = color
        self.band.setColor(color)
        self.pointband.setColor(color)

    def setEditMode(self, enabled, geom, feature):
        self.reset()
        self.editmode = enabled
        if self.geom != geom:
            self.clearErrors()

        self.geom = geom
        self.feature = feature
        if self.editmode:
            self.set_band_color(self.editcolour)
            self.pointband.setToGeometry(self.toMultiPoint(geom), self.currentVectorLayer())
            self.pointband.setVisible(True)
            self.band.setToGeometry(geom, self.currentVectorLayer())
        else:
            self.set_band_color(self.startcolour)

        self.endcaptureaction.setEnabled(self.editmode)
        self.endcaptureaction.setEditing(enabled)
        self.captureaction.setEditMode(enabled)


    def toMultiPoint(self, geom):
        points = QgsMultiPoint()
        for count, v in enumerate(geom.vertices()):
            points.addGeometry(v.clone())
        newgeom = QgsGeometry(points)
        return newgeom
