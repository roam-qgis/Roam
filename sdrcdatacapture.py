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
import PointTool
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from sdrcdatacapturedialog import SDRCDataCaptureDialog

class SDRCDataCapture:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

    def initGui(self):
        self.createFormButtons()

    def createFormButtons(self):
        # TODO Create toolbar buttons based on forms in form folder.
        toolbar = QToolbar("SDRC Data Capture")

        import forms
        userForms = forms.getForms()
        for form in userForms:
            form = forms.loadForm(form)
            action = QAction( form.name(), self.iface.mainWindow() )
            toolbar.addAction(action)

        self.iface.addToolBar(toolbar)
            
    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&Data Collection",self.action)
        self.iface.removeToolBarIcon(self.action)
