from PyQt4.QtCore import Qt, QFileInfo, QDir, QSize, QModelIndex
from PyQt4.QtGui import (QActionGroup
                        ,QWidget
                        ,QSizePolicy
                        ,QLabel
                        ,QApplication
                        ,QPixmap
                        ,QColor
                        ,QMessageBox
                        ,QStandardItemModel
                        ,QStandardItem
                        ,QItemSelectionModel
                        ,QIcon)
from qgis.core import (QgsProjectBadLayerHandler
                        ,QgsPalLabeling
                        ,QgsMapLayerRegistry
                        ,QgsProject
                        ,QgsMapLayer
                        ,QgsFeature
                        ,QgsFields)
from qgis.gui import (QgsMessageBar
                    ,QgsMapToolZoom
                    ,QgsMapToolTouch
                    ,QgsRubberBand)

from functools import partial

import getpass
import sys
import os

from qmap.gps_action import GPSAction
from qmap.dialog_provider import DialogProvider
from qmap.uifiles import mainwindow_widget, mainwindow_base
from qmap.listmodulesdialog import ProjectsWidget
from qmap.floatingtoolbar import FloatingToolBar
from qmap.settingswidget import SettingsWidget
from qmap.projectparser import ProjectParser
from qmap.project import QMapProject, NoMapToolConfigured, ErrorInMapTool
from qmap.maptools import MoveTool, InfoTool, EditTool, PointTool
from qmap.listfeatureform import ListFeaturesForm
from qmap.infodock import InfoDock

