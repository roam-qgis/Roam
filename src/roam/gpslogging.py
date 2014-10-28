import getpass

from PyQt4.QtCore import Qt, pyqtSignal, QObject, QDateTime
from qgis.core import QgsFeature, QgsGeometry

class GPSLogging(QObject):
    trackingchanged = pyqtSignal(bool)

    def __init__(self, gps):
        super(GPSLogging, self).__init__()
        self.layer = None
        self.layerprovider = None
        self.fields = None
        self.gps = gps
        self.logging = False
        self.featurecache = []
        self._tracking = False
        self.gps.gpsposition.connect(self.postionupdated)

    def enable_logging_on(self, layer):
        self.layer = layer
        self.layerprovider = self.layer.dataProvider()
        self.fields = self.layerprovider.fields()

    def clear_logging(self):
        self.logging = False
        self.layer = None
        self.layerprovider = None
        self.fields = None

    @property
    def logging(self):
        return self._tracking

    @logging.setter
    def logging(self, value):

        # If no layer for logging is set then we can't track.
        if not self.layer and self.layerprovider:
            value = False

        self._tracking = value
        self.trackingchanged.emit(value)

    def postionupdated(self, position, info):
        if not self.logging or not self.layer or not self.layerprovider:
            return

        feature = QgsFeature()
        feature.setFields(self.fields)

        for field in self.fields:
            name = field.name()
            if name == 'time':
                value = self.gps.gpsinfo('utcDateTime').toString(Qt.ISODate)
            elif name == 'localtime':
                value = QDateTime.currentDateTime().toString(Qt.ISODate)
            elif name == 'user':
                value = getpass.getuser()
            else:
                try:
                    value = self.gps.gpsinfo(name)
                except AttributeError:
                    continue

            feature[name] = value

        geom = QgsGeometry.fromPoint(position)
        feature.setGeometry(geom)
        self.featurecache.append(feature)
        if len(self.featurecache) > 5:
            self.layerprovider.addFeatures(self.featurecache)
            self.featurecache = []
