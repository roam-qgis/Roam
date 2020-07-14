from qgis.PyQt.QtCore import pyqtSignal, QThread, Qt
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsGpsDetector, Qgis, QgsProviderRegistry

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
        ports = QgsGpsDetector.availablePorts()[1:]
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
        self.gpsFlowControl.currentIndexChanged.connect(self.gpsFlowControl_currentIndexChanged)
        self.refreshPortsButton.pressed.connect(self.refreshPortsButton_pressed)
        self.gpslocationCheck.toggled.connect(self.gpslocationCheck_toggled)
        self.gpsloggingCheck.toggled.connect(self.gpsloggingCheck_toggled)
        self.gpscentermapCheck.toggled.connect(self.gpscentermapCheck_toggled)
        self.keyboardCheck.toggled.connect(self.keyboardCheck_toggled)
        self.updateServerEdit.textChanged.connect(self.updateServerEdit_edited)
        self.distanceCheck.toggled.connect(self.distanceCheck_toggled)
        self.errorReportCheck.toggled.connect(self.errorReportCheck_toggled)
        self.smallModeCheck.toggled.connect(self.smallMode_toggled)
        self.portfinder = PortFinder()
        self.portfinder.portsfound.connect(self._addports)
        self.gpsAntennaHeight.valueChanged.connect(self.gpsAntennaHeight_edited)
        self.gpsAntennaHeight.setSuffix(" meters")
        self.gpstiming_edit.valueChanged.connect(self.update_tracking)
        self.gpsdistance_edit.valueChanged.connect(self.update_tracking)
        self.gpstiming_edit.setSuffix(" seconds")
        self.gpsdistance_edit.setSuffix(" map units")
        self.gpstiming_edit.setEnabled(False)
        self.gpsdistance_edit.setEnabled(False)

    # --- gps averaging -------------------------------------------------------
        self.gpsAveragingCheck.toggled.connect(self.gpsAveragingCheck_toggled)

    def gpsAveragingCheck_toggled(self, checked):
        self.settings['gps_averaging'] = checked
        if not checked:
            self.settings['gps_averaging_in_action'] = False
            self.settings['gps_averaging_start_time'] = '0:00:00'
            self.settings['gps_averaging_measurements'] = 0
        self.notifysettingsupdate()
    #--------------------------------------------------------------------------

    @property
    def settings(self):
        return roam.config.settings

    def notifysettingsupdate(self):
        roam.config.save()
        self.settingsupdated.emit(self.settings)

    def smallMode_toggled(self, checked):
        self.settings['smallmode'] = checked
        self.notifysettingsupdate()

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

    def gpsAntennaHeight_edited(self):
        antennaHeight = self.gpsAntennaHeight.value()
        self.settings["gps_antenna_height"] = antennaHeight
        self.notifysettingsupdate()

    def fullScreenCheck_stateChanged(self, checked):
        utils.log("fullscreen changed")
        self.settings["fullscreen"] = checked
        self.notifysettingsupdate()

    def keyboardCheck_toggled(self, checked):
        self.settings["keyboard"] = checked
        self.notifysettingsupdate()

    def gpsFlowControl_currentIndexChanged(self, index):
        control = self.gpsFlowControl.currentText()
        control = control.lower()
        gpssettings = roam.config.settings.get("gps", {})
        gpssettings['flow_control'] = control
        self.notifysettingsupdate()

        roam.config.settings['gps'] = gpssettings
    def gpsPortCombo_currentIndexChanged(self, index):
        #If os returns port name with colon and label, strip label (noted in Windows 7)
        port = self.gpsPortCombo.itemData(index, Qt.UserRole)
        print(port)
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
        gpsindex = self.gpsPortCombo.findData(gpsport, Qt.UserRole)

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
        gpsantennaheight = self.settings.get('gps_antenna_height', None)
        keyboard = self.settings.get('keyboard', True)
        updateserver = self.settings.get('updateserver', None)
        distance = self.settings.get('draw_distance', True)
        reporterror = self.settings.get('online_error_reporting', True)
        smallmode = self.settings.get('smallmode', False)
        # --- gps averaging ---------------------------------------------------
        gpsaveraging = self.settings.get('gps_averaging', False)
        
        self.gpsAveragingCheck.setChecked(gpsaveraging)
        # ---------------------------------------------------------------------
        self.fullScreenCheck.setChecked(fullscreen)
        self.gpslocationCheck.setChecked(gpszoom)
        self.gpscentermapCheck.setChecked(gpscenter)
        self.gpsAntennaHeight.setValue(gpsantennaheight)
        self.keyboardCheck.setChecked(keyboard)
        self.gpsloggingCheck.setChecked(gpslogging)
        self.updateServerEdit.setText(updateserver)
        self.distanceCheck.setChecked(distance)
        self.errorReportCheck.setChecked(reporterror)
        self.smallModeCheck.setChecked(smallmode)

        self._setgpsport()
        self.set_gps_settings()
        self.set_gps_flow_control()

    def set_gps_flow_control(self):
        flowControl = self.settings.get('gps', {}).get("flow_control", "auto")
        if flowControl == "hardware":
            self.gpsFlowControl.setCurrentText("Hardware")
        elif flowControl == "software":
            self.gpsFlowControl.setCurrentText("Software")
        else:
            self.gpsFlowControl.setCurrentText("Auto")

    def update_tracking(self, value):
        gpssettings = roam.config.settings.get("gps", {})
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

        self.versionLabel.setText(roam.__version__)
        self.qgisapiLabel.setText(Qgis.QGIS_VERSION)
        ecwsupport = 'ecw' in QgsProviderRegistry.instance().fileRasterFilters()
        self.ecwlabel.setText("Yes" if ecwsupport else "No")
