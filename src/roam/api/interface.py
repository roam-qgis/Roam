from qgis.PyQt.QtCore import QObject


class RoamInterface(QObject):
    def __init__(self, events, gps, mainwindow, mapwindow, parent):
        super(RoamInterface, self).__init__(parent)
        self.events = events
        self.gps = gps
        self.mapwindow = mapwindow
        self.mainwindow = mainwindow
