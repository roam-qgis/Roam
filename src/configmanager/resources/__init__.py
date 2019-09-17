from PyQt5.QtGui import QIcon
from qgis._core import QgsWkbTypes

# noinspection PyUnresolvedReferences
# This required to load the icons from the resource file or
# else you get blanks
from configmanager.resources import resources_rc

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
    icon = ':/icons/{}'.format(widgettype)
    return QIcon(icon)
