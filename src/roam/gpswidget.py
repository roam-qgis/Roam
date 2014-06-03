from PyQt4.QtGui import QWidget
from ui.ui_gps import Ui_gpsWidget

class GPSWidget(Ui_gpsWidget, QWidget):
    def __init__(self, parent=None):
        super(GPSWidget, self).__init__(parent)
        self.setupUi(self)
        self.gps = None
        self.logginginfolabel.setVisible(False)

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

