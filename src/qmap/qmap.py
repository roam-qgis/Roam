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
import sys

from gps_action import GPSAction
from maptools import MoveTool, PointTool, EditTool
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebView, QWebPage
from listmodulesdialog import ProjectsWidget
from qgis.core import *
from qgis.gui import QgsMessageBar
from utils import log, critical, warning
from floatingtoolbar import FloatingToolBar
from dialog_provider import DialogProvider
import traceback
from PyQt4.uic import loadUi
from project import QMapProject, NoMapToolConfigured, getProjects, ErrorInMapTool
from ui_helppage import Ui_apphelpwidget

class BadLayerHandler( QgsProjectBadLayerHandler):
    def __init__( self, callback ):
        super(BadLayerHandler, self).__init__()
        self.callback = callback

    def handleBadLayers( self, domNodes, domDocument ):
        layers = [node.namedItem("layername").toElement().text() for node in domNodes]
        self.callback(layers)

class HelpPage(QWidget):
    def __init__(self, parent=None):
        super(HelpPage, self).__init__(parent)
        self.ui = Ui_apphelpwidget()
        self.ui.setupUi(self)
        
    def setHelpPage(self, helppath):
        self.ui.webView.load(QUrl.fromLocalFile(helppath))

class QMap():
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.panels= []
        self.navtoolbar = self.iface.mapNavToolToolBar()
        self.mainwindow = self.iface.mainWindow()
        self.iface.projectRead.connect(self.projectOpened)
        self.iface.initializationCompleted.connect(self.setupUI)
        self.actionGroup = QActionGroup(self.mainwindow)
        self.actionGroup.setExclusive(True)
        self.menuGroup = QActionGroup(self.mainwindow)
        self.menuGroup.setExclusive(True)
                
        self.movetool = MoveTool(self.iface.mapCanvas(), [])
        self.report = PopDownReport(self.iface.messageBar())
        
        self.dialogprovider = DialogProvider(iface.mapCanvas(), iface)
        self.dialogprovider.accepted.connect(self.clearToolRubberBand)
        self.dialogprovider.rejected.connect(self.clearToolRubberBand)
        
        self.edittool = EditTool(self.iface.mapCanvas(),[])
        self.edittool.finished.connect(self.openForm)

    @property
    def _mapLayers(self):
        return QgsMapLayerRegistry.instance().mapLayers()
        
    def clearToolRubberBand(self):
        tool = self.iface.mapCanvas().mapTool()
        try:
            tool.clearBand()
        except AttributeError:
            # No clearBand method found, but that's cool.
            pass
        
    def missingLayers(self, layers):
        def showError():
            html = ["<h1>Missing Layers</h1>", "<ul>"]
            for layer in layers:
                html.append("<li>{}</li>".format(layer))
            html.append("</ul>")
            
            self.errorreport.updateHTML("".join(html))
        
        message = "Seems like {} didn't load correctly".format(utils._pluralstring('layer', len(layers)))
        
        warning("Missing layers")
        map(warning, layers)
            
        self.widget = self.messageBar.createMessage("Missing Layers", 
                                                 message, 
                                                 QIcon(":/icons/sad"))
        button = QPushButton(self.widget)
        button.setCheckable(True)
        button.setChecked(self.errorreport.isVisible())
        button.setText("Show missing layers")
        button.toggled.connect(showError)
        button.toggled.connect(functools.partial(self.errorreport.setVisible))
        self.widget.destroyed.connect(self.hideReports)
        self.widget.layout().addWidget(button)
        self.messageBar.pushWidget(self.widget, QgsMessageBar.WARNING)
        
    def excepthook(self, ex_type, value, tb):
        """ 
        Custom exception hook so that we can handle errors in a
        nicer way
        """
        where = ''.join(traceback.format_tb(tb))
        msg = '{}'.format(value)
        critical(msg)
        
        def showError():
            html = """
                <html>
                <body bgcolor="#FFEDED">
                <p><b>{}</b></p>
                <p align="left"><small>{}</small></p>
                </body>
                </html>
            """.format(msg, where)
            self.errorreport.updateHTML(html)
        
        self.widget = self.messageBar.createMessage("oops", "Looks like an error occurred", QIcon(":/icons/sad"))
        button = QPushButton(self.widget)
        button.setCheckable(True)
        button.setChecked(self.errorreport.isVisible())
        button.setText("Show error")
        button.toggled.connect(showError)
        button.toggled.connect(functools.partial(self.errorreport.setVisible))
        self.widget.destroyed.connect(self.hideReports)
        self.widget.layout().addWidget(button)
        self.messageBar.pushWidget(self.widget, QgsMessageBar.CRITICAL)
    
    def hideReports(self):
        self.errorreport.setVisible(False)
        self.report.setVisible(False)
    
    def setupUI(self):
        """
        Set up the main QGIS interface items.  Called after QGIS has loaded
        the plugin.
        """
        fullscreen = utils.settings["fullscreen"]
        if fullscreen:
            self.mainwindow.showFullScreen()
        else:
            self.mainwindow.showMaximized()

        self.navtoolbar.setMovable(False)
        self.navtoolbar.setAllowedAreas(Qt.TopToolBarArea)
        
        self.mainwindow.insertToolBar(self.toolbar, self.navtoolbar)
        self.openProjectAction.trigger()

    def setMapTool(self, tool):
        """
        Set the current mapview canvas tool

        tool -- The QgsMapTool to set
        """
        self.iface.mapCanvas().setMapTool(tool)

    def createToolBars(self):
        """
        Create all the needed toolbars
        """
        
        self.menutoolbar = QToolBar("Menu", self.mainwindow)
        self.menutoolbar.setMovable(False)
        self.menutoolbar.setAllowedAreas(Qt.LeftToolBarArea)
        self.mainwindow.addToolBar(Qt.LeftToolBarArea, self.menutoolbar)
        
        self.toolbar = QToolBar("QMap", self.mainwindow)
        self.mainwindow.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.setMovable(False)

        self.editingtoolbar = FloatingToolBar("Editing", self.toolbar)
        self.extraaddtoolbar = FloatingToolBar("Extra Add Tools", self.toolbar)
        self.syncactionstoolbar = FloatingToolBar("Syncing", self.toolbar)
        self.syncactionstoolbar.setOrientation(Qt.Vertical)

    def createActions(self):
        """
        Create all the actions
        """

        self.homeAction = (QAction(QIcon(":/icons/zoomfull"),
                                  "Default View", self.mainwindow))
        self.gpsAction = (GPSAction(QIcon(":/icons/gps"), self.iface.mapCanvas(),
                                   self.mainwindow))
        self.openProjectAction = (QAction(QIcon(":/icons/open"), "Projects",
                                         self.mainwindow))
        self.openProjectAction.setCheckable(True)
        self.toggleRasterAction = (QAction(QIcon(":/icons/photo"), "Aerial Photos",
                                          self.mainwindow))
        self.syncAction = QAction(QIcon(":/icons/sync"), "Sync", self.mainwindow)
        self.syncAction.setVisible(False)
        
        self.editattributesaction = QAction(QIcon(":/icons/edit"), "Edit Attributes", self.mainwindow)
        self.editattributesaction.setCheckable(True)
        self.editattributesaction.toggled.connect(functools.partial(self.setMapTool, self.edittool))

        self.moveaction = QAction(QIcon(":/icons/move"), "Move Feature", self.mainwindow)
        self.moveaction.setCheckable(True)

        self.editingmodeaction = QAction(QIcon(":/icons/edittools"), "Editing Tools", self.mainwindow)
        self.editingmodeaction.setCheckable(True)

        self.addatgpsaction = QAction(QIcon(":/icons/gpsadd"), "Add at GPS", self.mainwindow)
        
        self.edittool.layersupdated.connect(self.editattributesaction.setVisible)
        self.movetool.layersupdated.connect(self.moveaction.setVisible)
        self.edittool.layersupdated.connect(self.updateEditTools)
        self.movetool.layersupdated.connect(self.updateEditTools)
        
    def updateEditTools(self, *args):
        """
            Show or hide the Editing Tools button based on the sub tools.
        """
        if self.edittool.layers and self.movetool.layers:  
            self.editingmodeaction.setVisible(True)
        else:
            self.editingmodeaction.setVisible(False)

    def initGui(self):
        """
        Create all the icons and setup the tool bars.  Called by QGIS when
        loading. This is called before setupUI.
        """
        QApplication.setWindowIcon(QIcon(":/branding/logo"))
        self.mainwindow.findChildren(QMenuBar)[0].setVisible(False)
        self.mainwindow.setContextMenuPolicy(Qt.PreventContextMenu)
        self.mainwindow.setWindowTitle("IntraMaps Roam: Mobile Data Collection")
        
        # Disable QGIS logging window popups. We do our own logging
        QgsMessageLog.instance().messageReceived.disconnect()
        
        s = """
        QToolButton { 
            padding: 6px;
            color: #4f4f4f;
         }
        
        QToolButton:hover { 
            padding: 6px;
            background-color: rgb(211, 228, 255);
         }
         
        QToolBar {
         background: white;
        }
        
        QCheckBox::indicator {
             width: 40px;
             height: 40px;
         }
        
        QLabel {
            color: #4f4f4f;
        }
        
        QDialog { background-color: rgb(255, 255, 255); }
        
        QPushButton { 
            border: 1px solid #e1e1e1;
             padding: 6px;
            color: #4f4f4f;
         }
        
        QPushButton:hover { 
            border: 1px solid #e1e1e1;
             padding: 6px;
            background-color: rgb(211, 228, 255);
         }
        
        QCheckBox {
            color: #4f4f4f;
        }
        
        QComboBox::drop-down {
            width: 30px;
        }


        """
        self.mainwindow.setStyleSheet(s)
        
        mainwidget = self.mainwindow.centralWidget()
        mainwidget.setLayout(QGridLayout())
        mainwidget.layout().setContentsMargins(0,0,0,0)
        
        newlayout = QGridLayout()
        newlayout.setContentsMargins(0,0,0,0)
        newlayout.addWidget(self.iface.mapCanvas(), 0,0,2,1)
        newlayout.addWidget(self.iface.messageBar(), 0,0,1,1)
        
        wid = QWidget()
        wid.setLayout(newlayout)
        
        self.stack = QStackedWidget()
        self.messageBar = QgsMessageBar(wid)
        self.messageBar.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed )
        self.errorreport = PopDownReport(self.messageBar)
         
        mainwidget.layout().addWidget(self.stack, 0,0,2,1)
        mainwidget.layout().addWidget(self.messageBar, 0,0,1,1)
        
        self.helppage = HelpPage()
        helppath = os.path.join(os.path.dirname(__file__) , 'help',"help.html")
        self.helppage.setHelpPage(helppath)
        
        self.projectwidget = ProjectsWidget()   
        self.projectwidget.requestOpenProject.connect(self.loadProject)
        self.stack.addWidget(wid)
        self.stack.addWidget(self.projectwidget)
        self.stack.addWidget(self.helppage)
                
        sys.excepthook = self.excepthook

        def createSpacer(width=30):
            widget = QWidget()
            widget.setMinimumWidth(width)
            return widget

        self.createToolBars()
        self.createActions()

        spacewidget = createSpacer(60)
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

        self.editingtoolbar.addToActionGroup(self.editattributesaction)
        self.editingtoolbar.addToActionGroup(self.moveaction)

        self.actionGroup.addAction(self.editingmodeaction)

        self.homeAction.triggered.connect(self.zoomToDefaultView)
        
        self.openProjectAction.triggered.connect(self.showOpenProjectDialog)
        self.openProjectAction.triggered.connect(functools.partial(self.stack.setCurrentIndex, 1))
        
        self.toggleRasterAction.triggered.connect(self.toggleRasterLayers)

        self.navtoolbar.insertAction(self.iface.actionZoomIn(), self.iface.actionTouch())
        self.navtoolbar.insertAction(self.iface.actionTouch(), self.homeAction)
        self.navtoolbar.insertAction(self.iface.actionTouch(), self.iface.actionZoomFullExtent())
        self.navtoolbar.insertAction(self.homeAction, self.iface.actionZoomFullExtent())

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
        
        self.mapview = QAction(QIcon(":/icons/map"), "Map", self.menutoolbar)
        self.mapview.setCheckable(True)
        self.mapview.triggered.connect(functools.partial(self.stack.setCurrentIndex, 0))
        
        self.help = QAction(QIcon(":/icons/help"), "Help", self.menutoolbar)
        self.help.setCheckable(True)
        self.help.triggered.connect(functools.partial(self.stack.setCurrentIndex, 2))
        
        self.quit = QAction(QIcon(":/icons/quit"), "Quit", self.menutoolbar)
        self.quit.triggered.connect(self.iface.actionExit().trigger)

        self.menuGroup.addAction(self.mapview)
        self.menuGroup.addAction(self.openProjectAction)
        self.menuGroup.addAction(self.help)
        
        self.menutoolbar.addAction(self.mapview)
        self.menutoolbar.addAction(self.openProjectAction)
        self.menutoolbar.addAction(self.help)
        self.menutoolbar.addAction(self.quit)
        
        quitspacewidget = createSpacer()
        quitspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.menutoolbar.insertWidget(self.quit, quitspacewidget)       

        self.setupIcons()
        self.stack.currentChanged.connect(self.updateUIState)
        
    def updateUIState(self, page):
        """
        Update the UI state to reflect the currently selected
        page in the stacked widget
        """
        def setToolbarsActive(enabled):
            toolbars = self.mainwindow.findChildren(QToolBar)
            for toolbar in toolbars:
                if toolbar == self.menutoolbar:
                    continue
                toolbar.setEnabled(enabled)
        
        def setPanelsVisible(visible):
            for panel in self.panels:
                panel.setVisible(visible)
                
        ismapview = page == 0
        setToolbarsActive(ismapview)
        setPanelsVisible(ismapview)

    def addAtGPS(self):
        """
        Add a record at the current GPS location.
        """
        action = self.actionGroup.checkedAction()
        if not action:
            return
        layer = action.data()
        if not layer:
            return
        
        point = self.gpsAction.position
        self.addNewFeature(layer=layer, geometry=point)
        
    def zoomToDefaultView(self):
        """
        Zoom the mapview canvas to the extents the project was opened at i.e. the
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
        for layer in self._mapLayers.values():
            if layer.type() == QgsMapLayer.RasterLayer:
                isvisible = legend.isLayerVisible(layer)
                legend.setLayerVisible(layer, not isvisible)
        self.iface.mapCanvas().freeze(False)
        self.iface.mapCanvas().refresh()

    def setupIcons(self):
        """
        Update toolbars to have text and icons, change normal QGIS
        icons to new style
        """
        toolbars = self.mainwindow.findChildren(QToolBar)
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
        for panel in self.panels:
            self.mainwindow.removeDockWidget(panel)
            del panel

        projectpath = QgsProject.instance().fileName()
        project = QMapProject(os.path.dirname(projectpath), self.iface)
        self.createFormButtons(projectlayers = project.getConfiguredLayers())
        
        # Enable the raster layers button only if the project contains a raster layer.
        hasrasters = any(layer.type() for layer in self._mapLayers.values())
        self.toggleRasterAction.setEnabled(hasrasters)
        self.defaultextent = self.iface.mapCanvas().extent()
        self.connectSyncProviders(project)
        
        # Show panels
        self.panels = list(project.getPanels())
        for panel in self.panels:
            self.mainwindow.addDockWidget(Qt.BottomDockWidgetArea , panel)
        
    def createFormButtons(self, projectlayers):
        """
            Create buttons for each form that is definded
        """
        # Remove all the old buttons
        for action in self.actions:
            self.actionGroup.removeAction(action)
            self.toolbar.removeAction(action)
                
        self.edittool.layers = []
        self.movetool.layers = []
        for layer in projectlayers:
            try:
                qgslayer = QgsMapLayerRegistry.instance().mapLayersByName(layer.name)[0]
                if qgslayer.type() == QgsMapLayer.RasterLayer:
                    log("We can't support raster layers for data entry")
                    continue
                       
                layer.QGISLayer = qgslayer
            except KeyError:
                log("Layer not found in project")
                continue
            
            if 'capture' in layer.capabilities:
                text = layer.icontext
                try:
                    tool = layer.getMaptool(self.iface.mapCanvas())
                except NoMapToolConfigured:
                    log("No map tool configured")
                    continue
                except ErrorInMapTool as error:
                    self.messageBar.pushMessage("Error configuring map tool", error.message, level=QgsMessageBar.WARNING)
                    continue
                    
                # Hack until I fix it later
                if isinstance(tool, PointTool):
                    add = functools.partial(self.addNewFeature, qgslayer)
                    tool.geometryComplete.connect(add)
                else:
                    tool.finished.connect(self.openForm)
         
                action = QAction(QIcon(layer.icon), text, self.mainwindow)
                action.setData(layer)
                action.setCheckable(True)
                action.toggled.connect(functools.partial(self.setMapTool, tool))
                
                self.toolbar.insertAction(self.editingmodeaction, action)
                
                if not tool.isEditTool():
                    # Connect the GPS tools strip to the action pressed event.                
                    showgpstools = (functools.partial(self.extraaddtoolbar.showToolbar, 
                                                 action,
                                                 None))
                    
                    action.toggled.connect(showgpstools)
                    
                self.actionGroup.addAction(action)
                self.actions.append(action)
            
            if 'edit' in layer.capabilities:
                # TODO Use snapping options from project
                radius = (QgsTolerance.toleranceInMapUnits( 10, qgslayer,
                                                            self.iface.mapCanvas().mapRenderer(), 
                                                            QgsTolerance.Pixels))
                self.edittool.addLayer(qgslayer)
                self.edittool.searchRadius = radius
                
            if 'move' in layer.capabilities:
                self.movetool.addLayer(qgslayer)
            
    def openForm(self, layer, feature):
        if not layer.isEditable():
            layer.startEditing()
            
        self.dialogprovider.openDialog(feature=feature, layer=layer)
            
    def addNewFeature(self, layer, geometry):
        fields = layer.pendingFields()
        
        if not layer.isEditable():
            layer.startEditing()
    
        feature = QgsFeature()
        feature.setGeometry( geometry )
        feature.initAttributes(fields.count())
        feature.setFields(fields)
        
        for indx in xrange(fields.count()):
            feature[indx] = layer.dataProvider().defaultValue(indx)

        self.dialogprovider.openDialog(feature=feature, layer=layer)

    def showOpenProjectDialog(self):
        """
        Show the project selection dialog.
        """
        self.stack.setCurrentIndex(1)
        path = os.path.join(os.path.dirname(__file__), '..' , 'projects/')
        projects = getProjects(path, self.iface)
        self.projectwidget.loadProjectList(projects)
        
    def loadProject(self, project):
        """
        Load a project into QGIS.
        """
        utils.log(project)
        utils.log(project.name)
        utils.log(project.projectfile)
        utils.log(project.vaild)
        
        (passed, message) = project.onProjectLoad()
        
        if not passed:
            QMessageBox.warning(self.mainwindow, "Project Load Rejected", 
                                "Project couldn't be loaded because {}".format(message))
            return
        
        self.mapview.trigger()
        self.iface.newProject(False)        
        self.iface.mapCanvas().freeze()
        fileinfo = QFileInfo(project.projectfile)
        self.badLayerHandler = BadLayerHandler(callback=self.missingLayers)
        QgsProject.instance().setBadLayerHandler( self.badLayerHandler )
        
        QgsProject.instance().read(fileinfo)
        
        self.iface.mapCanvas().updateScale()
        self.iface.mapCanvas().freeze(False)
        self.iface.mapCanvas().refresh()
        self.mainwindow.setWindowTitle("QMap: QGIS Data Collection")
        self.iface.projectRead.emit()
        
    def unload(self):
        del self.toolbar
        
    def connectSyncProviders(self, project):
        self.syncactionstoolbar.clear()
        
        syncactions = list(project.getSyncProviders())
        
        # Don't show the sync button if there is no sync providers
        if not syncactions:
            self.syncAction.setVisible(False)
            return
        
        self.syncAction.setVisible(True)
        
        for provider in syncactions:
            action = QAction(QIcon(":/icons/sync"), "Sync {}".format(provider.name), self.mainwindow)
            action.triggered.connect(functools.partial(self.syncProvider, provider))
            self.syncactionstoolbar.addAction(action)
        
        try:
            self.syncAction.toggled.disconnect()
        except TypeError:
            pass
        try:
            self.syncAction.triggered.disconnect()
        except TypeError:
            pass
        
        if len(syncactions) == 1:
            # If one provider is set then we just connect the main button.    
            self.syncAction.setCheckable(False)
            self.syncAction.setText("Sync")
            self.syncAction.triggered.connect(functools.partial(self.syncProvider, syncactions[0]))
        else:
            # the sync button because a sync menu
            self.syncAction.setCheckable(True)
            self.syncAction.setText("Sync Menu")
            showsyncoptions = (functools.partial(self.syncactionstoolbar.showToolbar, 
                                                 self.syncAction, None))
            self.syncAction.toggled.connect(showsyncoptions)

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
        self.syncAction.toggle()
        provider.syncStarted.connect(functools.partial(self.syncAction.setEnabled, False))
        provider.syncStarted.connect(self.syncstarted)
        
        provider.syncComplete.connect(self.synccomplete)
        provider.syncComplete.connect(functools.partial(self.syncAction.setEnabled, True))
        provider.syncComplete.connect(functools.partial(self.report.updateHTML))
        
        provider.syncMessage.connect(self.report.updateHTML)
        
        provider.syncError.connect(self.report.updateHTML)
        provider.syncError.connect(self.syncerror)
        provider.syncComplete.connect(functools.partial(self.syncAction.setEnabled, True))
        
        provider.startSync()
        
class PopDownReport(QDialog):
    def __init__(self, parent=None):
        super(PopDownReport, self).__init__(parent)
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
        