import qmap.messagebaritems
import qmap.utils


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

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.canvaslayers = []
        self.layerbuttons = []
        self.project = None
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        pal = QgsPalLabeling()
        self.canvas.mapRenderer().setLabelingEngine(pal)
        self.menuGroup = QActionGroup(self)
        self.menuGroup.setExclusive(True)

        self.menuGroup.addAction(self.actionMap)
        self.menuGroup.addAction(self.actionProject)
        self.menuGroup.addAction(self.actionSettings)
        self.menuGroup.triggered.connect(self.updatePage)

        self.editgroup = QActionGroup(self)
        self.editgroup.setExclusive(True)
        self.editgroup.addAction(self.actionPan)
        self.editgroup.addAction(self.actionZoom_In)
        self.editgroup.addAction(self.actionZoom_Out)
        self.editgroup.addAction(self.actionInfo)
        self.editgroup.addAction(self.actionEdit_Tools)
        self.editgroup.addAction(self.actionEdit_Attributes)

        #TODO Extract GPS out into a service and remove UI stuff
        self.actionGPS = GPSAction(":/icons/gps", self.canvas, self)
        self.projecttoolbar.addAction(self.actionGPS)

        self.projectwidget = ProjectsWidget(self)
        self.projectwidget.requestOpenProject.connect(self.loadProject)
        QgsProject.instance().readProject.connect(self._readProject)
        self.project_page.layout().addWidget(self.projectwidget)

        self.settingswidget = SettingsWidget(self)
        self.settings_page.layout().addWidget(self.settingswidget)
        self.actionSettings.toggled.connect(self.settingswidget.populateControls)
        self.actionSettings.toggled.connect(self.settingswidget.readSettings)

        def createSpacer(width):
            widget = QWidget()
            widget.setMinimumWidth(width)
            return widget

        gpsspacewidget = createSpacer(30)
        sidespacewidget = createSpacer(30)
        sidespacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.topspaceraction = self.projecttoolbar.insertWidget(self.actionSync, gpsspacewidget)

        def _createSideLabel(text):
            style = """
                QLabel {
                        color: #706565;
                        font: 14px "Calibri" ;
                        }"""
            label = QLabel(text)
            #label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(style)

            return label

        self.projectlabel = _createSideLabel("Project: {project}")
        self.userlabel = _createSideLabel("User: {user}".format(user=getpass.getuser()))
        self.statusbar.addWidget(self.projectlabel)
        self.statusbar.addWidget(self.userlabel)

        self.menutoolbar.insertWidget(self.actionSettings, sidespacewidget)
        self.stackedWidget.currentChanged.connect(self.updateUIState)

        self.panels = []

        self.edittoolbar = FloatingToolBar("Editing", self.projecttoolbar)
        self.extraaddtoolbar = FloatingToolBar("Feature Tools", self.projecttoolbar)
        self.syncactionstoolbar = FloatingToolBar("Syncing", self.projecttoolbar)
        self.syncactionstoolbar.setOrientation(Qt.Vertical)

        size = QSize(32, 32)
        self.edittoolbar.setIconSize(size)
        self.extraaddtoolbar.setIconSize(size)
        self.syncactionstoolbar.setIconSize(size)

        style = Qt.ToolButtonTextUnderIcon
        self.edittoolbar.setToolButtonStyle(style)
        self.extraaddtoolbar.setToolButtonStyle(style)
        self.syncactionstoolbar.setToolButtonStyle(style)

        self.connectButtons()

        self.band = QgsRubberBand(self.canvas)
        self.band.setIconSize(20)
        self.band.setWidth(10)
        self.band.setColor(QColor(186, 93, 212, 76))

        self.bar = qmap.messagebaritems.MessageBar(self)
        self.messageBar = qmap.messagebaritems.MessageBar(self.canvas)

        from PyQt4.QtGui import QToolBar, QComboBox

        self.canvas_page.layout().insertWidget(2, self.projecttoolbar)
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(48, 48))
        self.dataentrymodel = QStandardItemModel(self)
        self.dataentrycombo = QComboBox()
        self.dataentrycombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.dataentrycombo.setModel(self.dataentrymodel)
        self.dataentrycombo.currentIndexChanged.connect(self.dataentrychanged)
        self.toolbar.addWidget(self.dataentrycombo)
        self.canvas_page.layout().insertWidget(3, self.toolbar)

        self.centralwidget.layout().addWidget(self.statusbar)

        self.infodock = InfoDock(self.canvas)


    def dataentrychanged(self, index):
        print "Data entry"
        self.clearCapatureTools()

        modelindex = self.dataentrymodel.index(index, 0)
        print modelindex
        layer = modelindex.data(Qt.UserRole + 1)
        print "New layer:{}".format(layer)
        self.createCaptureFeature(layer)

    def raiseerror(self, exctype, value, traceback):
        item = qmap.messagebaritems.ErrorMessage(execinfo=(exctype, value, traceback))
        self.bar.pushItem(item)

    def setMapTool(self, tool, *args):
        self.canvas.setMapTool(tool)

    def zoomToDefaultView(self):
        """
        Zoom the mapview canvas to the extents the project was opened at i.e. the
        default extent.
        """
        self.canvas.setExtent(self.defaultextent)
        self.canvas.refresh()

    def connectButtons(self):
        def connectAction(action, tool):
            action.toggled.connect(partial(self.setMapTool, tool))

        self.zoomInTool = QgsMapToolZoom(self.canvas, False)
        self.zoomOutTool = QgsMapToolZoom(self.canvas, True)
        self.panTool = QgsMapToolTouch(self.canvas)
        self.moveTool = MoveTool(self.canvas, [])
        self.infoTool = InfoTool(self.canvas)
        self.editTool = EditTool(self.canvas, [])

        connectAction(self.actionZoom_In, self.zoomInTool)
        connectAction(self.actionZoom_Out, self.zoomOutTool)
        connectAction(self.actionPan, self.panTool)
        connectAction(self.actionMove, self.moveTool)
        connectAction(self.actionInfo, self.infoTool)
        connectAction(self.actionEdit_Attributes, self.editTool)

        self.actionRaster.triggered.connect(self.toggleRasterLayers)

        self.infoTool.infoResults.connect(self.showInfoResults)

        self.editTool.finished.connect(self.openForm)
        self.editTool.featuresfound.connect(self.showFeatureSelection)
        self.editTool.radius = 10

        self.editTool.layersupdated.connect(self.actionEdit_Attributes.setVisible)
        self.moveTool.layersupdated.connect(self.actionMove.setVisible)
        self.moveTool.layersupdated.connect(self.actionEdit_Tools.setVisible)

        self.extraaddtoolbar.addAction(self.actionGPSFeature)

        self.edittoolbar.addAction(self.actionMove)
        self.edittoolbar.addToActionGroup(self.actionMove)

        showediting = (partial(self.edittoolbar.showToolbar,
                               self.actionEdit_Tools,
                               self.actionMove))

        self.actionEdit_Tools.toggled.connect(showediting)

        self.actionGPSFeature.triggered.connect(self.addFeatureAtGPS)
        self.actionGPSFeature.setEnabled(self.actionGPS.isConnected)
        self.actionGPS.gpsfixed.connect(self.actionGPSFeature.setEnabled)

        self.actionHome.triggered.connect(self.zoomToDefaultView)
        self.actionDefault.triggered.connect(self.canvas.zoomToFullExtent)
        self.actionQuit.triggered.connect(self.exit)

    def showToolError(self, label, message):
        self.messageBar.pushMessage(label, message, QgsMessageBar.WARNING)

    def clearCapatureTools(self):
        for action in self.toolbar.actions():
            if action.property('dataentry'):
                self.toolbar.removeAction(action)

    def createCaptureFeature(self, layer):
        tool = layer.getMaptool(self.canvas)
        action = layer.action
        action.toggled.connect(partial(self.setMapTool, tool))

        # Hack until I fix it latemessageBarr
        if isinstance(tool, PointTool):
            add = partial(self.addNewFeature, layer.QGISLayer)
            tool.geometryComplete.connect(add)
        else:
            tool.finished.connect(self.openForm)
            tool.error.connect(partial(self.showToolError, layer.icontext))

        # Set the action as a data entry button so we can remove it later.
        action.setProperty("dataentry", True)

        if not tool.isEditTool():
            # Connect the GPS tools strip to the action pressed event.
            showgpstools = (partial(self.extraaddtoolbar.showToolbar,
                                    action,
                                    None))

            action.toggled.connect(showgpstools)

        self.toolbar.addAction(action)
        self.editgroup.addAction(action)
        self.layerbuttons.append(action)

    def createFormButtons(self, projectlayers):
        """
            Create buttons for each form that is defined
        """
        # TODO Refactor me!

        self.editTool.reset()
        self.moveTool.reset()

        def editFeature(layer):
            self.editTool.addLayer(layer.QGISLayer)

        def moveFeature(layer):
            self.moveTool.addLayer(layer.QGISLayer)

        def captureFeature(layer):
            item = QStandardItem(QIcon(layer.icon), layer.icontext)
            item.setData(layer, Qt.UserRole + 1)
            self.dataentrymodel.appendRow(item)

        capabilitityhandlers = {"capture": captureFeature,
                                "edit": editFeature,
                                "move": moveFeature}

        for layer in projectlayers:
            valid, reason = layer.valid
            if not valid:
                qmap.utils.log("Layer is invalid for data entry because {}".format(reason))
                continue

            for capability in layer.capabilities:
                try:
                    capabilitityhandlers[capability](layer)
                except NoMapToolConfigured:
                    qmap.utils.log("No map tool configured")
                    continue
                except ErrorInMapTool as error:
                    self.messageBar.pushMessage("Error configuring map tool",
                                                error.message,
                                                level=QgsMessageBar.WARNING)
                    continue

        self.dataentrycombo.setCurrentIndex(0)

    def addFeatureAtGPS(self):
        """
        Add a record at the current GPS location.
        """
        action = self.editgroup.checkedAction()
        if not action:
            return
        layer = action.data()
        if not layer:
            return

        point = self.actionGPS.position
        self.addNewFeature(layer=layer, geometry=point)

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

    def openForm(self, layer, feature):
        """
        Open the form that is assigned to the layer
        """
        if not layer.isEditable():
            layer.startEditing()

        def featureSaved():
            self.messageBar.pushMessage("Saved",
                                        "Changes Saved",
                                        QgsMessageBar.INFO,
                                        2)
            self.band.reset()
            self.clearToolRubberBand()

        def failSave():
            self.messageBar.pushMessage("Error",
                                        "Error with saving changes.",
                                        QgsMessageBar.CRITICAL)
            self.band.reset()
            self.clearToolRubberBand()

        self.band.setToGeometry(feature.geometry(), layer)
        provider = DialogProvider(self.canvas)
        provider.featuresaved.connect(featureSaved)
        provider.failedsave.connect(failSave)

        qmaplayer = self.project.layer(layer.name())

        provider.openDialog(feature=feature,
                            layer=layer,
                            settings=self.project.layersettings,
                            qmaplayer=qmaplayer,
                            parent=self)

    def addNewFeature(self, layer, geometry):
        """
        Add a new new feature to the given layer
        """
        fields = layer.pendingFields()

        feature = QgsFeature()
        feature.setGeometry(geometry)
        feature.initAttributes(fields.count())
        feature.setFields(fields)

        for indx in xrange(fields.count()):
            feature[indx] = layer.dataProvider().defaultValue(indx)

        self.openForm(layer, feature)

    def exit(self):
        """
        Exit the application.
        """
        QApplication.exit(0)

    def showInfoResults(self, results):
        print results
        self.infodock.clearResults()
        self.infodock.setResults(results)
        self.infodock.show()

    def showFeatureSelection(self, features):
        """
        Show a list of features for user selection.
        """
        listUi = ListFeaturesForm(self)
        listUi.loadFeatureList(features)
        listUi.openFeatureForm.connect(self.openForm)
        listUi.exec_()

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
        qmap.utils.warning("Missing layers")
        map(qmap.utils.warning, layers)

        missinglayers = qmap.messagebaritems.MissingLayerItem(layers,
                                                              parent=self.messageBar)
        self.messageBar.pushItem(missinglayers)

    def loadProjectList(self, projects):
        """
        Load the given projects into the project
        list
        """
        self.projectwidget.loadProjectList(projects)

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
        fullscreen = qmap.utils.settings.get("fullscreen", False)
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

        def setToolbarsActive(enabled):
            self.projecttoolbar.setEnabled(enabled)
            self.extraaddtoolbar.setVisible(enabled)

        def setPanelsVisible(visible):
            for panel in self.panels:
                panel.setVisible(visible)

        ismapview = page == 0
        setToolbarsActive(ismapview)
        setPanelsVisible(ismapview)
        self.infodock.hide()

    @qmap.utils.timeit
    def _readProject(self, doc):
        """
        readProject is called by QgsProject once the map layer has been
        populated with all the layers
        """
        print "_readProject"
        parser = ProjectParser(doc)
        canvasnode = parser.canvasnode
        self.canvas.mapRenderer().readXML(canvasnode)
        self.canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(self.canvaslayers)
        self.canvas.updateScale()
        self.canvas.freeze(False)
        self.canvas.refresh()

        self.projectOpened()
        self.stackedWidget.setCurrentIndex(0)

    @qmap.utils.timeit
    def projectOpened(self):
        """
            Called when a new project is opened in QGIS.
        """
        projectpath = QgsProject.instance().fileName()
        self.project = QMapProject(os.path.dirname(projectpath))
        self.projectlabel.setText("Project: {}".format(self.project.name))
        self.createFormButtons(projectlayers=self.project.getConfiguredLayers())

        # Enable the raster layers button only if the project contains a raster layer.
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        hasrasters = any(layer.type() == QgsMapLayer.RasterLayer for layer in layers)
        self.actionRaster.setEnabled(hasrasters)
        self.defaultextent = self.canvas.extent()
        # TODO Connect sync providers
        #self.connectSyncProviders(project)

        # Show panels
        for panel in self.project.getPanels():
            self.mainwindow.addDockWidget(Qt.BottomDockWidgetArea, panel)
            self.panels.append(panel)

    #noinspection PyArgumentList
    @qmap.utils.timeit
    def loadProject(self, project):
        """
        Load a project into the application .
        """
        qmap.utils.log(project)
        qmap.utils.log(project.name)
        qmap.utils.log(project.projectfile)
        qmap.utils.log(project.vaild)

        (passed, message) = project.onProjectLoad()

        if not passed:
            QMessageBox.warning(self.mainwindow, "Project Load Rejected",
                                "Project couldn't be loaded because {}".format(message))
            return

        self.actionMap.trigger()
        self.closeProject()
        self.canvas.freeze()
        self.infodock.clearResults()

        # No idea why we have to set this each time.  Maybe QGIS deletes it for
        # some reason.
        self.badLayerHandler = BadLayerHandler(callback=self.missingLayers)
        QgsProject.instance().setBadLayerHandler(self.badLayerHandler)

        #self.messageBar.pushMessage("Project Loading","", QgsMessageBar.INFO)
        self.stackedWidget.setCurrentIndex(3)
        self.projectloading_label.setText("Project {} Loading".format(project.name))
        self.projectimage.setPixmap(QPixmap(project.splash))
        QApplication.processEvents()

        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        QgsProject.instance().read(fileinfo)
        print project.projectfile
        print QgsProject.instance().error()

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



