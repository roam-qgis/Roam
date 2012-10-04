"""
/***************************************************************************
 SDRCDataCapture
                                 A QGIS plugin
 Data collection software for SDRC
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import forms
from listmodulesdialog import ListProjectsDialog
from qgis.core import *
from qgis.gui import QgsMapToolZoom, QgsMapTool
import resources_rc
from syncing.syncer import SyncDialog
from utils import log
import functools
import utils


class SDRCDataCapture():
    def __init__(self, iface):
        self.iface = iface
        self.layerstoForms = {}
        self.actions = []
        self.navtoolbar = self.iface.mapNavToolToolBar()
        self.mainwindow = iface.mainWindow()
        self.iface.projectRead.connect(self.projectOpened)
        self.iface.initializationCompleted.connect(self.setupUI)
        self.actionGroup = QActionGroup(self.iface.mainWindow())
        self.iface.mapCanvas().grabGesture(Qt.PinchGesture)
        self.iface.mapCanvas().viewport().setAttribute(Qt.WA_AcceptTouchEvents) 

    def setupUI(self):
        """
        Set up the main QGIS interface items.  Called after QGIS has loaded
        the plugin.
        """
        self.iface.mainWindow().setWindowTitle("QMap: A data collection program for QGIS")
        fullscreen = utils.settings.value("fullscreen").toBool()
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

    def initGui(self):
        """
        Create all the icons and setup the tool bars.  Called by QGIS when
        loading. This is called before setupUI.
        """
        self.toolbar = QToolBar("SDRC Data Capture", self.mainwindow)
        self.mainwindow.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.setMovable(False)

        spacewidget = QWidget()
        spacewidget.setMinimumWidth(30)

        gpsspacewidget = QWidget()
        gpsspacewidget.setMinimumWidth(30)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.homeAction = QAction(self.iface.actionZoomFullExtent().icon(), \
                                  "Default View", self.mainwindow)
        self.gpsAction = GPSAction(QIcon(":/icons/gps"), self.iface.mapCanvas(), \
                                   self.mainwindow)
        self.openProjectAction = QAction(QIcon(":/icons/open"), "Open Project", \
                                         self.mainwindow)
        self.toggleRasterAction = QAction(QIcon(":/icons/photo"), "Aerial Photos",\
                                          self.mainwindow)
        self.editAction = EditAction("Edit", self.iface)
        self.syncAction = QAction(QIcon(":/syncing/sync"), "Sync", self.mainwindow)
        self.editAction.setCheckable(True)

        self.actionGroup.addAction(self.editAction)

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
        self.toolbar.addAction(self.editAction)
        self.toolbar.addAction(self.syncAction)
        self.toolbar.insertSeparator(self.syncAction)
        self.toolbar.insertWidget(self.gpsAction, gpsspacewidget)
        self.toolbar.addAction(self.gpsAction)

        self.setupIcons()

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
        self.createFormButtons(layers)
        self.defaultextent = self.iface.mapCanvas().extent()
        # Enable the raster layers button only if the project contains a raster layer.
        self.toggleRasterAction.setEnabled(self.hasRasterLayers())

    def createFormButtons(self, layers):
        """
            Create buttons for each form that is definded
        """
        layerstoForms = {}

        # Remove all the old buttons
        for action in self.actions:
            self.toolbar.removeAction(action)

        userForms = forms.getForms()

        for form in userForms:
            try:
                layer = layers[form.layerName()]
                icon = form.icon()
                action = AddAction(form.formName(), self.iface, \
                                   form, layer, icon)
                self.toolbar.insertAction(self.editAction, action)
                self.actionGroup.addAction(action)
                self.actions.append(action)
                layerstoForms[layer] = form
            except KeyError:
                log("Couldn't find layer for form %s" % form.layerName())

        self.editAction.setLayersForms(layerstoForms)

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
        self.syndlg.runSync()
        self.iface.mapCanvas().refresh()