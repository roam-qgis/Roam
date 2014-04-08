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
                        QCursor, QFrame, QDesktopServices)
from qgis.core import (QgsProjectBadLayerHandler,
                        QgsPalLabeling,
                        QgsMapLayerRegistry,
                        QgsProject,
                        QgsMapLayer,
                        QgsFeature,
                        QgsFields,
                        QgsGeometry)
from qgis.gui import (QgsMessageBar,
                        QgsMapToolZoom,
                        QgsMapToolTouch,
                        QgsRubberBand,
                        QgsMapCanvas)


from roam.gps_action import GPSAction
from roam.reportwidget import ReportWidget
from roam.dataentrywidget import DataEntryWidget
from roam.ui.uifiles import mainwindow_widget, mainwindow_base
from roam.listmodulesdialog import ProjectsWidget
from roam.settingswidget import SettingsWidget
from roam.projectparser import ProjectParser
from roam.project import Project, NoMapToolConfigured, ErrorInMapTool
from roam.maptools import MoveTool, InfoTool, EditTool, PointTool, TouchMapTool
from roam.infodock import InfoDock
from roam.syncwidget import SyncWidget
from roam.helpviewdialog import HelpPage
from roam.biglist import BigList
from roam.imageviewerwidget import ImageViewer
from roam.api import RoamEvents

import roam.messagebaritems
import roam.utils
import roam.htmlviewer
import roam.api.featureform


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


