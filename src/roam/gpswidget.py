from roam.ui.uifiles import gps_widget, gps_base


class GPSWidget(gps_widget, gps_base):
    def __init__(self, gps, parent=None):
        super(GPSWidget, self).__init__(parent)
        self.gps = gps
        self.setupUi(self)
        self.gps.gpspostion.connect(self.updatepostionlabels)
        self.gps.gpsdisconnected.connect(self.disconnected)

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

