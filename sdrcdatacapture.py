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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import forms
from PointTool import PointTool
import resources
from sdrcdatacapturedialog import SDRCDataCaptureDialog

class SDRCDataCapture:
    
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.formToAction = {}

    def initGui(self):
        QgsMessageLog.logMessage("initGUI","SDRC")
        self.createFormButtons()

    def createFormButtons(self):
        # TODO Create toolbar buttons based on forms in form folder.
        self.toolbar = self.iface.addToolBar("SDRC Data Capture")
        self.toolbar.actionTriggered.connect( self.runAction )
        userForms = forms.getForms()
        
        for form in userForms:
            form = forms.loadForm(form)
            action = QAction( form.__formName__, self.iface.mainWindow() )
            self.formToAction[ form.__formName__,] = PointTool( self.iface.mapCanvas(), form )
            self.toolbar.addAction(action)

    def runTool(self):
        pass

    def runAction(self, action):
        name = action.text()
        maptool = self.formToAction[name]
        self.iface.mapCanvas().setMapTool(maptool)
        QgsMessageLog.logMessage("Run Action says %s" % name, "SDRC")

    def unload(self):
        pass