class MainWindow(mainwindow_widget, mainwindow_base):
    """
    Main application window
    """

    def __init__(self, settings):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.settings = settings
        self.canvaslayers = []
        self.layerbuttons = []
        self.project = None
        self.selectionbands = defaultdict(partial(QgsRubberBand, self.canvas))
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.bar = roam.messagebaritems.MessageBar(self)

        self.actionMap.setVisible(False)

        pal = QgsPalLabeling()
        self.canvas.mapRenderer().setLabelingEngine(pal)
        self.canvas.setFrameStyle(QFrame.NoFrame)
        self.menuGroup = QActionGroup(self)
        self.menuGroup.setExclusive(True)

        self.menuGroup.addAction(self.actionMap)
        self.menuGroup.addAction(self.actionDataEntry)
        self.menuGroup.addAction(self.actionReport)
        self.menuGroup.addAction(self.actionProject)
        self.menuGroup.addAction(self.actionSync)
        self.menuGroup.addAction(self.actionSettings)
        self.menuGroup.triggered.connect(self.updatePage)

        self.editgroup = QActionGroup(self)
        self.editgroup.setExclusive(True)
        self.editgroup.addAction(self.actionPan)
        self.editgroup.addAction(self.actionZoom_In)
        self.editgroup.addAction(self.actionZoom_Out)
        self.editgroup.addAction(self.actionInfo)

        #TODO Extract GPS out into a service and remove UI stuff
        self.actionGPS = GPSAction(":/icons/gps", self.canvas, self.settings, self)
        self.projecttoolbar.addAction(self.actionReport)
        self.projecttoolbar.addAction(self.actionGPS)

        self.projectwidget = ProjectsWidget(self)
        self.projectwidget.requestOpenProject.connect(self.loadProject)
        QgsProject.instance().readProject.connect(self._readProject)
        self.project_page.layout().addWidget(self.projectwidget)

        self.syncwidget = SyncWidget()
        self.syncpage.layout().addWidget(self.syncwidget)

        self.settingswidget = SettingsWidget(settings, self)
        self.settings_page.layout().addWidget(self.settingswidget)
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

        self.reportwidget = ReportWidget(self.bar)
        self.reportpage.layout().addWidget(self.reportwidget)
        self.reportwidget.closed.connect(self.reportclosed)


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
        self.statusbar.addWidget(self.projectlabel)
        self.statusbar.addWidget(self.userlabel)
        spacer = createSpacer()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.statusbar.addWidget(spacer)
        self.statusbar.addWidget(self.positionlabel)

        self.menutoolbar.insertWidget(self.actionQuit, sidespacewidget2)
        self.menutoolbar.insertWidget(self.actionProject, sidespacewidget)
        self.stackedWidget.currentChanged.connect(self.updateUIState)

        self.panels = []

        self.connectButtons()

        self.band = QgsRubberBand(self.canvas)
        self.band.setIconSize(20)
        self.band.setWidth(10)
        self.band.setColor(QColor(186, 93, 212, 76))

        self.canvas_page.layout().insertWidget(0, self.projecttoolbar)
        self.dataentrymodel = QStandardItemModel(self)
        self.dataentrycombo = QComboBox(self.projecttoolbar)
        self.dataentrycombo.setIconSize(QSize(48,48))
        self.dataentrycombo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.dataentrycombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.dataentrycombo.setModel(self.dataentrymodel)
        self.dataentrycomboaction = self.projecttoolbar.insertWidget(self.topspaceraction, self.dataentrycombo)

        self.dataentrycombo.showPopup = self.selectdataentry

        self.biglist = BigList(self.canvas)
        self.biglist.setlabel("Select data entry form")
        self.biglist.setmodel(self.dataentrymodel)
        self.biglist.itemselected.connect(self.dataentrychanged)
        self.biglist.hide()

        self.centralwidget.layout().addWidget(self.statusbar)

        self.actionGPSFeature.setProperty('dataentry', True)

        self.infodock = InfoDock(self.canvas)
        self.infodock.featureupdated.connect(self.highlightfeature)
        self.infodock.hide()
        self.hidedataentry()
	self.hidereport()
        self.canvas.extentsChanged.connect(self.updatestatuslabel)
        self.projecttoolbar.toolButtonStyleChanged.connect(self.updatecombo)
        
	self.canvas.refresh()
	self.canvas.repaint()

        RoamEvents.openimage.connect(self.openimage)
        RoamEvents.openurl.connect(self.viewurl)
        RoamEvents.openfeatureform.connect(self.openForm)
        RoamEvents.openkeyboard.connect(self.openkeyboard)
        RoamEvents.selectioncleared.connect(self.clearselection)

    def openkeyboard(self):
        if self.settings.settings.get('keyboard', True):
            cmd = r'C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe'
            os.startfile(cmd)

    def selectdataentry(self, ):
        if self.dataentrycombo.count() == 0:
            return

        self.biglist.show()

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

    def updatecombo(self, *args):
        self.dataentrycombo.setMinimumHeight(0)

    def settingsupdated(self, settings):
        settings.save()
        self.show()
        self.actionGPS.updateGPSPort()
        # eww!
        roam.featureform.settings = settings.settings

    def updatestatuslabel(self):
        extent = self.canvas.extent()
        self.positionlabel.setText("Map Center: {}".format(extent.center().toString()))

    def highlightselection(self, results):
        self.clearselection()
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
        self.band.reset()
        # Clear the rest
        for band in self.selectionbands.itervalues():
            band.reset()

    def highlightfeature(self, layer, feature, features):
        self.clearselection()
        self.highlightselection({layer: features})
        self.band.setToGeometry(feature.geometry(), layer)

    def showmap(self):
        self.actionMap.setVisible(True)
        self.actionMap.trigger()

    def hidedataentry(self):
        self.actionDataEntry.setVisible(False)

    def hidereport(self):
	self.actionReport.setVisible(False)

    def showdataentry(self):
        self.actionDataEntry.setVisible(True)
        self.actionDataEntry.trigger()

    def showreport(self):
	self.actionReport.setVisible(True)
        self.actionReport.trigger()

    def dataentrychanged(self, index):
        wasactive = self.clearCapatureTools()

        if not index.isValid():
            return

        modelindex = index
        # modelindex = self.dataentrymodel.index(index, 0)
        form = modelindex.data(Qt.UserRole + 1)
        self.dataentrycombo.setCurrentIndex(index.row())
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

        self.actionReport.triggered.connect(self.openReport)

        self.actionGPSFeature.triggered.connect(self.addFeatureAtGPS)
        self.actionGPSFeature.setEnabled(self.actionGPS.isConnected)
        self.actionGPS.gpsfixed.connect(self.actionGPSFeature.setEnabled)

        self.actionHome.triggered.connect(self.homeview)
        self.actionQuit.triggered.connect(self.exit)

    def showToolError(self, label, message):
        self.bar.pushMessage(label, message, QgsMessageBar.WARNING)

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
            tool.error.connect(partial(self.showToolError, form.label))

        self.projecttoolbar.insertAction(self.topspaceraction, self.actionGPSFeature)
        self.actionGPSFeature.setVisible(not tool.isEditTool())

    def createFormButtons(self, forms):
        """
            Create buttons for each form that is defined
        """
        self.dataentrymodel.clear()
        self.clearCapatureTools()


        def captureFeature(form):
            item = QStandardItem(QIcon(form.icon), form.icontext)
            item.setData(form, Qt.UserRole + 1)
            item.setSizeHint(QSize(item.sizeHint().width(), self.projecttoolbar.height()))
            self.dataentrymodel.appendRow(item)

        capabilitityhandlers = {"capture": captureFeature}

        failedforms = []
        for form in forms:
            valid, reasons = form.valid
            if not valid:
                roam.utils.log("Form is invalid for data entry because {}".format(reasons))
                failedforms.append((form, reasons))
                continue

            for capability in form.capabilities:
                try:
                    capabilitityhandlers[capability](form)
                except KeyError:
                    # Just ignore capabilities we don't support yet.
                    continue

        if failedforms:
            for form, reasons in failedforms:
                html = "<h3>{}</h3><br>{}".format(form.label,
                                             "<br>".join(reasons))
            self.bar.pushMessage(QApplication.translate("MainWindowPy", "Form errors", None, QApplication.UnicodeUTF8),
                                 QApplication.translate("MainWindowPy", "Looks like some forms couldn't be loaded", None, QApplication.UnicodeUTF8),
                                 level=QgsMessageBar.WARNING, extrainfo=html)

        visible = self.dataentrymodel.rowCount() > 0
        self.dataentrycomboaction.setVisible(visible)
        self.dataentrycombo.setMinimumHeight(self.projecttoolbar.height())

        index = self.dataentrymodel.index(0, 0)
        self.dataentrychanged(index)

    def addFeatureAtGPS(self):
        """
        Add a record at the current GPS location.
        """
        index = self.dataentrycombo.currentIndex()
        modelindex = self.dataentrymodel.index(index, 0)
        form = modelindex.data(Qt.UserRole + 1)
        point = self.actionGPS.position
        point = QgsGeometry.fromPoint(point)
        self.addNewFeature(form=form, geometry=point)

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
        self.bar.pushMessage("Deleted", "Feature Deleted", QgsMessageBar.INFO, 1)
        self.canvas.refresh()

    def featureSaved(self):
        self.dataentryfinished()
        self.canvas.refresh()

    def failSave(self, messages):
        self.bar.pushError("Error when saving changes.", messages)

    def cleartempobjects(self):
        self.band.reset()
        self.clearToolRubberBand()

    def reportclosed(self):
	self.showmap()
	self.cleartempobjects()
	self.infodock.refreshcurrent()

    def formrejected(self, message, level):
        self.dataentryfinished()
        if message:
            self.bar.pushMessage("Form Message", message, level, duration=2)

        self.cleartempobjects()
    
    def openReport(self):
	"""
	open report widget
	"""
	self.reportwidget.openReport(self.project)

    def openForm(self, form, feature):
        """
        Open the form that is assigned to the layer
        """
        self.band.setToGeometry(feature.geometry(), form.QGISLayer)
        self.showdataentry()
        self.dataentrywidget.openform(feature=feature, form=form, project=self.project)

    def addNewFeature(self, form, geometry):
        """
        Add a new new feature to the given layer
        """
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
        fullscreen = self.settings.settings.get("fullscreen", False)
        if fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()

    def viewprojects(self):
        self.stackedWidget.setCurrentIndex(1)

    def updateUIState(self, page):
        """
        Update the UI state to reflect the currently selected
        page in the stacked widget
        """
        pass

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
        self.showmap()

    @roam.utils.timeit
    def projectOpened(self):
        """
            Called when a new project is opened in QGIS.
        """
        projectpath = QgsProject.instance().fileName()
        self.project = Project.from_folder(os.path.dirname(projectpath))
        self.projectlabel.setText("Project: {}".format(self.project.name))
        self.createFormButtons(forms=self.project.forms)
	
	if self.project.hasReport:
	   self.showreport()
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

        self.dataentrymodel.clear()
        self.panels = []
        self.project = None
        self.dataentrywidget.clear()
	self.reportwidget.clear()
        self.hidedataentry()
	self.hidereport()
        self.infodock.close()




