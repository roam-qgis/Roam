from functools import partial
from collections import defaultdict
import getpass
import traceback
import os


from PyQt4.QtCore import Qt, QFileInfo, QDir, QSize
from PyQt4.QtGui import (QActionGroup,
                        QApplication,
                        QWidget,
                        QSizePolicy,
                        QLabel,
                        QApplication,
                        QPixmap,
                        QColor,
                        QStandardItemModel,
                        QStandardItem,
                        QIcon,
                        QComboBox,
                        QAction,
                        QCursor, QFrame, QDesktopServices, QToolButton, QPushButton)
from qgis.core import (QgsProjectBadLayerHandler,
                        QgsPalLabeling,
                        QgsMapLayerRegistry,
                        QgsProject,
                        QgsMapLayer,
                        QgsFeature,
                        QgsFields,
                        QgsGeometry,
                        QgsRectangle, QGis)
from qgis.gui import (QgsMessageBar,
                        QgsMapToolZoom,
                        QgsMapToolTouch,
                        QgsRubberBand,
                        QgsMapCanvas)


from roam.gps_action import GPSAction, GPSMarker
from roam.dataentrywidget import DataEntryWidget
from roam.listmodulesdialog import ProjectsWidget
from roam.settingswidget import SettingsWidget
from roam.projectparser import ProjectParser
from roam.project import Project, NoMapToolConfigured, ErrorInMapTool
from roam.maptools import MoveTool, InfoTool, EditTool, PointTool, TouchMapTool
from roam.infodock import InfoDock
from roam.syncwidget import SyncWidget
from roam.helpviewdialog import HelpPage
from roam.biglist import BigList
from roam.popupdialogs import PickActionDialog
from roam.imageviewerwidget import ImageViewer
from roam.gpswidget import GPSWidget
from roam.api import RoamEvents, GPS
from roam.ui import ui_mainwindow
from PyQt4.QtGui import QMainWindow


import roam.messagebaritems
import roam.utils
import roam.htmlviewer
import roam.api.featureform
import roam.config


class BadLayerHandler(QgsProjectBadLayerHandler):
    """
    Handler class for any layers that fail to load when
    opening the project.
    """

    def __init__(self, callback):
        """
            callback - Any bad layers are passed to the callback so it
            can do what it wills with them
        """
        super(BadLayerHandler, self).__init__()
        self.callback = callback

    def handleBadLayers(self, domNodes, domDocument):
        layers = [node.namedItem("layername").toElement().text() for node in domNodes]
        self.callback(layers)


