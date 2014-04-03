from PyQt4.QtCore import pyqtSignal, QObject, QUrl

from qgis.core import QgsFeature, QgsPoint

class _Events(QObject):
    # Emit when you need to open a image in the main window
    openimage = pyqtSignal(object)
    openurl = pyqtSignal(QUrl)
    openfeatureform = pyqtSignal(object, QgsFeature)
    gpspostion = pyqtSignal(QgsPoint, object)

RoamEvents = _Events()
