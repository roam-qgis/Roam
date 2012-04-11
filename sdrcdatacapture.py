"""
/***************************************************************************
 SDRCDataCapture
                                 A QGIS plugin
 Prototype Data collection software for SDRC
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

from AddAction import AddAction
from EditAction import EditAction
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import forms
from listmodulesdialog import ListProjectsDialog
from qgis.core import *
import resources
from sdrcdatacapturedialog import SDRCDataCaptureDialog
from syncing.Syncer import SyncDialog
from syncing.Syncer import Syncer
import syncing.ui_sync

log = lambda msg: QgsMessageLog.logMessage(msg ,"SDRC")

class SDRCDataCapture:
    def __init__(self, iface):
        self.iface = iface
        self.layerstoForms = {}
        self.actions = []
        self.iface.projectRead.connect(self.projectOpened)
        self.settings = QSettings( "settings.ini", QSettings.IniFormat )
        
    def initGui(self):
        self.toolbar = self.iface.addToolBar("SDRC Data Capture")
        self.setupIcons()

#        self.openProjectAction = QAction(QIcon(":/syncing/syncing/sync.png"), \
#                                    "Open Project", self.iface.mainWindow() )
#
#        self.openProjectAction.triggered.connect(self.openProject)
#        self.toolbar.addAction(self.openProjectAction)

        self.editAction = EditAction("Edit", self.iface, self.layerstoForms )
        self.syncAction = QAction(QIcon(":/syncing/syncing/sync.png"), \
                                    "Sync", self.iface.mainWindow() )
        self.syncAction.triggered.connect(self.sync)

        self.toolbar.addAction(self.editAction)                        
        self.toolbar.addAction(self.syncAction)
        self.toolbar.insertSeparator(self.syncAction)

        self.iface.actionToggleFullScreen().trigger()

    def setupIcons(self):
        """
            Update toolbars to have text and icons, change icons to new style
        """
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            #toolbar.setIconSize(QSize(32,32))
            
        self.iface.actionZoomIn().setIcon(QIcon(":/icons/in"))
        self.iface.actionZoomOut().setIcon(QIcon(":/icons/out"))
        self.iface.actionPan().setIcon(QIcon(":/icons/pan"))

    def projectOpened(self):
        """
            Create user buttons on project load
        """
        layers = dict((str(x.name()), x) for x in QgsMapLayerRegistry.instance().mapLayers().values())
        self.createFormButtons(layers)
        
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
                self.actions.append(action)
                self.layerstoForms[form.__layerName__] = form
            except KeyError:
                log("Couldn't find layer for form %s" % form.__layerName__)

        self.toolbar.insertSeparator(self.editAction)

    def openProject(self):
        self.dialog = ListProjectsDialog()
        self.dialog.setModal(True)
        self.dialog.show()
        #QCoreApplication.processEvents()
        curdir= os.path.dirname(__file__)
        path =os.path.join(curdir,'projects/')
        paths = self.settings.value("/projects/projectLocations", [path]).toList()
        self.dialog.loadProjectList(paths)
    
    def unload(self):
        del self.toolbar

    def sync(self):
        self.syndlg = SyncDialog()
        self.syndlg.setModal(True)
        self.syndlg.show()
        # HACK 
        QCoreApplication.processEvents()
        self.syndlg.runSync()