from PyQt4.QtCore import pyqtSignal, QThread, QObject
from PyQt4.QtGui import QWidget
from qgis.core import QgsGPSDetector, QGis, QgsProviderRegistry

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
        self.fullScreenCheck.toggled.connect(self.fullScreenCheck_stateChanged)
        self.gpsPortCombo.currentIndexChanged.connect(self.gpsPortCombo_currentIndexChanged)
        self.refreshPortsButton.pressed.connect(self.refreshPortsButton_pressed)
        self.gpslocationCheck.toggled.connect(self.gpslocationCheck_toggled)
        self.gpsloggingCheck.toggled.connect(self.gpsloggingCheck_toggled)
        self.gpscentermapCheck.toggled.connect(self.gpscentermapCheck_toggled)
        self.keyboardCheck.toggled.connect(self.keyboardCheck_toggled)
        self.updateServerEdit.textChanged.connect(self.updateServerEdit_edited)
        self.distanceCheck.toggled.connect(self.distanceCheck_toggled)
        self.errorReportCheck.toggled.connect(self.errorReportCheck_toggled)
        self.portfinder = PortFinder()
        self.portfinder.portsfound.connect(self._addports)
        self.gpstiming_edit.valueChanged.connect(self.update_tracking)
        self.gpsdistance_edit.valueChanged.connect(self.update_tracking)
        self.gpstiming_edit.setSuffix(" seconds")
        self.gpsdistance_edit.setSuffix(" map units")
        self.gpstiming_edit.setEnabled(False)
        self.gpsdistance_edit.setEnabled(False)

    @property
    def settings(self):
        return roam.config.settings

    def notifysettingsupdate(self):
        roam.config.save()
        self.settingsupdated.emit(self.settings)

    def errorReportCheck_toggled(self, checked):
        self.settings['online_error_reporting'] = checked
        self.notifysettingsupdate()

    def distanceCheck_toggled(self, checked):
        self.settings['draw_distance'] = checked
        self.notifysettingsupdate()

    def gpslocationCheck_toggled(self, checked):
        self.settings['gpszoomonfix'] = checked
        self.notifysettingsupdate()

    def gpsloggingCheck_toggled(self, checked):
        self.settings['gpslogging'] = checked
        self.notifysettingsupdate()

    def gpscentermapCheck_toggled(self, checked):
        self.settings["gpscenter"] = checked
        self.notifysettingsupdate()

    def fullScreenCheck_stateChanged(self, checked):
        utils.log("fullscreen changed")
        self.settings["fullscreen"] = checked
        self.notifysettingsupdate()

    def keyboardCheck_toggled(self, checked):
        self.settings["keyboard"] = checked
        self.notifysettingsupdate()

    def gpsPortCombo_currentIndexChanged(self, index):
        port = self.gpsPortCombo.itemText(index)
        self.settings["gpsport"] = port
        self.notifysettingsupdate()

    def updateServerEdit_edited(self):
        server = self.updateServerEdit.text()
        self.settings["updateserver"] = server
        roam.config.save()

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

    def set_gps_settings(self):
        gpsettings = roam.config.settings.get("gps", {})
        config = gpsettings.get('tracking', {})
        if "time" in config:
            value = config['time']
            self.gpstracking_timing_radio.setChecked(True)
            self.gpstiming_edit.setValue(value)
        elif "distance" in config:
            value = config['distance']
            self.gpstracking_distance_radio.setChecked(True)
            self.gpsdistance_edit.setValue(value)
        else:
            self.gpstracking_timing_radio.setChecked(True)
            self.gpstiming_edit.setValue(1)

    def readSettings(self):
        fullscreen = self.settings.get("fullscreen", False)
        gpszoom = self.settings.get('gpszoomonfix', True)
        gpscenter = self.settings.get('gpscenter', True)
        gpslogging = self.settings.get('gpslogging', False)
        keyboard = self.settings.get('keyboard', True)
        updateserver = self.settings.get('updateserver', None)
        distance = self.settings.get('draw_distance', True)
        reporterror = self.settings.get('online_error_reporting', False)

        self.fullScreenCheck.setChecked(fullscreen)
        self.gpslocationCheck.setChecked(gpszoom)
        self.gpscentermapCheck.setChecked(gpscenter)
        self.keyboardCheck.setChecked(keyboard)
        self.gpsloggingCheck.setChecked(gpslogging)
        self.updateServerEdit.setText(updateserver)
        self.distanceCheck.setChecked(distance)
        self.errorReportCheck.setChecked(reporterror)

        self._setgpsport()
        self.set_gps_settings()

    def update_tracking(self, value):
        gpssettings = {}
        if self.gpstracking_timing_radio.isChecked():
            gpssettings['tracking'] = {"time": value}
            roam.config.settings['gps'] = gpssettings
        elif self.gpstracking_distance_radio.isChecked():
            gpssettings['tracking'] = {"distance": value}

        roam.config.settings['gps'] = gpssettings
        self.notifysettingsupdate()

    def populateControls(self):
        if self.populated:
            return

        self.updateCOMPorts()
        # Read version

        self.versionLabel.setText(unicode(roam.__version__))
        self.qgisapiLabel.setText(unicode(QGis.QGIS_VERSION))
        ecwsupport = 'ecw' in QgsProviderRegistry.instance().fileRasterFilters()
        self.ecwlabel.setText("Yes" if ecwsupport else "No")
