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
 This script initializes the plugin, making it known to QGIS.
"""
def name():
    return "Prototype Data collection software for SDRC"
def description():
    return "Prototype Data collection software for SDRC"
def version():
    return "Version 0.1"
def icon():
    return "icon.png"
def qgisMinimumVersion():
    return "1.8"
def classFactory(iface):
    from sdrcdatacapture import SDRCDataCapture
    return SDRCDataCapture(iface)

if __name__ == "__main__":
    import forms
    import sys
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    list = forms.getForms()
    form = forms.loadFormModule(list[0])
    form.init(None)
    sys.exit(app.exec_())