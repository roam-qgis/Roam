import math
from functools import partial
from collections import defaultdict

from PyQt4.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QObject, pyqtProperty, QEasingCurve, QThread, \
    QRectF, QLocale, QPointF, QPoint
from PyQt4.QtGui import QActionGroup, QFrame, QWidget, QSizePolicy, \
    QAction, QPixmap, QCursor, QIcon, QColor, QMainWindow, QPen, QGraphicsItem, QPolygon, QFont, QFontMetrics, QBrush, \
    QPainterPath, QPainter, QToolButton, QLabel, QToolBar

from PyQt4.QtSvg import QGraphicsSvgItem

from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsRubberBand, QgsMapCanvasItem, QgsScaleComboBox, QgsLayerTreeMapCanvasBridge, \
                     QgsMapCanvasSnappingUtils
from qgis.core import QgsPalLabeling, QgsMapLayerRegistry, QgsMapLayer, QGis, QgsRectangle, QgsProject, QgsApplication, \
    QgsComposerScaleBar, \
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPoint, QgsCsException, QgsDistanceArea

from roam.gps_action import GPSAction, GPSMarker
from roam.projectparser import ProjectParser
from roam.maptools import MoveTool, InfoTool, EditTool, PointTool, TouchMapTool
from roam.api.events import RoamEvents
from roam.popupdialogs import PickActionDialog
from biglist import BigList
from roam.api import GPS, plugins

import roam.utils
import roam.config

import roam_style

try:
    from qgis.gui import QgsMapToolTouch

    PanTool = TouchMapTool
except ImportError:
    from qgis.gui import QgsMapToolPan

    PanTool = QgsMapToolPan


snapping = True


class SnappingUtils(QgsMapCanvasSnappingUtils):
    def prepareIndexStarting(self, count):
        print count

    def prepareIndexProgress(self, index):
        print index


class NorthArrow(QGraphicsSvgItem):
    def __init__(self, path, canvas, parent=None):
        super(NorthArrow, self).__init__(path, parent)
        self.canvas = canvas
        self.setTransformOriginPoint(self.boundingRect().width() / 2, self.boundingRect().height() / 2)

    def paint(self, painter, styleoptions, widget=None):
        angle = self._calc_north()
        if angle:
            self.setRotation(angle)
        super(NorthArrow, self).paint(painter, styleoptions, widget)

    def _calc_north(self):
        extent = self.canvas.extent()
        if self.canvas.layerCount() == 0 or extent.isEmpty():
            print "No layers or extent"
            return 0

        outcrs = self.canvas.mapSettings().destinationCrs()

        if outcrs.isValid() and not outcrs.geographicFlag():
            crs = QgsCoordinateReferenceSystem()
            crs.createFromOgcWmsCrs("EPSG:4326")

            transform = QgsCoordinateTransform(outcrs, crs)

            p1 = QgsPoint(extent.center())
            p2 = QgsPoint(p1.x(), p1.y() + extent.height() * 0.25)

            try:
                pp1 = transform.transform(p1)
                pp2 = transform.transform(p2)
            except QgsCsException:
                roam.utils.warning("North arrow. Error transforming.")
                return None

            area = QgsDistanceArea()
            area.setEllipsoid(crs.ellipsoidAcronym())
            area.setEllipsoidalMode(True)
            area.setSourceCrs(crs)
            distance, angle, _ = area.computeDistanceBearing(pp1, pp2)
            angle = math.degrees(angle)
            return angle
        else:
            return 0


