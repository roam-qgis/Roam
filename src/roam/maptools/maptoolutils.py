from qgis.gui import QgsMapMouseEvent
from qgis.core import QgsWkbTypes, QgsPointXY, QgsPoint


def point_from_event(event: QgsMapMouseEvent, snapping: bool) -> QgsPoint:
    """
    Returns the point from the mouse canvas event. If snapping is enabled it will be
    snapped using the settings.
    :param event: The map mouse event.
    :return: Point for the map canvas event.
    """
    if snapping:
        point = QgsPoint(event.snapPoint())
        point.addZValue(0)
    else:
        point = QgsPoint(event.originalMapPoint())
        point.addZValue(0)
    return point


def setRubberBand(canvas, selectRect, rubberBand):
    transform = canvas.getCoordinateTransform()
    lowerleft = transform.toMapCoordinates(selectRect.left(), selectRect.bottom())
    upperright = transform.toMapCoordinates(selectRect.right(), selectRect.top())

    if rubberBand:
        rubberBand.reset(QgsWkbTypes.PolygonGeometry);
        rubberBand.addPoint(lowerleft, False);
        rubberBand.addPoint(QgsPointXY(upperright.x(), lowerleft.y()), False);
        rubberBand.addPoint(upperright, False);
        rubberBand.addPoint(QgsPointXY(lowerleft.x(), upperright.y()), True);
