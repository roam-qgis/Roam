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
import qmaplayer
import resources_rc
import functools
import utils
import json

from edit_action import EditAction
from gps_action import GPSAction
from maptools import MoveTool, PointTool
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebView, QWebPage
from listmodulesdialog import ListProjectsDialog
from qgis.core import *
from qgis.gui import QgsMessageBar
from utils import log
from floatingtoolbar import FloatingToolBar
from syncing import replication
from dialog_provider import DialogProvider

currentproject = None

class QMap():
    layerformmap = []

    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.navtoolbar = self.iface.mapNavToolToolBar()
        self.mainwindow = iface.mainWindow()
        self.iface.projectRead.connect(self.projectOpened)
        self.iface.initializationCompleted.connect(self.setupUI)
        self.actionGroup = QActionGroup(self.iface.mainWindow())
        self.actionGroup.setExclusive(True)
        self.iface.mapCanvas().grabGesture(Qt.PinchGesture)
        self.iface.mapCanvas().viewport().setAttribute(Qt.WA_AcceptTouchEvents)
        self.movetool = MoveTool(iface.mapCanvas(), QMap.layerformmap )
        self.report = SyncReport(self.iface.messageBar())
        self.dialogprovider = DialogProvider(iface.mapCanvas(), iface)

    def setupUI(self):
        """
        Set up the main QGIS interface items.  Called after QGIS has loaded
        the plugin.
        """
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

        self.homeAction = (QAction(QIcon(":/icons/zoomfull"),
                                  "Default View", self.mainwindow))
        self.gpsAction = (GPSAction(QIcon(":/icons/gps"), self.iface.mapCanvas(),
                                   self.mainwindow))
        self.openProjectAction = (QAction(QIcon(":/icons/open"), "Open Project",
                                         self.mainwindow))
        self.toggleRasterAction = (QAction(QIcon(":/icons/photo"), "Aerial Photos",
                                          self.mainwindow))
        self.syncAction = QAction(QIcon(":/icons/sync"), "Sync", self.mainwindow)
        self.syncAction.setVisible(False)

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
        
        QApplication.setWindowIcon(QIcon(":/branding/logo"))

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
        self.iface.mainWindow().findChildren(QMenuBar)[0].setVisible(False)
        self.iface.mainWindow().setStyleSheet("QToolBar {background-color:white}")
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
        
        self.connectSyncProviders()
        
        for layer in QgsMapLayerRegistry.instance().mapLayers().itervalues():
            form = layer.editForm()
            if not form.endsWith(".ui"): 
                continue
            self.iface.preloadForm(form)

    def createFormButtons(self, projectlayers):
        """
            Create buttons for each form that is definded
        """
        # Remove all the old buttons
        for action in self.actions:
            self.toolbar.removeAction(action)
        
        folder = currentproject.folder
        layerfolders = ( [os.path.join(folder, item) for item in os.walk(folder).next()[1] 
                                                    if not item.startswith('_')])
        
        for layer in layerfolders:
            try:
                name = os.path.basename(layer)
                qgslayer = projectlayers[name]
            except KeyError:
                log("Layer not found in project")
                continue
            
            text = name
            icon = os.path.join(layer, 'icon.png')
                  
            if qgslayer.geometryType() == QGis.Point:
                tool = PointTool(self.iface.mapCanvas())
                add = functools.partial(self.addNewFeature, qgslayer)
            else:
                log("Geometry type not supported yet")
                continue
            
            tool.geometryComplete.connect(add)
                
            action = QAction(QIcon(icon), text, self.mainwindow)
            action.setCheckable(True)
            action.toggled.connect(functools.partial(self.setMapTool, tool))
            
            self.toolbar.insertAction(self.editingmodeaction, action)
            
            # Connect the GPS tools strip to the action pressed event.                
            showgpstools = (functools.partial(self.extraaddtoolbar.showToolbar, 
                                         action,
                                         None))
            
            action.toggled.connect(showgpstools)
            self.actionGroup.addAction(action)
            self.actions.append(action)
            QMap.layerformmap.append(qgslayer)
            
    def addNewFeature(self, layer, geometry):
        fields = layer.pendingFields()
        
        if not layer.isEditable():
            layer.startEditing()
    
        feature = QgsFeature()
        feature.setGeometry( geometry )
        feature.initAttributes(fields.count())
        feature.setFields(fields)
        
        for indx in xrange(fields.count()):
            feature[indx] = layer.dataProvider().defaultValue( indx )

        self.dialogprovider.openDialog( feature, layer, False )

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
        dialog = ListProjectsDialog()
        path = os.path.join(os.path.dirname(__file__), '..' , 'projects/')
        dialog.loadProjectList(path)
        dialog.resize(self.iface.mapCanvas().size())
        point = self.iface.mapCanvas().geometry().topLeft()
        point = self.iface.mapCanvas().mapToGlobal(point)
        dialog.move(point)
        dialog.setModal(True)
        dialog.show()
        
        if dialog.exec_():
            self.loadProject(dialog.selectedProject)
        else:
            self.setUIState(True)   

    def loadProject(self, project):
        """
        Load a project into QGIS.

        path -- The path to the .qgs project file.
        """

        self.iface.newProject(False)
        
        global currentproject
        currentproject = project
        
        self.iface.mapCanvas().freeze()

        fileinfo = QFileInfo(project.file)
        QgsProject.instance().read(fileinfo)
        
        self.iface.mapCanvas().updateScale()
        
        self.iface.mapCanvas().freeze(False)
        self.iface.mapCanvas().refresh()
        
        self.iface.mainWindow().setWindowTitle("QMap: QGIS Data Collection")
        
        self.iface.projectRead.emit()
        self.setUIState(True)

    def unload(self):
        del self.toolbar
        
    def connectSyncProviders(self):
        projectfolder = currentproject.folder
        settings = os.path.join(projectfolder, "settings.config")
        try:
            with open(settings,'r') as f:
                settings = json.load(f)
        except IOError:
            log("No sync providers configured")
            return
        
        syncactions = []
        for name, config in settings["providers"].iteritems():
            cmd = config['cmd']
            cmd = os.path.join(projectfolder, cmd)
            if config['type'] == 'replication':
                provider = replication.ReplicationSync(name, cmd)          
                syncactions.append(provider)
                
        if len(syncactions) == 1: 
            # If one provider is set then we just show a single button.
            self.syncAction.setVisible(True)
            self.syncAction.triggered.connect(functools.partial(self.syncProvider, syncactions[0]))
        else:
            self.syncAction.setVisible(False)
                
    def syncstarted(self):                   
        # Remove the old widget if it's still there.
        # I don't really like this. Seems hacky.
        try:
            self.iface.messageBar().popWidget(self.syncwidget)
        except RuntimeError:
            pass
        except AttributeError:
            pass
        
        self.iface.messageBar().findChildren(QToolButton)[0].setVisible(False)        
        self.syncwidget = self.iface.messageBar().createMessage("Syncing", "Sync in progress", QIcon(":/icons/syncing"))
        button = QPushButton(self.syncwidget)
        button.setCheckable(True)
        button.setText("Status")
        button.setIcon(QIcon(":/icons/syncinfo"))
        button.toggled.connect(functools.partial(self.report.setVisible))
        self.syncwidget.layout().addWidget(button)
        self.iface.messageBar().pushWidget(self.syncwidget, QgsMessageBar.INFO)
        
    def synccomplete(self):
        try:
            self.iface.messageBar().popWidget(self.syncwidget)
        except RuntimeError:
            pass
        
        stylesheet = ("QgsMessageBar { background-color: rgba(239, 255, 233); border: 0px solid #b9cfe4; } "
                     "QLabel,QTextEdit { color: #057f35; } ")
        
        closebutton = self.iface.messageBar().findChildren(QToolButton)[0]
        closebutton.setVisible(True)
        closebutton.clicked.connect(functools.partial(self.report.setVisible, False))
        self.syncwidget = self.iface.messageBar().createMessage("Syncing", "Sync Complete", QIcon(":/icons/syncdone"))
        button = QPushButton(self.syncwidget)
        button.setCheckable(True)
        button.setChecked(self.report.isVisible())
        button.setText("Sync Report")
        button.setIcon(QIcon(":/icons/syncinfo"))
        button.toggled.connect(functools.partial(self.report.setVisible))            
        self.syncwidget.layout().addWidget(button)
        self.iface.messageBar().pushWidget(self.syncwidget)
        self.iface.messageBar().setStyleSheet(stylesheet)
        self.iface.mapCanvas().refresh()
        
    def syncerror(self):
        try:
            self.iface.messageBar().popWidget(self.syncwidget)
        except RuntimeError:
            pass
        
        closebutton = self.iface.messageBar().findChildren(QToolButton)[0]
        closebutton.setVisible(True)
        closebutton.clicked.connect(functools.partial(self.report.setVisible, False))
        self.syncwidget = self.iface.messageBar().createMessage("Syncing", "Sync Error", QIcon(":/icons/syncfail"))
        button = QPushButton(self.syncwidget)
        button.setCheckable(True)
        button.setChecked(self.report.isVisible())
        button.setText("Sync Report")
        button.setIcon(QIcon(":/icons/syncinfo"))
        button.toggled.connect(functools.partial(self.report.setVisible))            
        self.syncwidget.layout().addWidget(button)
        self.iface.messageBar().pushWidget(self.syncwidget, QgsMessageBar.CRITICAL)
        self.iface.mapCanvas().refresh()
        
    def syncProvider(self, provider):       
        provider.syncStarted.connect(functools.partial(self.syncAction.setEnabled, False))
        provider.syncStarted.connect(self.syncstarted)
        
        provider.syncComplete.connect(self.synccomplete)
        provider.syncComplete.connect(functools.partial(self.syncAction.setEnabled, True))
        provider.syncComplete.connect(functools.partial(self.report.updateHTML))
        
        provider.syncMessage.connect(self.report.updateHTML)
        
        provider.syncError.connect(self.report.updateHTML)
        provider.syncError.connect(self.syncerror)
        
        provider.startSync()
        
class SyncReport(QDialog):
    def __init__(self, parent=None):
        super(SyncReport, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.web = QWebView()
        self.resize(400,400)
        self.layout().addWidget(self.web)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint)
        
    def updateHTML(self, html):
        self.web.setHtml(html)
        self.web.triggerPageAction(QWebPage.MoveToEndOfDocument)
        
    def clear(self):
        self.web.setHtml("No Sync in progress")
        
    def updatePosition(self):
        point = self.parent().rect().bottomRight()
        newpoint = self.parent().mapToGlobal(point - QPoint(self.size().width(),0))
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint)
        self.move(newpoint)
        
    def showEvent(self, event):
        self.updatePosition()
        