class ScaleBarItem(QGraphicsItem):
    def __init__(self, canvas, parent=None):
        super(ScaleBarItem, self).__init__(parent)
        self.canvas = canvas
        self.realsize = 100
        black = QColor(Qt.black)
        black.setAlpha(150)
        white = QColor(Qt.white)
        white.setAlpha(150)
        blackpen = QPen(black, 4)
        whitepen = QPen(white, 8)
        self.pens = [whitepen, blackpen]
        self.whitepen = QPen(white, 1)
        self.blackbrush = QBrush(black)
        self.ticksize = 10
        self.fontsize = 15
        self.font = QFont()
        self.font.setPointSize(self.fontsize)
        self.font.setStyleHint(QFont.Times, QFont.PreferAntialias)
        self.font.setBold(True)
        self.metrics = QFontMetrics(self.font)

    def boundingRect(self):
        try:
            width, realsize, label, fontsize = self._calc_size()
            halfheight = (self.ticksize + fontsize[1]) / 2
            halfwidth = (width + fontsize[0]) / 2
            return QRectF(-halfwidth, -halfheight, halfwidth, halfheight)
        except ZeroDivisionError:
            return QRectF()

    def paint(self, painter, styleoptions, widget=None):
        try:
            width, realsize, label, fontsize = self._calc_size()
        except ZeroDivisionError:
            return

        mapunits = self.canvas.mapUnits()

        # painter.drawRect(self.boundingRect())
        array = QPolygon()
        canvasheight = self.canvas.height()
        canvaswidth = self.canvas.width()
        margin = 20
        originy = 0
        originx = 0

        self.setPos(margin, canvasheight - margin)

        x1, y1 = originx, originy
        x2, y2 = originx, originy + self.ticksize
        x3, y3 = originx + width, originy + self.ticksize
        midx, midy = originx + width / 2, originy + self.ticksize / 2
        x4, y4 = originx + width, originy

        for pen in self.pens:
            painter.setPen(pen)
            # Drwa the scale bar
            painter.drawLine(x1, y1, x2, y2)
            painter.drawLine(x2, y2, x3, y3)
            painter.drawLine(x3, y3, x4, y4)
            painter.drawLine(midx, midy, midx, y1)

        # Draw the text
        fontwidth = self.metrics.width("0")
        fontheight = self.metrics.height()
        fontheight /= 2
        fontwidth /= 2
        path = QPainterPath()
        point = QPointF(x1 - fontwidth, y1 - fontheight)
        path.addText(point, self.font, "0")
        painter.setPen(self.whitepen)
        painter.setBrush(self.blackbrush)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setFont(self.font)
        painter.drawPath(path)

        fontwidth = self.metrics.width(label)
        fontheight = self.metrics.height()
        fontheight /= 2
        fontwidth /= 2
        point = QPointF(x4 - fontwidth, y4 - fontheight)
        path.addText(point, self.font, label)
        painter.drawPath(path)

    def _calc_size(self):
        realSize = self.realsize
        canvaswidth = self.canvas.width()
        mapunitsperpixel = abs(self.canvas.mapUnitsPerPixel())
        mapunits = self.canvas.mapUnits()
        prefered_units = roam.config.settings.get("prefer_units", "meters")
        newunits = QGis.fromLiteral(prefered_units, QGis.Meters)
        mapunitsperpixel *= QGis.fromUnitToUnitFactor(mapunits, newunits)
        mapunits = newunits

        # Convert the real distance into pixels
        barwidth = realSize / mapunitsperpixel

        if barwidth < 30:
            barwidth = canvaswidth / 4

        while barwidth > canvaswidth / 3:
            barwidth /= 3

        realSize = barwidth * mapunitsperpixel

        # Round
        powerof10 = math.floor(math.log10(realSize))
        scaler = math.pow(10.0, powerof10)
        realSize = round(realSize / scaler) * scaler
        barwidth = realSize / mapunitsperpixel
        label, realSize = self._label_size(mapunits, realSize)
        metrics = QFontMetrics(self.font)
        fontwidth = metrics.width(label)
        fontheight = metrics.height()

        sizelabel = QLocale.system().toString(realSize)
        sizelabel = "{} {}".format(sizelabel, label)

        barwidth = self._adjust_bar_size(barwidth, mapunits)
        barwidth = barwidth + fontwidth

        return barwidth, realSize, sizelabel, (fontwidth, fontheight)

    def _label_size(self, unit, currentsize):
        if unit == QGis.Meters:
            if currentsize > 1000:
                return "km", currentsize / 1000
            elif currentsize < 0.01:
                return "mm", currentsize * 1000
            elif currentsize < 0.1:
                return "cm", currentsize * 100
            else:
                return "m", currentsize
        elif unit == QGis.Feet:
            print currentsize
            if currentsize > 5280.0:
                return "miles", currentsize / 5000
            elif currentsize == 5280.0:
                return "mile", currentsize / 5000
            elif currentsize < 1:
                return "inches", currentsize * 10
            elif currentsize == 1.0:
                return "foot", currentsize
            else:
                return "feet", currentsize
        elif unit == QGis.Degrees:
            if currentsize == 1.0:
                return "degree", currentsize
            else:
                return "degrees", currentsize
        else:
            return str(unit), currentsize

    def _adjust_bar_size(self, barsize, unit):
        if unit == QGis.Feet:
            if barsize > 5280.0 or barsize == 5280.0:
                return (barsize * 5290) / 5000
            elif barsize < 1:
                return (barsize * 10) / 12

        return barsize


