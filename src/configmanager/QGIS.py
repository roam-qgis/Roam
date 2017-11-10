"""
API for talking to QGIS
"""

from qgis.core import QgsProject, QgsMapLayerRegistry

def close_project():
    QgsMapLayerRegistry.instance().removeAllMapLayers()
