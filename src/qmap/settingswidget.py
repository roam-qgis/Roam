import os
from qgis.core import QgsGPSDetector

from uifiles import settings_widget, settings_base
from utils import settings, curdir

class SettingsWidget(settings_widget, settings_base):            
    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        
    def gpsPortCombo_currentIndexChanged(self, index):
        port = self.gpsPortCombo.itemData(index)
        settings["gpsport"] = port
        settings.saveSettings()
         
    def readSettings(self):
        fullscreen = settings.get("fullscreen", False)
        gpsport = settings.get("gpsport", 'scan')
        self.fullScreenCheck.setChecked(fullscreen)
        gpsindex = self.gpsPortCombo.findData(gpsport)
        
        self.blockSignals(True)
        if gpsindex == -1:
            self.gpsPortCombo.addItem(gpsport)
        else:
            self.gpsPortCombo.setCurrentIndex(gpsindex)
        self.blockSignals(False)
        
    def populateControls(self):
        # First item is the local gpsd so skip that. 
        ports = QgsGPSDetector.availablePorts()[1:]
        self.gpsPortCombo.addItem('scan', 'scan')
        for port, name in ports:
            self.gpsPortCombo.addItem(name, port)
            
        # Read version
        try:
            with open(os.path.join(curdir, 'version.txt')) as f:
                version = f.read().strip()
        except IOError:
            version = 'unknown'
            
        self.versionLabel.setText(version)