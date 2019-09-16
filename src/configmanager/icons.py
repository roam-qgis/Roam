from PyQt5.QtGui import QIcon
from qgis._core import QgsWkbTypes

icons = {
    QgsWkbTypes.PointGeometry: ":/icons/PointLayer",
    QgsWkbTypes.PolygonGeometry: ":/icons/PolygonLayer",
    QgsWkbTypes.LineGeometry: ":/icons/LineLayer",
    QgsWkbTypes.NoGeometry: ":/icons/TableLayer"
}


def widgeticon(widgettype):
    """
    Return the icon for the given widget type.
    :param widgettype: The widget type to get the icon for
    :return: The QIcon for the given widget based on type.
    """
    return QIcon(':/icons/{}'.format(widgettype))