class CurrentSelection(QgsRubberBand):
    """
    Position marker for the current location in the viewer.
    """

    class AniObject(QObject):
        def __init__(self, band):
            super(CurrentSelection.AniObject, self).__init__()
            self.color = QColor()

        @pyqtProperty(int)
        def alpha(self):
            return self.color.alpha()

        @alpha.setter
        def alpha(self, value):
            self.color.setAlpha(value)

    def __init__(self, canvas):
        super(CurrentSelection, self).__init__(canvas)
        self.outline = QgsRubberBand(canvas)
        self.outline.setBrushStyle(Qt.NoBrush)
        self.outline.setWidth(5)
        self.outline.setIconSize(30)
        self.aniobject = CurrentSelection.AniObject(self)
        self.anim = QPropertyAnimation(self.aniobject, "alpha")
        self.anim.setDuration(500)
        self.anim.setStartValue(50)
        self.anim.setEndValue(100)
        self.anim.valueChanged.connect(self.value_changed)

    def setOutlineColour(self, color):
        self.outline.setColor(color)

    def setToGeometry(self, geom, layer):
        super(CurrentSelection, self).setToGeometry(geom, layer)
        self.outline.setToGeometry(geom, layer)
        self.anim.stop()
        self.anim.start()

    def reset(self, geomtype=QGis.Line):
        super(CurrentSelection, self).reset(geomtype)
        self.outline.reset(geomtype)
        self.anim.stop()

    def value_changed(self, value):
        self.setColor(self.aniobject.color)
        self.update()

    def setColor(self, color):
        self.aniobject.color = color
        super(CurrentSelection, self).setColor(color)


from ui.ui_mapwidget import Ui_CanvasWidget


