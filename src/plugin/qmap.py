"""
/***************************************************************************
 QMap
                                 A QGIS plugin
 Data collection software for QGIS
                              -------------------
        begin                : 2012-03-21
        copyright            : (C) 2012 by Nathan Woodrow @ SDRC
        email                : nathan.woodrow@southerndowns.qld.gov.au
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from add_action import AddAction
from edit_action import EditAction
from gps_action import GPSAction
from movetool import MoveTool
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import qmaplayer
from listmodulesdialog import ListProjectsDialog
from qgis.core import *
from qgis.gui import QgsMapToolZoom, QgsMapTool
import resources_rc
from syncing.syncdialog import SyncDialog
from utils import log
import functools
import utils
from floatingtoolbar import FloatingToolBar
from syncing.syncer import syncproviders


class QMap():
    layerformmap = {}

    def __init__(self, iface):
        self.iface = iface
        self.layerstoForms = {}
        self.actions = []
        self.navtoolbar = self.iface.mapNavToolToolBar()
        self.mainwindow = iface.mainWindow()
        self.iface.projectRead.connect(self.projectOpened)
        self.iface.initializationCompleted.connect(self.setupUI)
        self.actionGroup = QActionGroup(self.iface.mainWindow())
        self.actionGroup.setExclusive(True)
        # self.editActionGroup = QActionGroup(self.iface.mainWindow())
        # self.editActionGroup.setExclusive(True)
        self.iface.mapCanvas().grabGesture(Qt.PinchGesture)
        self.iface.mapCanvas().viewport().setAttribute(Qt.WA_AcceptTouchEvents)
        self.movetool = MoveTool(iface.mapCanvas()) 

    def setupUI(self):
        """
        Set up the main QGIS interface items.  Called after QGIS has loaded
        the plugin.
        """
        self.iface.mainWindow().setWindowTitle("QMap: A data collection program for QGIS")
        fullscreen = utils.settings["fullscreen"]
        if fullscreen:
            self.iface.mainWindow().showFullScreen()
        else:
            self.iface.mainWindow().showMaximized()

        self.navtoolbar.setMovable(False)
        self.navtoolbar.setAllowedAreas(Qt.TopToolBarArea)
        self.mainwindow.insertToolBar(self.toolbar, self.navtoolbar)
        self.showOpenProjectDialog()

    def setMapTool(self, tool):
        """
        Set the current map canvas tool

        tool -- The QgsMapTool to set
        """
        self.iface.mapCanvas().setMapTool(tool)

    def createToolBars(self):
        """
        Create all the needed toolbars
        """
        self.toolbar = QToolBar("QMap", self.mainwindow)
        self.mainwindow.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.setMovable(False)

        self.editingtoolbar = FloatingToolBar("Editing", self.toolbar)
        self.extraaddtoolbar = FloatingToolBar("Extra Add Tools", self.toolbar)

    def createActions(self):
        """
        Create all the actions
        """

        self.homeAction = (QAction(self.iface.actionZoomFullExtent().icon(),
                                  "Default View", self.mainwindow))
        self.gpsAction = (GPSAction(QIcon(":/icons/gps"), self.iface.mapCanvas(),
                                   self.mainwindow))
        self.openProjectAction = (QAction(QIcon(":/icons/open"), "Open Project",
                                         self.mainwindow))
        self.toggleRasterAction = (QAction(QIcon(":/icons/photo"), "Aerial Photos",
                                          self.mainwindow))
        self.syncAction = QAction(QIcon(":/syncing/sync"), "Sync", self.mainwindow)

        self.editattributesaction = EditAction("Edit Attributes", self.iface)
        self.editattributesaction.setCheckable(True)

        self.moveaction = QAction(QIcon(":/icons/move"), "Move Feature", self.mainwindow)
        self.moveaction.setCheckable(True)

        self.editingmodeaction = QAction(QIcon(":/icons/edittools"), "Editing Tools", self.mainwindow)
        self.editingmodeaction.setCheckable(True)

        self.addatgpsaction = QAction(QIcon(":/icons/gpsadd"), "Add at GPS", self.mainwindow)

    def initGui(self):
        """
        Create all the icons and setup the tool bars.  Called by QGIS when
        loading. This is called before setupUI.
        """

        def createSpacer():
            widget = QWidget()
            widget.setMinimumWidth(30)
            return widget

        self.createToolBars()
        self.createActions()

        spacewidget = createSpacer()
        gpsspacewidget = createSpacer()
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.moveaction.toggled.connect(functools.partial(self.setMapTool, self.movetool))
        
        showediting = (functools.partial(self.editingtoolbar.showToolbar, 
                                         self.editingmodeaction,
                                         self.editattributesaction))
        self.editingmodeaction.toggled.connect(showediting)

        self.addatgpsaction.triggered.connect(self.addAtGPS)
        self.addatgpsaction.setEnabled(self.gpsAction.isConnected)
        self.gpsAction.gpsfixed.connect(self.addatgpsaction.setEnabled)

        self.menu = QMenu()
        self.exitaction = self.menu.addAction("Exit")
        self.exitaction.setIcon(QIcon(":/icons/exit"))
        self.exitaction.triggered.connect(self.iface.actionExit().trigger)
        self.openProjectAction.setMenu(self.menu)

        self.editingtoolbar.addToActionGroup(self.editattributesaction)
        self.editingtoolbar.addToActionGroup(self.moveaction)

        self.actionGroup.addAction(self.editingmodeaction)

        self.homeAction.triggered.connect(self.zoomToDefaultView)
        self.syncAction.triggered.connect(self.sync)
        self.openProjectAction.triggered.connect(self.showOpenProjectDialog)
        self.toggleRasterAction.triggered.connect(self.toggleRasterLayers)

        self.navtoolbar.insertAction(self.iface.actionZoomIn(), self.iface.actionTouch())
        self.navtoolbar.insertAction(self.iface.actionTouch(), self.homeAction)
        self.navtoolbar.insertAction(self.iface.actionTouch(), self.iface.actionZoomFullExtent())
        self.navtoolbar.insertAction(self.homeAction, self.iface.actionZoomFullExtent())
        self.navtoolbar.insertAction(self.iface.actionZoomFullExtent(), self.openProjectAction)

        self.navtoolbar.addAction(self.toggleRasterAction)
        self.navtoolbar.insertWidget(self.iface.actionZoomFullExtent(), spacewidget)
        self.toolbar.addAction(self.editingmodeaction)
        self.toolbar.addAction(self.syncAction)
        self.toolbar.addAction(self.gpsAction)
        self.toolbar.insertWidget(self.syncAction, gpsspacewidget)
        self.toolbar.insertSeparator(self.gpsAction)

        self.extraaddtoolbar.addAction(self.addatgpsaction)

        self.editingtoolbar.addAction(self.editattributesaction)
        self.editingtoolbar.addAction(self.moveaction)

        self.setupIcons()

    def addAtGPS(self):
        """
        Add a record at the current GPS location.
        """
        action = self.actionGroup.checkedAction()
        log(action)
        if action:
            point = self.gpsAction.gpsLocation
            try:
                action.pointClick(point)
            except AttributeError:
                pass

    def zoomToDefaultView(self):
        """
        Zoom the map canvas to the extents the project was opened at i.e. the
        default extent.
        """
        self.iface.mapCanvas().setExtent(self.defaultextent)
        self.iface.mapCanvas().refresh()

    def toggleRasterLayers(self):
        """
        Toggle all raster layers on or off.
        """
        legend = self.iface.legendInterface()
        #Freeze the canvas to save on UI refresh
        self.iface.mapCanvas().freeze()
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.RasterLayer:
                isvisible = legend.isLayerVisible(layer)
                legend.setLayerVisible(layer, not isvisible)
        self.iface.mapCanvas().freeze(False)
        self.iface.mapCanvas().refresh()

    def hasRasterLayers(self):
        """
        Check if the project has any raster layers.

        Returns: True if there is a raster layer, else False.
        """
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.RasterLayer:
                return True
        return False

    def setupIcons(self):
        """
        Update toolbars to have text and icons, change normal QGIS
        icons to new style
        """
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            toolbar.setIconSize(QSize(32, 32))

        self.iface.actionTouch().setIconText("Pan")
        self.iface.actionTouch().setIcon(QIcon(":/icons/pan"))
        self.iface.actionZoomIn().setIcon(QIcon(":/icons/in"))
        self.iface.actionZoomOut().setIcon(QIcon(":/icons/out"))
        self.iface.actionPan().setIcon(QIcon(":/icons/pan"))
        self.iface.actionZoomFullExtent().setIcon(QIcon(":/icons/home"))
        self.iface.actionZoomFullExtent().setIconText("Home View")

        self.actionGroup.addAction(self.iface.actionZoomIn())
        self.actionGroup.addAction(self.iface.actionZoomOut())
        self.actionGroup.addAction(self.iface.actionTouch())

    def projectOpened(self):
        """
            Called when a new project is opened in QGIS.
        """
        layers = dict((str(x.name()), x) for x in QgsMapLayerRegistry.instance().mapLayers().values())
        
        path = str(QgsProject.instance().fileName())
        projectname = os.path.basename(path)[:-4]
        projectsettings = utils.settings["projects"][projectname]
        
        self.createFormButtons(layers, projectsettings)
        self.defaultextent = self.iface.mapCanvas().extent()
        
        # Enable the raster layers button only if the project contains a raster layer.
        self.toggleRasterAction.setEnabled(self.hasRasterLayers())

    def createFormButtons(self, projectlayers, projectsettings):
        """
            Create buttons for each form that is definded
        """
        layerstoForms = {}

        # Remove all the old buttons
        for action in self.actions:
            self.toolbar.removeAction(action)
            
        formlayers = projectsettings["layers"]
        
        for layer, options in formlayers.iteritems():
            try:
                qgslayer = projectlayers[layer]
                text = options['text']
                                
                action = AddAction(text, self.iface, qgslayer, QIcon())
                
                self.toolbar.insertAction(self.editingmodeaction, action)
                
                showgpstools = (functools.partial(self.extraaddtoolbar.showToolbar, 
                                             action,
                                             None))
                action.toggled.connect(showgpstools)
                self.actionGroup.addAction(action)
                self.actions.append(action)
                layerstoForms[qgslayer] = None
                
            except KeyError:
                log("Layer not found in project")
                continue
            
        QMap.layerformmap = layerstoForms

    def rejectProjectDialog(self):
        """
        Handler for rejected open project dialog.
        """
        if QgsProject.instance().fileName() is None:
            self.setUIState(False)
            self.openProjectAction.setEnabled(True)
        else:
            self.setUIState(True)

    def setUIState(self, enabled):
        """
        Enable or disable the toolbar.

        enabled -- True to enable all the toolbar icons.
        """
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setEnabled(enabled)

    def showOpenProjectDialog(self):
        """
        Show the project selection dialog.
        """
        self.setUIState(False)
        self.dialog = ListProjectsDialog()
        self.dialog.requestOpenProject.connect(self.loadProject)
        self.dialog.requestOpenProject.connect(self.dialog.close)
        self.dialog.rejected.connect(self.rejectProjectDialog)
        self.dialog.resize(self.iface.mapCanvas().size())
        point = self.iface.mapCanvas().geometry().topLeft()
        point = self.iface.mapCanvas().mapToGlobal(point)
        self.dialog.move(point)
        self.dialog.setModal(True)
        self.dialog.show()
        QCoreApplication.processEvents()
        curdir = os.path.dirname(__file__)
        path = os.path.join(curdir, 'projects/')
        self.dialog.loadProjectList([path])

    def loadProject(self, path):
        """
        Load a project into QGIS.

        path -- The path to the .qgs project file.
        """
        self.iface.addProject(path)
        self.setUIState(True)

    def unload(self):
        del self.toolbar

    def sync(self):
        """
        Open and run the sync.  Shows the sync dialog.

        notes: Blocking the user while we wait for syncing is not very nice.
               Maybe we can do it in the background and show the dialog as non
               model and report pass/fail.
        """
        self.syndlg = SyncDialog()
        self.syndlg.setModal(True)
        self.syndlg.show()
        # HACK
        QCoreApplication.processEvents()
        self.syndlg.runSync(syncproviders)
        self.iface.mapCanvas().refresh()