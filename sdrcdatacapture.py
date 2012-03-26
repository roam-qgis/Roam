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
from PointTool import PointAction
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import forms
from PointTool import PointAction
import resources
from sdrcdatacapturedialog import SDRCDataCaptureDialog

class SDRCDataCapture:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        QgsMessageLog.logMessage("initGUI","SDRC")
        self.createFormButtons()

    def createFormButtons(self):
        self.toolbar = self.iface.addToolBar("SDRC Data Capture")
        userForms = forms.getForms()
        
        for form in userForms:
            form = forms.loadForm(form)
            action = PointAction( form.__formName__, self.iface, form )
            self.toolbar.addAction(action)

    def unload(self):
        del self.toolbar