class MapWidget(Ui_CanvasWidget, QMainWindow):
    def __init__(self, parent=None):
        super(MapWidget, self).__init__(parent)
        self.setupUi(self)

        icon = roam_style.iconsize()
        self.projecttoolbar.setIconSize(QSize(icon, icon))

        self.firstshow = True
        self.layerbuttons = []
        self.editfeaturestack = []
        self.lastgpsposition = None
        self.project = None
        self.gps = None
        self.gpslogging = None
        self.selectionbands = defaultdict(partial(QgsRubberBand, self.canvas))

        self.bridge = QgsLayerTreeMapCanvasBridge(QgsProject.instance().layerTreeRoot(), self.canvas)
        self.bridge.setAutoSetupOnFirstLayer(False)
        QgsProject.instance().writeProject.connect(self.bridge.writeProject)
        QgsProject.instance().readProject.connect(self.bridge.readProject)

        # self.canvas.setInteractive(False)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)

        self.snapping = SnappingUtils(self.canvas, self)
        self.canvas.setSnappingUtils(self.snapping)
        QgsProject.instance().readProject.connect(self.snapping.readConfigFromProject)

        if hasattr(self.canvas, 'setParallelRenderingEnabled'):
            threadcount = QThread.idealThreadCount()
            threadcount = 2 if threadcount > 2 else 1
            QgsApplication.setMaxThreads(threadcount)
            self.canvas.setParallelRenderingEnabled(True)

        pal = QgsPalLabeling()
        self.canvas.mapRenderer().setLabelingEngine(pal)
        self.canvas.setFrameStyle(QFrame.NoFrame)

        self.editgroup = QActionGroup(self)
        self.editgroup.setExclusive(True)
        self.editgroup.addAction(self.actionPan)
        self.editgroup.addAction(self.actionZoom_In)
        self.editgroup.addAction(self.actionZoom_Out)
        self.editgroup.addAction(self.actionInfo)

        self.actionGPS = GPSAction(":/icons/gps", self.canvas, self)
        self.projecttoolbar.addAction(self.actionGPS)

        if roam.config.settings.get('north_arrow', False):
            self.northarrow = NorthArrow(":/icons/north", self.canvas)
            self.northarrow.setPos(10, 10)
            self.canvas.scene().addItem(self.northarrow)


        smallmode = roam.config.settings.get("smallmode", False)
        self.projecttoolbar.setSmallMode(smallmode)

        self.scalebar_enabled = roam.config.settings.get('scale_bar', False)
        if self.scalebar_enabled:
            self.scalebar = ScaleBarItem(self.canvas)
            self.canvas.scene().addItem(self.scalebar)

        self.projecttoolbar.setContextMenuPolicy(Qt.CustomContextMenu)

        gpsspacewidget = QWidget()
        gpsspacewidget.setMinimumWidth(30)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.topspaceraction = self.projecttoolbar.insertWidget(self.actionGPS, gpsspacewidget)

        self.dataentryselection = QAction(self.projecttoolbar)
        self.dataentryaction = self.projecttoolbar.insertAction(self.topspaceraction, self.dataentryselection)
        self.dataentryselection.triggered.connect(self.select_data_entry)

        self.marker = GPSMarker(self.canvas)
        self.marker.hide()

        self.currentfeatureband = CurrentSelection(self.canvas)
        self.currentfeatureband.setIconSize(30)
        self.currentfeatureband.setWidth(10)
        self.currentfeatureband.setColor(QColor(186, 93, 212, 50))
        self.currentfeatureband.setOutlineColour(QColor(186, 93, 212))

        self.gpsband = QgsRubberBand(self.canvas)
        self.gpsband.setColor(QColor(165, 111, 212, 75))
        self.gpsband.setWidth(5)

        RoamEvents.editgeometry.connect(self.queue_feature_for_edit)
        RoamEvents.selectioncleared.connect(self.clear_selection)
        RoamEvents.selectionchanged.connect(self.highlight_selection)
        RoamEvents.openfeatureform.connect(self.feature_form_loaded)
        RoamEvents.sync_complete.connect(self.refresh_map)
        RoamEvents.snappingChanged.connect(self.snapping_changed)

        self.snappingbutton = QToolButton()
        self.snappingbutton.setText("Snapping: On")
        self.snappingbutton.setAutoRaise(True)
        self.snappingbutton.pressed.connect(self.toggle_snapping)

        spacer = QWidget()
        spacer2 = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.scalewidget = QgsScaleComboBox()

        self.scalebutton = QToolButton()
        self.scalebutton.setAutoRaise(True)
        self.scalebutton.setMaximumHeight(self.statusbar.height())
        self.scalebutton.pressed.connect(self.selectscale)
        self.scalebutton.setText("Scale")

        self.scalelist = BigList(parent=self.canvas, centeronparent=True, showsave=False)
        self.scalelist.hide()
        self.scalelist.setlabel("Map Scale")
        self.scalelist.setmodel(self.scalewidget.model())
        self.scalelist.closewidget.connect(self.scalelist.close)
        self.scalelist.itemselected.connect(self.update_scale_from_item)
        self.scalelist.itemselected.connect(self.scalelist.close)

        self.positionlabel = QLabel('')
        self.gpslabel = QLabel("GPS: Not active")
        self.gpslabelposition = QLabel("")

        self.statusbar.addWidget(self.snappingbutton)
        self.statusbar.addWidget(spacer2)
        self.statusbar.addWidget(self.gpslabel)
        self.statusbar.addWidget(self.gpslabelposition)
        self.statusbar.addPermanentWidget(self.scalebutton)

        self.canvas.extentsChanged.connect(self.updatestatuslabel)
        self.canvas.scaleChanged.connect(self.updatestatuslabel)

        GPS.gpsposition.connect(self.update_gps_label)
        GPS.gpsdisconnected.connect(self.gps_disconnected)

        self.connectButtons()

    def clear_plugins(self):
        toolbars = self.findChildren(QToolBar)
        for toolbar in toolbars:
            if toolbar.property("plugin_toolbar"):
                toolbar.unload()
                self.removeToolBar(toolbar)
                toolbar.deleteLater()

    def add_plugins(self, pluginnames):
        for name in pluginnames:
            # Get the plugin
            try:
                plugin_mod = plugins.loaded_plugins[name]
            except KeyError:
                continue

            if not hasattr(plugin_mod, 'toolbars'):
                roam.utils.warning("No toolbars() function found in {}".format(name))
                continue

            toolbars = plugin_mod.toolbars()
            self.load_plugin_toolbars(toolbars)

    def load_plugin_toolbars(self, toolbars):
        for ToolBarClass in toolbars:
            toolbar = ToolBarClass(plugins.api, self)
            self.addToolBar(Qt.BottomToolBarArea, toolbar)
            toolbar.setProperty("plugin_toolbar", True)

    def snapping_changed(self, snapping):
        """
        Called when the snapping settings have changed. Updates the label in the status bar.
        :param snapping:
        """
        if snapping:
            self.snappingbutton.setText("Snapping: On")
        else:
            self.snappingbutton.setText("Snapping: Off")

    def toggle_snapping(self):
        """
        Toggle snapping on or off.
        """
        global snapping
        snap = not snapping
        snapping = snap
        RoamEvents.snappingChanged.emit(snapping)

    def selectscale(self):
        """
        Show the select scale widget.
        :return:
        """
        self.scalelist.show()

    def update_scale_from_item(self, index):
        """
        Update the canvas scale from the selected scale item.
        :param index: The index of the selected item.
        """
        scale, _ = self.scalewidget.toDouble(index.data(Qt.DisplayRole))
        self.canvas.zoomScale(1.0 / scale)

    def update_gps_label(self, position, gpsinfo):
        """
        Update the GPS label in the status bar with the GPS status.
        :param position: The current GPS position.
        :param gpsinfo: The current extra GPS information.
        """
        self.gpslabel.setText("GPS: PDOP <b>{0:.2f}</b> HDOP <b>{1:.2f}</b>    VDOP <b>{2:.2f}</b>".format(gpsinfo.pdop,
                                                                                        gpsinfo.hdop,
                                                                                        gpsinfo.vdop))

        places = roam.config.settings.get("gpsplaces", 8)
        self.gpslabelposition.setText("X <b>{x:.{places}f}</b> Y <b>{y:.{places}f}</b>".format(x = position.x(),
                                                                                      y = position.y(),
                                                                                      places=places))

    def gps_disconnected(self):
        """
        Called when the GPS is disconnected. Updates the label in the status bar with the message.
        :return:
        """
        self.gpslabel.setText("GPS Not Active")
        self.gpslabelposition.setText("")

    def zoom_to_feature(self, feature):
        box = feature.geometry().boundingBox()
        xmin, xmax, ymin, ymax = box.xMinimum(), box.xMaximum(), box.yMinimum(), box.yMaximum()
        xmin -= 5
        xmax += 5
        ymin -= 5
        ymax += 5
        box = QgsRectangle(xmin, ymin, xmax, ymax)
        self.canvas.setExtent(box)
        self.canvas.refresh()

    def updatestatuslabel(self, *args):
        """
        Update the status bar labels when the information has changed.
        """
        extent = self.canvas.extent()
        self.positionlabel.setText("Map Center: {}".format(extent.center().toString()))
        scale = 1.0 / self.canvas.scale()
        scale = self.scalewidget.toString(scale)
        self.scalebutton.setText(scale)

    def refresh_map(self):
        """
        Refresh the map
        """
        self.canvas.refresh()

    def updatescale(self):
        """
        Update the scale of the map with the current scale from the scale widget
        :return:
        """
        self.canvas.zoomScale(1.0 / self.scalewidget.scale())

    def init_qgisproject(self, doc):
        """
        Called when the project file is read for the firs time.
        :param doc: The XML doc.
        :return: The current canvas CRS
        :note: This method is old and needs to be refactored into something else.
        """
        return self.canvas.mapSettings().destinationCrs()

    def showEvent(self, *args, **kwargs):
        """
        Handle the show event of the of the map widget. We have to do a little hack here to make the QGIS map refresh.
        """
        if QGis.QGIS_VERSION_INT == 20200 and self.firstshow:
            self.canvas.refresh()
            self.canvas.repaint()
            self.firstshow = False

    def feature_form_loaded(self, form, feature, *args):
        """
        Called when the feature form is loaded.
        :param form: The Form object. Holds a reference to the forms layer.
        :param feature: The current capture feature
        """
        self.currentfeatureband.setToGeometry(feature.geometry(), form.QGISLayer)

    def highlight_selection(self, results):
        """
        Highlight the selection on the canvas.  This updates all selected objects based on the result set.
        :param results: A dict-of-list of layer-features.
        """
        self.clear_selection()
        for layer, features in results.iteritems():
            band = self.selectionbands[layer]
            band.setColor(QColor(255, 0, 0))
            band.setIconSize(25)
            band.setWidth(5)
            band.setBrushStyle(Qt.NoBrush)
            band.reset(layer.geometryType())
            band.setZValue(self.currentfeatureband.zValue() - 1)
            for feature in features:
                band.addGeometry(feature.geometry(), layer)
        self.canvas.update()

    def highlight_active_selection(self, layer, feature, features):
        """
        Update the current active selected feature.
        :param layer: The layer of the active feature.
        :param feature: The active feature.
        :param features: The other features in the set to show as non active selection.
        :return:
        """
        self.clear_selection()
        self.highlight_selection({layer: features})
        self.currentfeatureband.setToGeometry(feature.geometry(), layer)
        self.canvas.update()

    def clear_selection(self):
        """
        Clear the selection from the canvas.   Resets all selection rubbber bands.
        :return:
        """
        # Clear the main selection rubber band
        self.canvas.scene().update()
        self.currentfeatureband.reset()
        # Clear the rest
        for band in self.selectionbands.itervalues():
            band.reset()

        self.canvas.update()
        self.editfeaturestack = []

    def queue_feature_for_edit(self, form, feature):
        """
        Push a feature on the edit stack so the feature can have the geometry edited.
        :note: This is a big hack and I don't like it!
        :param form: The form for the current feature
        :param feature: The active feature.
        """
        def trigger_default_action():
            for action in self.projecttoolbar.actions():
                if action.property('dataentry') and action.isdefault:
                    action.trigger()
                    self.canvas.mapTool().setEditMode(True, feature.geometry())
                    break

        self.editfeaturestack.append((form, feature))
        self.load_form(form)
        trigger_default_action()

    def clear_temp_objects(self):
        """
        Clear all temp objects from the canvas.
        :return:
        """
        def clear_tool_band():
            """
            Clear the rubber band of the active tool if it has one
            """
            tool = self.canvas.mapTool()
            try:
                tool.clearBand()
            except AttributeError:
                # No clearBand method found, but that's cool.
                pass

        self.currentfeatureband.reset()
        clear_tool_band()

    def settings_updated(self, settings):
        """
        Called when the settings have been updated in the Roam config.
        :param settings: A dict of the settings.
        """
        self.actionGPS.updateGPSPort()
        gpslogging = settings.get('gpslogging', True)
        if self.gpslogging:
            self.gpslogging.logging = gpslogging

    def set_gps(self, gps, logging):
        """
        Set the GPS for the map widget.  Connects GPS signals
        """
        self.gps = gps
        self.gpslogging = logging
        self.gps.gpsposition.connect(self.gps_update_canvas)
        self.gps.firstfix.connect(self.gps_first_fix)
        self.gps.gpsdisconnected.connect(self.gps_disconnected)

    def gps_update_canvas(self, position, gpsinfo):
        """
        Updates the map canvas based on the GPS position.  By default if the GPS is outside the canvas
        extent the canvas will move to center on the GPS.  Can be turned off in settings.
        :param postion: The current GPS position.
        :param gpsinfo: The extra GPS information
        """
        # Recenter map if we go outside of the 95% of the area
        if self.gpslogging.logging:
            self.gpsband.addPoint(position)
            self.gpsband.show()

        if roam.config.settings.get('gpscenter', True):
            if not self.lastgpsposition == position:
                self.lastposition = position
                rect = QgsRectangle(position, position)
                extentlimt = QgsRectangle(self.canvas.extent())
                extentlimt.scale(0.95)

                if not extentlimt.contains(position):
                    self.zoom_to_location(position)

        self.marker.show()
        self.marker.setCenter(position, gpsinfo)

    def gps_first_fix(self, postion, gpsinfo):
        """
        Called the first time the GPS gets a fix.  If set this will zoom to the GPS after the first fix
        :param postion: The current GPS position.
        :param gpsinfo: The extra GPS information
        """
        zoomtolocation = roam.config.settings.get('gpszoomonfix', True)
        if zoomtolocation:
            self.canvas.zoomScale(1000)
            self.zoom_to_location(postion)

    def zoom_to_location(self, position):
        """
        Zoom to ta given position on the map..
        """
        rect = QgsRectangle(position, position)
        self.canvas.setExtent(rect)
        self.canvas.refresh()

    def gps_disconnected(self):
        """
        Called when the GPS is disconnected
        """
        self.marker.hide()

    def select_data_entry(self):
        """
        Open the form selection widget to allow the user to pick the active capture form.
        """
        def showformerror(form):
            pass

        def actions():
            for form in self.project.forms:
                if not self.form_valid_for_capture(form):
                    continue

                action = form.createuiaction()
                valid, failreasons = form.valid
                if not valid:
                    roam.utils.warning("Form {} failed to load".format(form.label))
                    roam.utils.warning("Reasons {}".format(failreasons))
                    action.triggered.connect(partial(showformerror, form))
                else:
                    action.triggered.connect(partial(self.load_form, form))
                yield action

        formpicker = PickActionDialog(msg="Select data entry form", wrap=5)
        formpicker.addactions(actions())
        formpicker.exec_()

    def project_loaded(self, project):
        """
        Called when the project is loaded. Main entry point for a loade project.
        :param project: The Roam project that has been loaded.
        """
        self.project = project
        self.actionPan.trigger()
        firstform = self.first_capture_form()
        if firstform:
            self.load_form(firstform)
            self.dataentryselection.setVisible(True)
        else:
            self.dataentryselection.setVisible(False)

        # Enable the raster layers button only if the project contains a raster layer.
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        hasrasters = any(layer.type() == QgsMapLayer.RasterLayer for layer in layers)
        self.actionRaster.setEnabled(hasrasters)
        self.defaultextent = self.canvas.extent()
        roam.utils.info("Extent: {}".format(self.defaultextent.toString()))

        self.infoTool.selectionlayers = project.selectlayersmapping()

        self.canvas.refresh()

        projectscales, _ = QgsProject.instance().readBoolEntry("Scales", "/useProjectScales")
        if projectscales:
            projectscales, _ = QgsProject.instance().readListEntry("Scales", "/ScalesList")

            self.scalewidget.updateScales(projectscales)
        else:
            scales = ["1:50000", "1:25000", "1:10000", "1:5000",
                      "1:2500", "1:1000", "1:500", "1:250", "1:200", "1:100"]
            scales = roam.config.settings.get('scales', scales)
            self.scalewidget.updateScales(scales)

        if self.scalebar_enabled:
            self.scalebar.update()

        self.actionPan.toggle()
        self.clear_plugins()
        self.add_plugins(project.enabled_plugins)

    def setMapTool(self, tool, *args):
        """
        Set the active map tool in the canvas.
        :param tool: The QgsMapTool to set.
        """
        if tool == self.canvas.mapTool():
            return

        if hasattr(tool, "setSnapping"):
            tool.setSnapping(snapping)
        self.canvas.setMapTool(tool)

    def connectButtons(self):
        """
        Connect the default buttons in the interface. Zoom, pan, etc
        """
        def connectAction(action, tool):
            action.toggled.connect(partial(self.setMapTool, tool))

        def cursor(name):
            pix = QPixmap(name)
            pix = pix.scaled(QSize(24, 24))
            return QCursor(pix)

        self.zoomInTool = QgsMapToolZoom(self.canvas, False)
        self.zoomOutTool = QgsMapToolZoom(self.canvas, True)
        self.panTool = PanTool(self.canvas)
        self.infoTool = InfoTool(self.canvas)

        self.infoTool.setAction(self.actionInfo)
        self.zoomInTool.setAction(self.actionZoom_In)
        self.zoomOutTool.setAction(self.actionZoom_Out)
        self.panTool.setAction(self.actionPan)

        connectAction(self.actionZoom_In, self.zoomInTool)
        connectAction(self.actionZoom_Out, self.zoomOutTool)
        connectAction(self.actionPan, self.panTool)
        connectAction(self.actionInfo, self.infoTool)

        self.zoomInTool.setCursor(cursor(':/icons/in'))
        self.zoomOutTool.setCursor(cursor(':/icons/out'))
        self.infoTool.setCursor(cursor(':/icons/select'))

        self.actionRaster.triggered.connect(self.toggleRasterLayers)
        self.actionHome.triggered.connect(self.homeview)

    def homeview(self):
        """
        Zoom the mapview canvas to the extents the project was opened at i.e. the
        default extent.
        """
        self.canvas.setExtent(self.defaultextent)
        self.canvas.refresh()

    def form_valid_for_capture(self, form):
        """
        Check if the given form is valid for capture.
        :param form: The form to check.
        :return: True if valid form for capture
        """
        return form.has_geometry and self.project.layer_can_capture(form.QGISLayer)

    def first_capture_form(self):
        """
        Return the first valid form for capture.
        """
        for form in self.project.forms:
            if self.form_valid_for_capture(form):
                return form

    def load_form(self, form):
        """
        Load the given form so it's the active one for capture
        :param form: The form to load
        """
        self.clearCaptureTools()
        self.dataentryselection.setIcon(QIcon(form.icon))
        self.dataentryselection.setText(form.icontext)
        self.create_capture_buttons(form)

    def create_capture_buttons(self, form):
        """
        Create the capture buttons in the toolbar for the given form.
        :param form: The active form.
        """
        layer = form.QGISLayer
        tool = form.getMaptool()(self.canvas)
        for action in tool.actions:
            # Create the action here.
            if action.ismaptool:
                action.toggled.connect(partial(self.setMapTool, tool))

            # Set the action as a data entry button so we can remove it later.
            action.setProperty("dataentry", True)
            self.editgroup.addAction(action)
            self.layerbuttons.append(action)
            self.projecttoolbar.insertAction(self.topspaceraction, action)
            action.setChecked(action.isdefault)

        if hasattr(tool, 'geometryComplete'):
            add = partial(self.add_new_feature, form)
            tool.geometryComplete.connect(add)
        else:
            tool.finished.connect(self.openForm)

        tool.error.connect(self.show_invalid_geometry_message)

    def show_invalid_geometry_message(self, message):
        RoamEvents.raisemessage("Invalid geometry capture", message, level=RoamEvents.CRITICAL)

    def add_new_feature(self, form, geometry):
        """
        Add a new new feature to the given layer
        """
        # TODO Extract into function.
        # NOTE This function is doing too much, acts as add and also edit.
        layer = form.QGISLayer
        if layer.geometryType() in [QGis.WKBMultiLineString, QGis.WKBMultiPoint, QGis.WKBMultiPolygon]:
            geometry.convertToMultiType()

        try:
            form, feature = self.editfeaturestack.pop()
            self.editfeaturegeometry(form, feature, newgeometry=geometry)
            return
        except IndexError:
            pass

        feature = form.new_feature(geometry=geometry)
        RoamEvents.load_feature_form(form, feature, editmode=False)

    def editfeaturegeometry(self, form, feature, newgeometry):
        # TODO Extract into function.
        layer = form.QGISLayer
        layer.startEditing()
        feature.setGeometry(newgeometry)
        layer.updateFeature(feature)
        saved = layer.commitChanges()
        if not saved:
            map(roam.utils.error, layer.commitErrors())
        self.canvas.refresh()
        self.currentfeatureband.setToGeometry(feature.geometry(), layer)
        RoamEvents.editgeometry_complete.emit(form, feature)
        self.canvas.mapTool().setEditMode(False, None)

    def clearCaptureTools(self):
        """
        Clear the capture tools from the toolbar.
        :return: True if the capture button was active at the time of clearing.
        """
        captureselected = False
        for action in self.projecttoolbar.actions():
            if action.objectName() == "capture" and action.isChecked():
                captureselected = True

            if action.property('dataentry'):
                self.projecttoolbar.removeAction(action)
        return captureselected

    def toggleRasterLayers(self):
        """
        Toggle all raster layers on or off.
        """
        # Freeze the canvas to save on UI refresh
        self.canvas.freeze()
        tree = QgsProject.instance().layerTreeRoot()
        for node in tree.findLayers():
            if node.layer().type() == QgsMapLayer.RasterLayer:
                if node.isVisible() == Qt.Checked:
                    state = Qt.Unchecked
                else:
                    state = Qt.Checked
                node.setVisible(state)

        self.canvas.freeze(False)
        self.canvas.refresh()

    def cleanup(self):
        """
        Clean up when the project has changed.
        :return:
        """
        self.bridge.clear()
        self.gpsband.reset()
        self.gpsband.hide()
        self.clear_selection()
        self.clear_temp_objects()
        self.clearCaptureTools()
        self.canvas.freeze()
        self.canvas.clear()
        self.canvas.freeze(False)
        for action in self.layerbuttons:
            self.editgroup.removeAction(action)
