from PyQt4.QtCore import Qt, QFileInfo, QDir
from PyQt4.QtGui import QActionGroup, QWidget, QSizePolicy, QLabel, QApplication
from qgis.core import (QgsProjectBadLayerHandler, QgsPalLabeling, QgsMapLayerRegistry,
                        QgsProject)
from qgis.gui import (QgsMessageBar, QgsMapToolZoom, QgsMapToolTouch)

from functools import partial
import sys
import os

from qmap.uifiles import mainwindow_widget, mainwindow_base
from qmap.listmodulesdialog import ProjectsWidget
from qmap.projectparser import ProjectParser

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
        self.actionpages = {self.actionMap: 0,
                            self.actionProject: 1,
                            self.actionSettings: 2}

        self.editgroup = QActionGroup(self)
        self.editgroup.setExclusive(True)
        self.editgroup.addAction(self.actionPan)
        self.editgroup.addAction(self.actionZoom_In)
        self.editgroup.addAction(self.actionZoom_Out)
        self.editgroup.addAction(self.actionInfo)
        self.editgroup.addAction(self.actionEdit_Tools)
        self.editgroup.addAction(self.actionEdit_Attributes)

        self.menuGroup.triggered.connect(self.updatePage)

        self.projectwidget = ProjectsWidget(self)
        self.projectwidget.requestOpenProject.connect(self.loadProject)
        QgsProject.instance().readProject.connect(self._readProject)
        self.project_page.layout().addWidget(self.projectwidget)

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
                        color: #8c8c8c;
                        font: 10px "Calibri" ;
                        }"""
            label = QLabel(text)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(style)

            return label

        self.projectlabel = _createSideLabel("Project: <br> {project}")
        self.userlabel = _createSideLabel("User: <br> {user}")

        labelaction = self.menutoolbar.insertWidget(self.actionSettings, self.userlabel)

        self.menutoolbar.insertWidget(labelaction, sidespacewidget)
        self.menutoolbar.insertWidget(labelaction, self.projectlabel)

        self.stackedWidget.currentChanged.connect(self.updateUIState)

        self.panels = []
        self.infodock = QWidget()

        self.createMapTools()

    def setMapTool(self, tool, *args):
        self.canvas.setMapTool(tool)

    def createMapTools(self):
        def connectAction(action, tool):
            action.toggled.connect(partial(self.setMapTool, tool))

        self.zoomInTool = QgsMapToolZoom(self.canvas, False)
        self.zoomOutTool  = QgsMapToolZoom(self.canvas, True)
        self.panTool = QgsMapToolTouch(self.canvas)

        connectAction(self.actionZoom_In, self.zoomInTool)
        connectAction(self.actionZoom_Out, self.zoomOutTool)
        connectAction(self.actionPan, self.panTool)

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

        ismapview = page == self.actionpages[self.actionMap]
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

        self.messageBar.pushMessage("Project Loading","", QgsMessageBar.INFO)
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
        self.panels = []




