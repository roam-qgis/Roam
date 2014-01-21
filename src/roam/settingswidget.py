import os
from PyQt4.QtCore import pyqtSignal
from qgis.core import QgsGPSDetector, QGis

import roam
import roam.utils as utils
from roam.uifiles import settings_widget, settings_base


class SettingsWidget(settings_widget, settings_base):
    settingsupdated = pyqtSignal(object)

    def __init__(self, settings, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self._settings = settings
        self.populated = False
        self.fullScreenCheck.toggled.connect(self.fullScreenCheck_stateChanged)
        self.gpsPortCombo.currentIndexChanged.connect(self.gpsPortCombo_currentIndexChanged)
        self.refreshPortsButton.pressed.connect(self.refreshPortsButton_pressed)
        self.gpslocationCheck.toggled.connect(self.gpslocationCheck_toggled)

    @property
    def settings(self):
        return self._settings.settings

    def notifysettingsupdate(self):
        self.settingsupdated.emit(self._settings)

    def gpslocationCheck_toggled(self, checked):
        self.settings['gpszoomonfix'] = checked
        self.notifysettingsupdate()

    def fullScreenCheck_stateChanged(self, checked):
        utils.log("fullscreen changed")
        self.settings["fullscreen"] = checked
        self.notifysettingsupdate()

    def gpsPortCombo_currentIndexChanged(self, index):
        port = self.gpsPortCombo.itemData(index)
        self.settings["gpsport"] = port
        self.notifysettingsupdate()

    def refreshPortsButton_pressed(self):
        self.updateCOMPorts()
        
    def updateCOMPorts(self):
        # First item is the local gpsd so skip that. 
        ports = QgsGPSDetector.availablePorts()[1:]
        self.blockSignals(True)
        self.gpsPortCombo.clear()
        self.gpsPortCombo.addItem('scan', 'scan')
        for port, name in ports:
            self.gpsPortCombo.addItem(name, port)
        self.blockSignals(False)
        
    def readSettings(self):
        fullscreen = self.settings.get("fullscreen", False)
        gpsport = self.settings.get("gpsport", 'scan')
        gpszoom = self.settings.get('gpszoomonfix', True)

        self.fullScreenCheck.setChecked(fullscreen)
        self.gpslocationCheck.setChecked(gpszoom)
        gpsindex = self.gpsPortCombo.findData(gpsport)
        
        self.blockSignals(True)
        if gpsindex == -1:
            self.gpsPortCombo.addItem(gpsport)
        else:
            self.gpsPortCombo.setCurrentIndex(gpsindex)
        self.blockSignals(False)
        
    def populateControls(self):
        if self.populated:
            return
        
        self.updateCOMPorts()
        # Read version

        self.versionLabel.setText(roam.__version__)
        self.qgisapiLabel.setText(str(QGis.QGIS_VERSION))
        self.populated = True