from PyQt4.QtGui import QWidget
from ui.ui_gps import Ui_gpsWidget

import roam.config


class GPSWidget(Ui_gpsWidget, QWidget):
    def __init__(self, parent=None):
        super(GPSWidget, self).__init__(parent)
        self.setupUi(self)
        self.gps = None
        self.logginginfolabel.setVisible(False)
        self.gpstiming_edit.valueChanged.connect(self.update_tracking)
        self.gpsdistance_edit.valueChanged.connect(self.update_tracking)
        self.gpstiming_edit.setSuffix(" seconds")
        self.gpsdistance_edit.setSuffix(" map units")
        self.gpstiming_edit.setEnabled(False)
        self.gpsdistance_edit.setEnabled(False)
        self.set_gps_settings()

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

    def update_tracking(self, value):
        gpssettings = {}
        if self.gpstracking_timing_radio.isChecked():
            gpssettings['tracking'] = {"time": value}
            roam.config.settings['gps'] = gpssettings
        elif self.gpstracking_distance_radio.isChecked():
            gpssettings['tracking'] = {"distance": value}

        roam.config.settings['gps'] = gpssettings
        roam.config.save()

    def setgps(self, gps):
        self.gps = gps
        self.gps.gpsposition.connect(self.updatepostionlabels)
        self.gps.gpsdisconnected.connect(self.disconnected)

    def settracking(self, trackingobject):
        self.tracking = trackingobject
        self.tracking.trackingchanged.connect(self.updatetrackingstate)

    def updatetrackingstate(self, istracking):
        if istracking:
            self.trackinglabel.setText("GPS Logging Active")
        else:
            self.trackinglabel.setText("GPS Logging Disabled")

        self.trackinglabel.setProperty("active", istracking)
        self.trackinglabel.style().polish(self.trackinglabel)
        self.logginginfolabel.setVisible(istracking)

    def updatepostionlabels(self, postion, info):
        self.activeLabel.setText("GPS Active")
        self.activeLabel.setProperty("active", True)
        self.activeLabel.style().polish(self.activeLabel)

        self.xLabel.setText(str(postion.x()))
        self.yLabel.setText(str(postion.y()))
        self.latLabel.setText(str(info.latitude))
        self.longLabel.setText(str(info.longitude))
        self.hdopLabel.setText(str(info.hdop))
        self.vdopLabel.setText(str(info.vdop))
        self.pdopLabel.setText(str(info.pdop))

    def disconnected(self):
        self.activeLabel.setText("GPS Not Active")
        self.activeLabel.setProperty("active", False)
        self.activeLabel.style().polish(self.activeLabel)

