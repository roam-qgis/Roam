import getpass
import uuid
from datetime import datetime

import roam.config
from qgis.PyQt.QtCore import Qt, pyqtSignal, QObject, QDateTime
from qgis.core import QgsFeature, QgsGeometry, QgsPointXY


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
        #Get tracklog interval settings
        self.tracking_settings = roam.config.settings['gps']['tracking']
        #Add unique track id
        self.tracking_settings['trackid'] = str(uuid.uuid4())
        #Setup initial tracking value
        if hasattr(self.tracking_settings, 'distance'):
            #Default to 0,0 for distance based tracking
            self.tracking_settings['last'] = QgsPointXY(0,0)
        else:
            #Default to epoch for time based tracking
            self.tracking_settings['last'] = 0

    def enable_logging_on(self, layer):
        #Enable logging
        self.logging = True
        #Setup layer and provider
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

    def postionupdated(self, position: QgsPointXY, info):
        #Check layer for logging capability and if in logging mode
        if not self.logging or not self.layer or not self.layerprovider or not self.tracking_settings:  
            return
        #Check tracking setting type
        if hasattr(self.tracking_settings, 'distance'):
            #Get tracking interval
            tracking_interval = getattr(self.tracking_settings, 'distance')
            #Compare distance
            if position.distance(self.tracking_settings['last']) >= tracking_interval:
                #Log track element
                self.log_track(position, info)
                #Update last position
                self.tracking_last = position
        else:      
            #Get tracking interval (default to time 1 sec)
            tracking_interval = getattr(self.tracking_settings, 'time', 1)
            #Get current timestamp
            now = datetime.timestamp(datetime.now())
            #Compare timestamp
            if (now - self.tracking_settings['last']) > tracking_interval:
                #Log track element
                self.log_track(position, info)
                #Update last position
                self.tracking_last = now

    #Seprate log_track function to allow for multiple types of log intervals
    def log_track(self, position: QgsPointXY, info):

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
            elif name == 'trackid':
                value = self.tracking_settings['trackid']
            else:
                try:
                    value = self.gps.gpsinfo(name)
                except AttributeError:
                    continue

            feature[name] = value

        geom = QgsGeometry.fromPointXY(position)
        feature.setGeometry(geom)
        self.featurecache.append(feature)
        if len(self.featurecache) > 5:
            self.layerprovider.addFeatures(self.featurecache)
            self.featurecache = []
