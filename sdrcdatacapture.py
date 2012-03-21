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
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from sdrcdatacapturedialog import SDRCDataCaptureDialog

class SDRCDataCapture:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/sdrcdatacapture/icon.png"), \
            "Data Collection", self.iface.mainWindow())
        # connect the action to the run method
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)

        #Create the toolbar icons.
        self.createFormButtons()
        
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Data Collection", self.action)

    def createFormButtons(self):
        # TODO Create toolbar buttons based on forms in form folder.
        import forms
        userForms = forms.getForms()
        for form in userForms:
            form = forms.loadForm(form)
            action = QAction( form.name(), self.iface.mainWindow() )
            self.iface.addToolBarIcon(action)
            
    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&Data Collection",self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def run(self):

        # create and show the dialog
        dlg = SDRCDataCaptureDialog()
        # show the dialog
        dlg.show()
        result = dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code
            pass
