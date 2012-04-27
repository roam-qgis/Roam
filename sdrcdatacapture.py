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
import resources
from syncing.Syncer import SyncDialog, Syncer
import syncing.ui_sync
from utils import log

class SDRCDataCapture():
    def __init__(self, iface):
        self.iface = iface
        self.layerstoForms = {}
        self.actions = []
        self.navtoolbar = self.iface.mapNavToolToolBar()
        self.mainwindow = iface.mainWindow()
        self.iface.projectRead.connect(self.projectOpened)
        self.iface.initializationCompleted.connect(self.setupUI)
        self.settings = QSettings( "settings.ini", QSettings.IniFormat )
        self.actionGroup = QActionGroup(self.iface.mainWindow())

    def setupUI(self):
        self.iface.mainWindow().showFullScreen()
        self.navtoolbar.setMovable(False)
        self.navtoolbar.setAllowedAreas(Qt.TopToolBarArea)
        self.mainwindow.insertToolBar(self.toolbar, self.navtoolbar)
        self.openProject()
        
    def initGui(self):
        self.toolbar = QToolBar("SDRC Data Capture", self.mainwindow)
        self.mainwindow.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.setMovable(False)
        
        spacewidget = QWidget()
        spacewidget.setMinimumWidth(30)
        

        gpsspacewidget = QWidget()
        gpsspacewidget.setMinimumWidth(30)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.homeAction = QAction(QIcon(":/icons/home"), "Home View" , self.mainwindow)
        self.gpsAction = GPSAction(self.iface)
        self.openProjectAction = QAction(QIcon(":/icons/open"),"Open Project" , self.mainwindow)
        self.toggleRasterAction = QAction(QIcon(":/icons/photo"),"Aerial Photos" , self.mainwindow)
        self.editAction = EditAction("Edit", self.iface, self.layerstoForms )
        self.syncAction = QAction(QIcon(":/syncing/syncing/sync.png"), "Sync", self.mainwindow)

        self.editAction.setCheckable(True)

        self.actionGroup.addAction(self.editAction)

        self.homeAction.triggered.connect(self.zoomToHomeView)
        self.syncAction.triggered.connect(self.sync)
        self.openProjectAction.triggered.connect(self.openProject)
        self.toggleRasterAction.triggered.connect(self.toggleRasterLayers)

        self.navtoolbar.insertAction(self.iface.actionPan(),self.homeAction )
        self.navtoolbar.insertAction(self.homeAction, self.openProjectAction)

        self.navtoolbar.addAction(self.toggleRasterAction)
        self.navtoolbar.insertWidget(self.homeAction, spacewidget)
        self.toolbar.addAction(self.editAction)                        
        self.toolbar.addAction(self.syncAction)
        self.toolbar.insertSeparator(self.syncAction)
        self.toolbar.insertWidget(self.gpsAction, gpsspacewidget)
        self.toolbar.addAction(self.gpsAction)

        self.setupIcons()

    def zoomToHomeView(self):
        self.iface.mapCanvas().setExtent(self.homeextent)
        self.iface.mapCanvas().refresh()

    def toggleRasterLayers(self):
        legend = self.iface.legendInterface()
        #Freeze the canvas to save on UI refresh
        self.iface.mapCanvas().freeze()
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.RasterLayer:
                isvisible = legend.isLayerVisible(layer)
                legend.setLayerVisible(layer, not isvisible )
        self.iface.mapCanvas().freeze(False)
        #self.iface.mapCanvas().refresh()

    def setupIcons(self):
        """
            Update toolbars to have text and icons, change icons to new style
        """
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            toolbar.setIconSize(QSize(32,32))
            
        self.iface.actionZoomIn().setIcon(QIcon(":/icons/in"))
        self.iface.actionZoomOut().setIcon(QIcon(":/icons/out"))
        self.iface.actionPan().setIcon(QIcon(":/icons/pan"))
        
        self.actionGroup.addAction(self.iface.actionZoomIn())
        self.actionGroup.addAction(self.iface.actionZoomOut())
        self.actionGroup.addAction(self.iface.actionPan())

    def projectOpened(self):
        """
            Called when a new project is opened in QGIS.
        """
        layers = dict((str(x.name()), x) for x in QgsMapLayerRegistry.instance().mapLayers().values())
        self.createFormButtons(layers)
        self.homeextent = self.iface.mapCanvas().extent()
        
    def createFormButtons(self, layers):
        """
            Create buttons for each form that is definded
        """
        # Remove all the old buttons
        for action in self.actions:
            self.toolbar.removeAction(action)

        userForms = forms.getForms()
        
        for form in userForms:
            form = forms.loadFormModule(form)
            try:
                layer = layers[form.__layerName__]
                action = AddAction( form.__formName__, self.iface, form , layer )
                self.toolbar.insertAction(self.editAction, action)
                self.actionGroup.addAction(action)
                self.actions.append(action)
                self.layerstoForms[layer] = form
            except KeyError:
                log("Couldn't find layer for form %s" % form.__layerName__)

    def openProject(self):
        self.dialog = ListProjectsDialog()
        self.dialog.requestOpenProject.connect(self.loadProject)
        self.dialog.setModal(True)
        self.dialog.show()
        QCoreApplication.processEvents()
        curdir= os.path.dirname(__file__)
        path =os.path.join(curdir,'projects/')
        #paths = self.settings.value("/projects/projectLocations", [path]).toList()
        self.dialog.loadProjectList([path])

    def loadProject(self, path):
        self.dialog.close()
        self.iface.addProject(path)
    
    def unload(self):
        del self.toolbar

    def sync(self):
        self.syndlg = SyncDialog()
        self.syndlg.setModal(True)
        self.syndlg.show()
        # HACK 
        QCoreApplication.processEvents()
        self.syndlg.runSync()
        self.iface.mapCanvas().refresh()