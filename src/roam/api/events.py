"""
RoamEvents is an event sink for common signals used though out Roam.

These can be raised and handled anywhere in the application.
"""
from PyQt4.QtCore import pyqtSignal, QObject, QUrl

from qgis.core import QgsFeature, QgsPoint

class _Events(QObject):
    # Emit when you need to open a image in the main window
    openimage = pyqtSignal(object)

    #Emit to open a url
    openurl = pyqtSignal(QUrl)

    # Emit when requesting to open a feature form
    openfeatureform = pyqtSignal(object, QgsFeature)

    # Connect to listen to GPS status updates.
    gpspostion = pyqtSignal(QgsPoint, object)

    # Emit when you need to open the on screen keyboard
    openkeyboard = pyqtSignal()

RoamEvents = _Events()
