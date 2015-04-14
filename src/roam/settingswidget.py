from PyQt4.QtCore import pyqtSignal, QThread, QObject
from PyQt4.QtGui import QWidget
from qgis.core import QgsGPSDetector, QGis

import roam
import roam.utils as utils
import roam.config
from roam.ui.ui_settings import Ui_settingsWidget


class PortFinder(QThread):
    portsfound = pyqtSignal(list)
    finished = pyqtSignal()

    def run(self):
        # NOTE: This is not the correct way, however it works and the
        # correct way still blocked the UI :S
        ports = QgsGPSDetector.availablePorts()[1:]
        self.portsfound.emit(ports)
        self.finished.emit()


class SettingsWidget(Ui_settingsWidget, QWidget):
    settingsupdated = pyqtSignal(object)

    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self._settings = None
        self.populated = False
        self.fullScreenCheck.toggled.connect(self.save)
        self.gpsPortCombo.currentIndexChanged.connect(self.save)
        self.refreshPortsButton.pressed.connect(self.save)
        self.gpslocationCheck.toggled.connect(self.save)
        self.gpsloggingCheck.toggled.connect(self.save)
        self.gpscentermapCheck.toggled.connect(self.save)
        self.keyboardCheck.toggled.connect(self.save)
        self.updateServerEdit.editingFinished.connect(self.save)
        self.distanceCheck.toggled.connect(self.save)
        self.portfinder = PortFinder()
        self.portfinder.portsfound.connect(self._addports)

    def save(self, *args):
        self.settings['draw_distance'] = self.distanceCheck.isChecked()
        self.settings['gpszoomonfix'] = self.gpslocationCheck.isChecked()
        self.settings['gpslogging'] = self.gpsloggingCheck.isChecked()
        self.settings["gpscenter"] = self.gpscentermapCheck.isChecked()
        self.settings["fullscreen"] = self.fullScreenCheck.isChecked()
        self.settings["keyboard"] = self.keyboardCheck.isChecked()
        self.settings["gpsport"] = self.gpsPortCombo.currentText()
        self.settings["updateserver"] = self.updateServerEdit.text()
        self.notifysettingsupdate()

    @property
    def settings(self):
        return roam.config.settings

    def notifysettingsupdate(self):
        roam.config.save()
        self.settingsupdated.emit(self.settings)

    def refreshPortsButton_pressed(self):
        self.updateCOMPorts()
        
    def updateCOMPorts(self):
        # First item is the local gpsd so skip that.
        self.portfinder.start()

        self.gpsPortCombo.blockSignals(True)
        self.gpsPortCombo.clear()
        self.gpsPortCombo.addItem('scan', 'scan')
        self.gpsPortCombo.blockSignals(False)

    def _addports(self, ports):
        self.gpsPortCombo.blockSignals(True)
        for port, name in ports:
            self.gpsPortCombo.addItem(name[:-1], port)
        self.gpsPortCombo.blockSignals(False)
        self.populated = True
        self._setgpsport()

    def _setgpsport(self):
        if not self.populated:
            return

        gpsport = self.settings.get("gpsport", 'scan')
        gpsport.replace(r"\\\.\\", "")
        gpsindex = self.gpsPortCombo.findText(gpsport)

        self.gpsPortCombo.blockSignals(True)
        if gpsindex == -1:
            self.gpsPortCombo.addItem(gpsport)
            self.gpsPortCombo.setCurrentIndex(self.gpsPortCombo.count() - 1)
        else:
            self.gpsPortCombo.setCurrentIndex(gpsindex)
        self.gpsPortCombo.blockSignals(False)

    def readSettings(self):
        fullscreen = self.settings.get("fullscreen", False)
        gpszoom = self.settings.get('gpszoomonfix', True)
        gpscenter = self.settings.get('gpscenter', True)
        gpslogging = self.settings.get('gpslogging', True)
        keyboard = self.settings.get('keyboard', True)
        updateserver = self.settings.get('updateserver', None)
        distance = self.settings.get('draw_distance', True)

        self.fullScreenCheck.setChecked(fullscreen)
        self.gpslocationCheck.setChecked(gpszoom)
        self.gpscentermapCheck.setChecked(gpscenter)
        self.keyboardCheck.setChecked(keyboard)
        self.gpsloggingCheck.setChecked(gpslogging)
        self.updateServerEdit.setText(updateserver)
        self.distanceCheck.setChecked(distance)

        self._setgpsport()

    def populateControls(self):
        if self.populated:
            return
        
        self.updateCOMPorts()
        # Read version

        self.versionLabel.setText(roam.__version__)
        self.qgisapiLabel.setText(str(QGis.QGIS_VERSION))
