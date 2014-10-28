from functools import partial
from collections import defaultdict

from PyQt4.QtCore import Qt, pyqtSignal, QSize
from PyQt4.QtGui import QActionGroup, QFrame, QWidget, QSizePolicy, \
                        QAction, QPixmap, QCursor, QIcon, QColor, QMainWindow

from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsRubberBand
from qgis.core import QgsPalLabeling, QgsMapLayerRegistry, QgsMapLayer, QgsFeature, QGis, QgsRectangle, QgsProject

from roam.gps_action import GPSAction, GPSMarker
from roam.projectparser import ProjectParser
from roam.maptools import MoveTool, InfoTool, EditTool, PointTool, TouchMapTool
from roam.api.events import RoamEvents
from roam.popupdialogs import PickActionDialog

import roam.utils
import roam.config

try:
    from qgis.gui import QgsMapToolTouch
    PanTool = TouchMapTool
except ImportError:
    from qgis.gui import QgsMapToolPan
    PanTool = QgsMapToolPan

from ui.ui_mapwidget import Ui_CanvasWidget

class MapWidget(Ui_CanvasWidget, QMainWindow):
    def __init__(self, parent=None):
        super(MapWidget, self).__init__(parent)
        self.setupUi(self)

        self.firstshow = True
        self.layerbuttons = []
        self.editfeaturestack = []
        self.lastgpsposition = None
        self.project = None
        self.gps = None
        self.gpslogging = None
        self.selectionbands = defaultdict(partial(QgsRubberBand, self.canvas))

        self.canvas.setInteractive(False)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)

        if hasattr(self.canvas, 'setParallelRenderingEnabled'):
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

        gpsspacewidget= QWidget()
        gpsspacewidget.setMinimumWidth(30)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.topspaceraction = self.projecttoolbar.insertWidget(self.actionGPS, gpsspacewidget)

        self.dataentryselection = QAction(self.projecttoolbar)
        self.dataentryaction = self.projecttoolbar.insertAction(self.topspaceraction, self.dataentryselection)
        self.dataentryselection.triggered.connect(self.select_data_entry)

        self.marker = GPSMarker(self.canvas)
        self.marker.hide()

        self.currentfeatureband = QgsRubberBand(self.canvas)
        self.currentfeatureband.setIconSize(20)
        self.currentfeatureband.setWidth(10)
        self.currentfeatureband.setColor(QColor(186, 93, 212, 76))

        self.gpsband = QgsRubberBand(self.canvas)
        self.gpsband.setColor(QColor(0, 0, 212, 76))
        self.gpsband.setWidth(5)

        RoamEvents.editgeometry.connect(self.queue_feature_for_edit)
        RoamEvents.selectioncleared.connect(self.clear_selection)
        RoamEvents.selectionchanged.connect(self.highlight_selection)
        RoamEvents.openfeatureform.connect(self.feature_form_loaded)

        self.connectButtons()

    def init_qgisproject(self, doc):
        parser = ProjectParser(doc)
        canvasnode = parser.canvasnode
        self.canvas.freeze()
        self.canvas.mapRenderer().readXML(canvasnode)
        self.canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(self.canvaslayers)
        red = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorRedPart", 255 )[0]
        green = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorGreenPart", 255 )[0]
        blue = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorBluePart", 255 )[0]
        color = QColor(red, green, blue)
        self.canvas.setCanvasColor(color)
        self.canvas.updateScale()
        self.canvas.freeze(False)
        return self.canvas.mapRenderer().destinationCrs()

    def showEvent(self, *args, **kwargs):
        if QGis.QGIS_VERSION_INT == 20200 and self.firstshow:
            self.canvas.refresh()
            self.canvas.repaint()
            self.firstshow = False

    def feature_form_loaded(self, form, feature, *args):
        self.currentfeatureband.setToGeometry(feature.geometry(), form.QGISLayer)

    def highlight_selection(self, results):
        self.clear_selection()
        for layer, features in results.iteritems():
            band = self.selectionbands[layer]
            band.setColor(QColor(255, 0, 0, 200))
            band.setIconSize(20)
            band.setWidth(2)
            band.setBrushStyle(Qt.NoBrush)
            band.reset(layer.geometryType())
            for feature in features:
                band.addGeometry(feature.geometry(), layer)
        self.canvas.update()

    def highlight_active_selection(self, layer, feature, features):
        self.clear_selection()
        self.highlight_selection({layer: features})
        self.currentfeatureband.setToGeometry(feature.geometry(), layer)
        self.canvas.update()

    def clear_selection(self):
        # Clear the main selection rubber band
        self.canvas.scene().update()
        self.currentfeatureband.reset()
        # Clear the rest
        for band in self.selectionbands.itervalues():
            band.reset()

        self.canvas.update()
        self.editfeaturestack = []

    def queue_feature_for_edit(self, form, feature):
        def trigger_default_action():
            for action in self.projecttoolbar.actions():
                if action.property('dataentry') and action.isdefault:
                    action.trigger()
                    break

        self.editfeaturestack.append((form, feature))
        self.load_form(form)
        trigger_default_action()

    def clear_temp_objects(self):
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
        self.actionGPS.updateGPSPort()
        gpslogging = settings.get('gpslogging', True)
        if self.gpslogging:
            self.gpslogging.logging = gpslogging

    def set_gps(self, gps, logging):
        self.gps = gps
        self.gpslogging = logging
        self.gps.gpsposition.connect(self.gps_update_canvas)
        self.gps.firstfix.connect(self.gps_first_fix)
        self.gps.gpsdisconnected.connect(self.gps_disconnected)

    def gps_update_canvas(self, position, gpsinfo):
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
        self.marker.setCenter(position)

    def gps_first_fix(self, postion, gpsinfo):
        zoomtolocation = roam.config.settings.get('gpszoomonfix', True)
        if zoomtolocation:
            self.canvas.zoomScale(1000)
            self.zoom_to_location(postion)

    def zoom_to_location(self, position):
        rect = QgsRectangle(position, position)
        self.canvas.setExtent(rect)
        self.canvas.refresh()

    def gps_disconnected(self):
        self.marker.hide()

    def select_data_entry(self):
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

        formpicker = PickActionDialog(msg="Select data entry form")
        formpicker.addactions(actions())
        formpicker.exec_()

    def project_loaded(self, project):
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

        self.canvas.freeze(False)
        self.canvas.refresh()

    def setMapTool(self, tool, *args):
        self.canvas.setMapTool(tool)

    def connectButtons(self):
        def connectAction(action, tool):
            action.toggled.connect(partial(self.setMapTool, tool))

        def cursor(name):
            pix = QPixmap(name)
            pix = pix.scaled(QSize(24,24))
            return QCursor(pix)

        self.zoomInTool = QgsMapToolZoom(self.canvas, False)
        self.zoomOutTool = QgsMapToolZoom(self.canvas, True)
        self.panTool = PanTool(self.canvas)
        self.infoTool = InfoTool(self.canvas)

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
        return form.has_geometry and self.project.layer_can_capture(form.QGISLayer)

    def first_capture_form(self):
        for form in self.project.forms:
            if self.form_valid_for_capture(form):
                return form

    def load_form(self, form):
        self.clearCapatureTools()
        self.dataentryselection.setIcon(QIcon(form.icon))
        self.dataentryselection.setText(form.icontext)
        self.create_capture_buttons(form)

    def create_capture_buttons(self, form):
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
            tool.error.connect(partial(self.showUIMessage, form.label))

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

        layer = form.QGISLayer
        fields = layer.pendingFields()

        feature = QgsFeature(fields)
        feature.setGeometry(geometry)

        for index in xrange(fields.count()):
            pkindexes = layer.dataProvider().pkAttributeIndexes()
            if index in pkindexes and layer.dataProvider().name() == 'spatialite':
                continue

            value = layer.dataProvider().defaultValue(index)
            feature[index] = value

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

    def clearCapatureTools(self):
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
        if not self.canvaslayers:
            return

        #Freeze the canvas to save on UI refresh
        self.canvas.freeze()
        for layer in self.canvaslayers:
            if layer.layer().type() == QgsMapLayer.RasterLayer:
                layer.setVisible(not layer.isVisible())
                # Really!? We have to reload the whole layer set every time?
            # WAT?
        self.canvas.setLayerSet(self.canvaslayers)
        self.canvas.freeze(False)
        self.canvas.refresh()

    def cleanup(self):
        self.gpsband.reset()
        self.gpsband.hide()
        self.clear_selection()
        self.clear_temp_objects()
        self.clearCapatureTools()
        self.canvas.freeze()
        self.canvas.clear()
        self.canvas.freeze(False)
        for action in self.layerbuttons:
            self.editgroup.removeAction(action)
