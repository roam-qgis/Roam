"""
API for talking to QGIS
"""

from qgis.core import QgsProject


def close_project() -> None:
    """
    Remove all layers from the current project
    """
    QgsProject.instance().removeAllMapLayers()
