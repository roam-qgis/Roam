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
import syncing.ui_sync
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import forms
from EditAction import EditAction
from AddAction import AddAction
from syncing.Syncer import SyncDialog, Syncer
import resources
from sdrcdatacapturedialog import SDRCDataCaptureDialog

log = lambda msg: QgsMessageLog.logMessage(msg ,"SDRC")

class SDRCDataCapture:
    def __init__(self, iface):
        self.iface = iface
        self.layerstoForms = {}

    def initGui(self):
        # TODO Set the icon size bigger
        self.createFormButtons()
        
    def createFormButtons(self):
        self.toolbar = self.iface.addToolBar("SDRC Data Capture")
        userForms = forms.getForms()
        
        for form in userForms:
            form = forms.loadForm(form)
            action = AddAction( form.__formName__, self.iface, form )
            self.toolbar.addAction(action)
            self.layerstoForms[form.__layerName__] = form

        editAction = EditAction("Edit", self.iface, self.layerstoForms )
        self.toolbar.addAction(editAction)

        syncAction = QAction("Sync", self.iface.mainWindow() )
        syncAction.triggered.connect(self.sync)
        self.toolbar.addAction(syncAction)
        
    def unload(self):
        del self.toolbar

    def sync(self):
        self.syndlg = SyncDialog()
        self.syndlg.setModal(True)
        self.syndlg.show()
        QCoreApplication.processEvents()
        self.syndlg.runSync()