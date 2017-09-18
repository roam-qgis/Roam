__author__ = 'Nathan.Woodrow'


import roam.config
import os
# portname = roam.config.settings.get('gpsport', '')
# if os.path.exists(portname):
#     print "Setting fake GPS"
#     GPS = gps.FileGPSService(portname)

from roam.api.gps import GPS
from roam.api.events import RoamEvents
from roam.api.featureform import FeatureForm
from roam.api.interface import RoamInterface
from roam.api.featureforms import inspectionform
