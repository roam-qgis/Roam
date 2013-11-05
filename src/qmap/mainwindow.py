from PyQt4.QtCore import Qt, QFileInfo, QDir
from PyQt4.QtGui import (QActionGroup, QWidget, QSizePolicy, QLabel, QApplication,
                         QPixmap)
from qgis.core import (QgsProjectBadLayerHandler, QgsPalLabeling, QgsMapLayerRegistry,
                        QgsProject, QgsMapLayer)
from qgis.gui import (QgsMessageBar, QgsMapToolZoom, QgsMapToolTouch)

from functools import partial
import sys
import os

from qmap.uifiles import mainwindow_widget, mainwindow_base
from qmap.listmodulesdialog import ProjectsWidget
from qmap.settingswidget import SettingsWidget
from qmap.projectparser import ProjectParser
from qmap.project import QMapProject

import qmap.messagebaritems
import qmap.utils


class BadLayerHandler( QgsProjectBadLayerHandler):
    """
    Handler class for any layers that fail to load when
    opening the project.
    """
    def __init__( self, callback ):
        """
            callback - Any bad layers are passed to the callback so it
            can do what it wills with them
        """
        super(BadLayerHandler, self).__init__()
        self.callback = callback

    def handleBadLayers( self, domNodes, domDocument ):
        layers = [node.namedItem("layername").toElement().text() for node in domNodes]
        self.callback(layers)


class MainWindow(mainwindow_widget, mainwindow_base):
    """
    Main application window
    """
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
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

        spacewidget = createSpacer(60)
        gpsspacewidget = createSpacer(30)
        sidespacewidget = createSpacer(30)
        sidespacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.projecttoolbar.insertWidget(self.actionSync, gpsspacewidget)
        self.projecttoolbar.insertWidget(self.actionHome, spacewidget)

        def _createSideLabel(text):
            style = """
                QLabel {
                        color: #706565;
                        font: 12px "Calibri" ;
                        }"""
            label = QLabel(text)
            #label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(style)

            return label

        self.projectlabel = _createSideLabel("Project: {project}")
        self.userlabel = _createSideLabel("User: {user}")
        self.statusbar.addWidget(self.projectlabel)
        self.statusbar.addWidget(self.userlabel)

        self.menutoolbar.insertWidget(self.actionSettings, sidespacewidget)
        self.stackedWidget.currentChanged.connect(self.updateUIState)

        self.panels = []
        self.infodock = QWidget()

        self.connectButtons()

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
        self.zoomOutTool  = QgsMapToolZoom(self.canvas, True)
        self.panTool = QgsMapToolTouch(self.canvas)

        connectAction(self.actionZoom_In, self.zoomInTool)
        connectAction(self.actionZoom_Out, self.zoomOutTool)
        connectAction(self.actionPan, self.panTool)
        self.actionHome.triggered.connect(self.zoomToDefaultView)
        self.actionDefault.triggered.connect(self.canvas.zoomToFullExtent)

    def missingLayers(self, layers):
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

    def updateUIState(self, page):
        """
        Update the UI state to reflect the currently selected
        page in the stacked widget
        """
        def setToolbarsActive(enabled):
          self.projecttoolbar.setEnabled(enabled)

        def setPanelsVisible(visible):
            for panel in self.panels:
                panel.setVisible(visible)

        ismapview = page == 0
        setToolbarsActive(ismapview)
        setPanelsVisible(ismapview)
        self.infodock.hide()

    def _readProject(self, doc):
        """
        readProject is called by QgsProject once the map layer has been
        populated with all the layers
        """
        parser = ProjectParser(doc)
        canvasnode = parser.canvasnode
        self.canvas.mapRenderer().readXML(canvasnode)
        canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(canvaslayers)
        self.canvas.updateScale()
        self.canvas.freeze(False)
        self.canvas.refresh()

        self.projectOpened()
        self.stackedWidget.setCurrentIndex(0)

    def projectOpened(self):
        """
            Called when a new project is opened in QGIS.
        """
        projectpath = QgsProject.instance().fileName()
        project = QMapProject(os.path.dirname(projectpath))
        self.projectlabel.setText("Project: {}".format(project.name))
        # TODO create form buttons
        #self.createFormButtons(projectlayers = project.getConfiguredLayers())

        # Enable the raster layers button only if the project contains a raster layer.
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        hasrasters = any(layer.type() == QgsMapLayer.RasterLayer for layer in layers)
        self.actionRaster.setEnabled(hasrasters)
        self.defaultextent = self.canvas.extent()
        # TODO Connect sync providers
        #self.connectSyncProviders(project)

        # Show panels
        for panel in project.getPanels():
            self.mainwindow.addDockWidget(Qt.BottomDockWidgetArea , panel)
            self.panels.append(panel)

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
        # TODO: Fix info dock
        #self.infodock.clearResults()
        # No idea why we have to set this each time.  Maybe QGIS deletes it for
        # some reason.
        self.badLayerHandler = BadLayerHandler(callback=self.missingLayers)
        QgsProject.instance().setBadLayerHandler( self.badLayerHandler )

        #self.messageBar.pushMessage("Project Loading","", QgsMessageBar.INFO)
        self.stackedWidget.setCurrentIndex(3)
        self.projectloading_label.setText("Project {} Loading".format(project.name))
        self.projectimage.setPixmap(QPixmap(project.splash))
        QApplication.processEvents()

        fileinfo = QFileInfo(project.projectfile)
        QDir.setCurrent(os.path.dirname(project.projectfile))
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
        self.panels = []




