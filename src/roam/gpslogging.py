import getpass

from PyQt4.QtCore import Qt, pyqtSignal, QObject, QDateTime
from qgis.core import QgsFeature, QgsGeometry

class GPSLogging(QObject):
    trackingchanged = pyqtSignal(bool)

    def __init__(self, gps):
        super(GPSLogging, self).__init__()
        self.gps = gps
        self.logging = False
        self.featurecache = []

    def enable_logging_on(self, layer):
        self.layer = layer
        self.layerprovider = self.layer.dataProvider()
        self.fields = self.layerprovider.fields()
        self.logging = True

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
        self._tracking = value
        if value:
            self.gps.gpsposition.connect(self.postionupdated)
        else:
            try:
                self.gps.gpsposition.disconnect(self.postionupdated)
            except TypeError:
                pass
        self.trackingchanged.emit(value)

    def postionupdated(self, position, info):
        if not self.logging:
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