class MainWindow(ui_mainwindow.Ui_MainWindow, QMainWindow):
    """
    Main application window
    """

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.canvaslayers = []
        self.layerbuttons = []
        self.project = None
        self.selectionbands = defaultdict(partial(QgsRubberBand, self.canvas))
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.bar = roam.messagebaritems.MessageBar(self.centralwidget)

        self.actionMap.setVisible(False)
        self.actionLegend.setVisible(False)

        pal = QgsPalLabeling()
        self.canvas.mapRenderer().setLabelingEngine(pal)
        self.canvas.setFrameStyle(QFrame.NoFrame)

        self.menuGroup = QActionGroup(self)
        self.menuGroup.setExclusive(True)
        self.menuGroup.addAction(self.actionMap)
        self.menuGroup.addAction(self.actionDataEntry)
        self.menuGroup.addAction(self.actionLegend)
        self.menuGroup.addAction(self.actionProject)
        self.menuGroup.addAction(self.actionSync)
        self.menuGroup.addAction(self.actionSettings)
        self.menuGroup.addAction(self.actionGPS)
        self.menuGroup.triggered.connect(self.updatePage)

        self.editgroup = QActionGroup(self)
        self.editgroup.setExclusive(True)
        self.editgroup.addAction(self.actionPan)
        self.editgroup.addAction(self.actionZoom_In)
        self.editgroup.addAction(self.actionZoom_Out)
        self.editgroup.addAction(self.actionInfo)

        self.actionLegend.triggered.connect(self.updatelegend)

        self.actionGPS = GPSAction(":/icons/gps", self.canvas, self)
        self.projecttoolbar.addAction(self.actionGPS)

        self.projectwidget.requestOpenProject.connect(self.loadProject)
        QgsProject.instance().readProject.connect(self._readProject)

        self.gpswidget.setgps(GPS)

        self.actionSettings.toggled.connect(self.settingswidget.populateControls)
        self.actionSettings.toggled.connect(self.settingswidget.readSettings)
        self.settingswidget.settingsupdated.connect(self.settingsupdated)

        self.dataentrywidget = DataEntryWidget(self.canvas, self.bar)
        self.widgetpage.layout().addWidget(self.dataentrywidget)

        self.dataentrywidget.rejected.connect(self.formrejected)
        self.dataentrywidget.featuresaved.connect(self.featureSaved)
        self.dataentrywidget.featuredeleted.connect(self.featuredeleted)
        self.dataentrywidget.failedsave.connect(self.failSave)
        self.dataentrywidget.helprequest.connect(self.showhelp)

        def createSpacer(width=0, height=0):
            widget = QWidget()
            widget.setMinimumWidth(width)
            widget.setMinimumHeight(height)
            return widget

        gpsspacewidget = createSpacer(30)
        sidespacewidget = createSpacer(30)
        sidespacewidget2 = createSpacer(height=20)

        sidespacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sidespacewidget2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.topspaceraction = self.projecttoolbar.insertWidget(self.actionGPS, gpsspacewidget)

        def createlabel(text):
            style = """
                QLabel {
                        color: #706565;
                        font: 14px "Calibri" ;
                        }"""
            label = QLabel(text)
            label.setStyleSheet(style)

            return label

        self.projectlabel = createlabel("Project: {project}")
        self.userlabel = createlabel("User: {user}".format(user=getpass.getuser()))
        self.positionlabel = createlabel('')
        self.gpslabel = createlabel("GPS: Not active")
        self.statusbar.addWidget(self.projectlabel)
        self.statusbar.addWidget(self.userlabel)
        spacer = createSpacer()
        spacer2 = createSpacer()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.statusbar.addWidget(spacer)
        self.statusbar.addWidget(self.positionlabel)
        self.statusbar.addWidget(spacer2)
        self.statusbar.addWidget(self.gpslabel)

        self.menutoolbar.insertWidget(self.actionQuit, sidespacewidget2)
        self.menutoolbar.insertWidget(self.actionProject, sidespacewidget)

        self.panels = []

        self.connectButtons()

        self.currentfeatureband = QgsRubberBand(self.canvas)
        self.currentfeatureband.setIconSize(20)
        self.currentfeatureband.setWidth(10)
        self.currentfeatureband.setColor(QColor(186, 93, 212, 76))

        self.canvas_page.layout().insertWidget(0, self.projecttoolbar)
        self.dataentryselection = QAction(self.projecttoolbar)
        self.dataentryaction = self.projecttoolbar.insertAction(self.topspaceraction, self.dataentryselection)
        self.dataentryselection.triggered.connect(self.selectdataentry)

        self.centralwidget.layout().addWidget(self.statusbar)

        self.actionGPSFeature.setProperty('dataentry', True)

        self.infodock = InfoDock(self.canvas)
        self.infodock.featureupdated.connect(self.highlightfeature)
        self.infodock.hide()
        self.hidedataentry()
        self.canvas.extentsChanged.connect(self.updatestatuslabel)

        RoamEvents.openimage.connect(self.openimage)
        RoamEvents.openurl.connect(self.viewurl)
        RoamEvents.openfeatureform.connect(self.openForm)
        RoamEvents.openkeyboard.connect(self.openkeyboard)
        RoamEvents.selectioncleared.connect(self.clearselection)
        RoamEvents.editgeometry.connect(self.addforedit)
        RoamEvents.editgeometry_complete.connect(self.on_geometryedit)
        RoamEvents.onShowMessage.connect(self.showUIMessage)

        GPS.gpspostion.connect(self.updatecanvasfromgps)
        GPS.firstfix.connect(self.gpsfirstfix)
        GPS.gpsdisconnected.connect(self.gpsdisconnected)

        self.lastgpsposition = None
        self.marker = GPSMarker(self.canvas)
        self.marker.hide()

        self.legendpage.showmap.connect(self.showmap)

        self.editfeaturestack = []
        self.currentselection = {}

    def showUIMessage(self, label, message, level=QgsMessageBar.INFO, time=0, extra=''):
        self.bar.pushMessage(label, message, level, duration=time, extrainfo=extra)

    def addforedit(self, form, feature):
        self.editfeaturestack.append((form, feature))
        self.loadform(form)
        actions = self.getcaptureactions()
        for action in actions:
            if action.isdefault:
                action.trigger()
                break

    def updatelegend(self):
        self.legendpage.updatelegend(self.canvas)
        layers = self.project.legendlayersmapping().values()
        self.legendpage.updateitems(layers)

    def gpsfirstfix(self, postion, gpsinfo):
        zoomtolocation = roam.config.settings.get('gpszoomonfix', True)
        if zoomtolocation:
            self.canvas.zoomScale(1000)

    def updatecanvasfromgps(self, position, gpsinfo):
        # Recenter map if we go outside of the 95% of the area
        if not self.lastgpsposition == position:
            self.lastposition = position
            rect = QgsRectangle(position, position)
            extentlimt = QgsRectangle(self.canvas.extent())
            extentlimt.scale(0.95)

            if not extentlimt.contains(position):
                self.canvas.setExtent(rect)
                self.canvas.refresh()

        self.marker.show()
        self.marker.setCenter(position)
        self.gpslabel.setText("GPS: PDOP {}   HDOP {}    VDOP {}".format(gpsinfo.pdop,
                                                                        gpsinfo.hdop,
                                                                        gpsinfo.vdop))

    def gpsdisconnected(self):
        self.marker.hide()
        self.gpslabel.setText("GPS Not Active")

    def openkeyboard(self):
        if roam.config.settings.get('keyboard', True):
            cmd = r'C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe'
            os.startfile(cmd)

    def selectdataentry(self):
        forms = self.project.forms
        formpicker = PickActionDialog(msg="Select data entry form")
        for form in forms:
            action = form.createuiaction()
            valid, failreasons = form.valid
            if not valid:
                roam.utils.warning("Form {} failed to load".format(form.label))
                roam.utils.warning("Reasons {}".format(failreasons))
                action.triggered.connect(partial(self.showformerror, form))
            else:
                action.triggered.connect(partial(self.loadform, form))
            formpicker.addAction(action)

        formpicker.exec_()

    def showformerror(self, form):
        pass

    def viewurl(self, url):
        """
        Open a URL in Roam
        :param url:
        :return:
        """
        key = url.toString().lstrip('file://')
        try:
            # Hack. Eww fix me.
            data, imagetype = roam.htmlviewer.images[os.path.basename(key)]
        except KeyError:
            # It's not a image so lets just pass it of as a normal
            # URL
            QDesktopServices.openUrl(url)
            return

        pix = QPixmap()
        if imagetype == 'base64':
            pix.loadFromData(data)
        else:
            pix.load(data)

        self.openimage(pix)

    def openimage(self, pixmap):
        viewer = ImageViewer(self.stackedWidget)
        viewer.resize(self.stackedWidget.size())
        viewer.openimage(pixmap)

    def settingsupdated(self, settings):
        self.show()
        self.actionGPS.updateGPSPort()

    def updatestatuslabel(self):
        extent = self.canvas.extent()
        self.positionlabel.setText("Map Center: {}".format(extent.center().toString()))

    def on_geometryedit(self, form, feature):
        layer = form.QGISLayer
        try:
            selectedfeatures = self.currentselection[layer]
            oldfeature = [f for f in selectedfeatures if f.id() == feature.id()][0]
            self.currentselection[layer].remove(oldfeature)
            self.currentselection[layer].append(feature)
        except KeyError:
            return
        except IndexError:
            return

        self.currentfeatureband.setToGeometry(feature.geometry(), layer)
        self.highlightselection(self.currentselection)


    def highlightselection(self, results):
        self.clearselection()
        self.currentselection = results
        for layer, features in results.iteritems():
            band = self.selectionbands[layer]
            band.setColor(QColor(255, 0, 0, 200))
            band.setIconSize(20)
            band.setWidth(2)
            band.setBrushStyle(Qt.NoBrush)
            band.reset(layer.geometryType())
            for feature in features:
                band.addGeometry(feature.geometry(), layer)

    def clearselection(self):
        # Clear the main selection rubber band
        self.currentfeatureband.reset()
        # Clear the rest
        for band in self.selectionbands.itervalues():
            band.reset()

        self.editfeaturestack = []

    def highlightfeature(self, layer, feature, features):
        self.clearselection()
        self.highlightselection({layer: features})
        self.currentfeatureband.setToGeometry(feature.geometry(), layer)

    def showmap(self):
        self.actionMap.setVisible(True)
        self.actionLegend.setVisible(True)
        self.actionMap.trigger()

    def hidedataentry(self):
        self.actionDataEntry.setVisible(False)

    def showdataentry(self):
        self.actionDataEntry.setVisible(True)
        self.actionDataEntry.trigger()

    def dataentrychanged(self, index):
        wasactive = self.clearCapatureTools()

        if not index.isValid():
            return

        modelindex = index
        # modelindex = self.dataentrymodel.index(index, 0)
        form = modelindex.data(Qt.UserRole + 1)
        self.dataentryselection.setCurrentIndex(index.row())
        self.createCaptureButtons(form, wasactive)

    def raiseerror(self, *exinfo):
        info = traceback.format_exception(*exinfo)
        item = self.bar.pushError(QApplication.translate('MainWindowPy','Seems something has gone wrong. Press for more details', None, QApplication.UnicodeUTF8),
                                  info)

    def setMapTool(self, tool, *args):
        self.canvas.setMapTool(tool)

    def homeview(self):
        """
        Zoom the mapview canvas to the extents the project was opened at i.e. the
        default extent.
        """
        self.canvas.setExtent(self.defaultextent)
        self.canvas.refresh()

    def connectButtons(self):
        def connectAction(action, tool):
            action.toggled.connect(partial(self.setMapTool, tool))

        def cursor(name):
            pix = QPixmap(name)
            pix = pix.scaled(QSize(24,24))
            return QCursor(pix)

        self.zoomInTool = QgsMapToolZoom(self.canvas, False)
        self.zoomOutTool = QgsMapToolZoom(self.canvas, True)
        self.panTool = TouchMapTool(self.canvas)
        self.moveTool = MoveTool(self.canvas, [])
        self.infoTool = InfoTool(self.canvas)

        connectAction(self.actionZoom_In, self.zoomInTool)
        connectAction(self.actionZoom_Out, self.zoomOutTool)
        connectAction(self.actionPan, self.panTool)
        connectAction(self.actionMove, self.moveTool)
        connectAction(self.actionInfo, self.infoTool)

        self.zoomInTool.setCursor(cursor(':/icons/in'))
        self.zoomOutTool.setCursor(cursor(':/icons/out'))
        self.infoTool.setCursor(cursor(':/icons/info'))

        self.actionRaster.triggered.connect(self.toggleRasterLayers)

        self.infoTool.infoResults.connect(self.showInfoResults)

        # The edit toolbutton is currently not being used but leaving it for feature.
        self.moveTool.layersupdated.connect(self.actionMove.setEnabled)
        self.moveTool.layersupdated.connect(self.actionEdit_Tools.setEnabled)

        self.actionHome.triggered.connect(self.homeview)
        self.actionQuit.triggered.connect(self.exit)

    def getcaptureactions(self):
        for action in self.projecttoolbar.actions():
            if action.property('dataentry'):
                yield action

    def clearCapatureTools(self):
        captureselected = False
        for action in self.projecttoolbar.actions():
            if action.objectName() == "capture" and action.isChecked():
                captureselected = True

            if action.property('dataentry'):
                self.projecttoolbar.removeAction(action)
        return captureselected

    def createCaptureButtons(self, form, wasselected):
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

            if action.isdefault:
                action.setChecked(wasselected)

        if hasattr(tool, 'geometryComplete'):
            add = partial(self.addNewFeature, form)
            tool.geometryComplete.connect(add)
        else:
            tool.finished.connect(self.openForm)
            tool.error.connect(partial(self.showUIMessage, form.label))

        #self.projecttoolbar.insertAction(self.topspaceraction, self.actionGPSFeature)
        #self.actionGPSFeature.setVisible(not tool.isEditTool())

    def loadform(self, form):
        captureactive = self.clearCapatureTools()
        self.dataentryselection.setIcon(QIcon(form.icon))
        self.dataentryselection.setText(form.icontext)
        self.createCaptureButtons(form, captureactive)

    def clearToolRubberBand(self):
        """
        Clear the rubber band of the active tool if it has one
        """
        tool = self.canvas.mapTool()
        try:
            tool.clearBand()
        except AttributeError:
            # No clearBand method found, but that's cool.
            pass

    def showhelp(self, url):
        help = HelpPage(self.stackedWidget)
        help.setHelpPage(url)
        help.show()

    def dataentryfinished(self):
        self.hidedataentry()
        self.showmap()
        self.cleartempobjects()
        self.infodock.refreshcurrent()

    def featuredeleted(self):
        self.dataentryfinished()
        RoamEvents.raisemessage("Deleted", "Feature Deleted", QgsMessageBar.INFO, 1)
        self.canvas.refresh()

    def featureSaved(self):
        self.dataentryfinished()
        self.canvas.refresh()

    def failSave(self, messages):
        self.bar.pushError("Error when saving changes.", messages)

    def cleartempobjects(self):
        self.currentfeatureband.reset()
        self.clearToolRubberBand()

    def formrejected(self, message, level):
        self.dataentryfinished()
        if message:
            RoamEvents.raisemessage("Form Message", message, level, duration=2)

        self.cleartempobjects()

    def openForm(self, form, feature):
        """
        Open the form that is assigned to the layer
        """
        self.currentfeatureband.setToGeometry(feature.geometry(), form.QGISLayer)
        self.showdataentry()
        self.dataentrywidget.openform(feature=feature, form=form, project=self.project)

    def editfeaturegeometry(self, form, feature, newgeometry):
        layer = form.QGISLayer
        layer.startEditing()
        feature.setGeometry(newgeometry)
        layer.updateFeature(feature)
        saved = layer.commitChanges()
        map(roam.utils.error, layer.commitErrors())
        self.canvas.refresh()
        RoamEvents.editgeometry_complete.emit(form, feature)

    def addNewFeature(self, form, geometry):
        """
        Add a new new feature to the given layer
        """
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

        self.openForm(form, feature)

    def exit(self):
        """
        Exit the application.
        """
        QApplication.exit(0)

    def showInfoResults(self, results):
        forms = {}
        for layer in results.keys():
            layername = layer.name()
            if not layername in forms:
                forms[layername] = list(self.project.formsforlayer(layername))

        self.infodock.setResults(results, forms)
        self.infodock.show()

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

    def missingLayers(self, layers):
        """
        Called when layers have failed to load from the current project
        """
        roam.utils.warning("Missing layers")
        map(roam.utils.warning, layers)

        missinglayers = roam.messagebaritems.MissingLayerItem(layers,
                                                              parent=self.bar)
        self.bar.pushItem(missinglayers)

    def loadprojects(self, projects):
        """
        Load the given projects into the project
        list
        """
        projects = list(projects)
        self.projectwidget.loadProjectList(projects)
        self.syncwidget.loadprojects(projects)

    def updatePage(self, action):
        """
        Update the current stack page based on the current selected
        action
        """
        page = action.property("page")
        self.stackedWidget.setCurrentIndex(page)

    def show(self):
        """
        Override show method. Handles showing the app in fullscreen
        mode or just maximized
        """
        fullscreen = roam.config.settings.get("fullscreen", False)
        if fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()

    def viewprojects(self):
        self.stackedWidget.setCurrentIndex(1)

    @roam.utils.timeit
    def _readProject(self, doc):
        """
        readProject is called by QgsProject once the map layer has been
        populated with all the layers
        """
        parser = ProjectParser(doc)
        canvasnode = parser.canvasnode
        self.canvas.freeze()
        self.canvas.mapRenderer().readXML(canvasnode)
        self.canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(self.canvaslayers)
        #red = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorRedPart", 255 )[0];
        #green = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorGreenPart", 255 )[0];
        #blue = QgsProject.instance().readNumEntry( "Gui", "/CanvasColorBluePart", 255 )[0];
        #color = QColor(red, green, blue);
        #self.canvas.setCanvasColor(color)
        self.canvas.updateScale()
        self.projectOpened()
        self.canvas.freeze(False)
        self.canvas.refresh()
        GPS.crs = self.canvas.mapRenderer().destinationCrs()
        self.showmap()

    @roam.utils.timeit
    def projectOpened(self):
        """
            Called when a new project is opened in QGIS.
        """
        projectpath = QgsProject.instance().fileName()
        self.project = Project.from_folder(os.path.dirname(projectpath))
        self.projectlabel.setText("Project: {}".format(self.project.name))
        try:
            firstform = self.project.forms[0]
            self.loadform(self.project.forms[0])
            self.dataentryselection.setVisible(True)
        except IndexError:
            self.dataentryselection.setVisible(False)

        # Enable the raster layers button only if the project contains a raster layer.
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        hasrasters = any(layer.type() == QgsMapLayer.RasterLayer for layer in layers)
        self.actionRaster.setEnabled(hasrasters)
        self.defaultextent = self.canvas.extent()
        roam.utils.info("Extent: {}".format(self.defaultextent.toString()))

        # Show panels
        for panel in self.project.getPanels():
            self.mainwindow.addDockWidget(Qt.BottomDockWidgetArea, panel)
            self.panels.append(panel)

        self.infoTool.selectionlayers = self.project.selectlayersmapping()
        self.actionPan.trigger()

    #noinspection PyArgumentList
    @roam.utils.timeit
    def loadProject(self, project):
        """
        Load a project into the application .
        """
        roam.utils.log(project)
        roam.utils.log(project.name)
        roam.utils.log(project.projectfile)
        roam.utils.log(project.valid)

        (passed, message) = project.onProjectLoad()

        if not passed:
            self.bar.pushMessage("Project load rejected", "Sorry this project couldn't"
                                                          "be loaded.  Click for me details.",
                                 QgsMessageBar.WARNING, extrainfo=message)
            return

        self.actionMap.trigger()

        self.closeProject()

        self.canvas.refresh()
        self.canvas.repaint()

        RoamEvents.selectioncleared.emit()

        # No idea why we have to set this each time.  Maybe QGIS deletes it for
        # some reason.
        self.badLayerHandler = BadLayerHandler(callback=self.missingLayers)
        QgsProject.instance().setBadLayerHandler(self.badLayerHandler)

        self.stackedWidget.setCurrentIndex(3)
        self.projectloading_label.setText("Project {} Loading".format(project.name))
        pixmap = QPixmap(project.splash)
        w = self.projectimage.width()
        h = self.projectimage.height()
        self.projectimage.setPixmap(pixmap.scaled(w,h, Qt.KeepAspectRatio))
        QApplication.processEvents()

        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        QgsProject.instance().read(fileinfo)

    def closeProject(self):
        """
        Close the current open project
        """
        self.clearCapatureTools()
        self.canvas.freeze()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        self.canvas.clear()
        self.canvas.freeze(False)
        for panel in self.panels:
            self.removeDockWidget(panel)
            del panel
            # Remove all the old buttons
        for action in self.layerbuttons:
            self.editgroup.removeAction(action)

        self.panels = []
        self.project = None
        self.dataentrywidget.clear()
        self.hidedataentry()
        self.infodock.close()



