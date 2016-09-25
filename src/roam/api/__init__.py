__author__ = 'Nathan.Woodrow'


import roam.config
import os

portname = roam.config.settings.get('gpsport', '')

import gps
if portname.startswith("file://"):
    print "Setting fake GPS"
    portname = portname.strip("file://")
    GPS = gps.FileGPSService(portname)
else:
    GPS = gps.GPSService()

from roam.api.events import RoamEvents
from roam.api.featureform import FeatureForm
from roam.api.interface import RoamInterface

from roam.api.featureforms import inspectionform
