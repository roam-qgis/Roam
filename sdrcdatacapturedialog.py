"""
/***************************************************************************
 SDRCDataCaptureDialog
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

from PyQt4 import QtCore, QtGui
from ui_sdrcdatacapture import Ui_SDRCDataCapture
# create the dialog for zoom to point
class SDRCDataCaptureDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_SDRCDataCapture()
        self.ui.setupUi(self)
