from qgis.gui import QgsMapMouseEvent
from qgis.core import QgsWkbTypes, QgsPointXY
from qgis.PyQt.QtCore import QPoint


def point_from_event(event: QgsMapMouseEvent, snapping: bool) -> QgsPointXY:
    """
    Returns the point from the mouse canvas event. If snapping is enabled it will be
    snapped using the settings.
    :param event: The map mouse event.
    :return: Point for the map canvas event.
    """
    if snapping:
        point = event.snapPoint()
    else:
        point = event.originalMapPoint()
    return point


def setRubberBand(canvas, selectRect, rubberBand):
    transform = canvas.getCoordinateTransform()
    lowerleft = transform.toMapCoordinates(QPoint(int(selectRect.left()), int(selectRect.bottom())))
    upperright = transform.toMapCoordinates(QPoint(int(selectRect.right()), int(selectRect.top())))

    if rubberBand:
        rubberBand.reset(QgsWkbTypes.PolygonGeometry);
        rubberBand.addPoint(lowerleft, False);
        rubberBand.addPoint(QgsPointXY(upperright.x(), lowerleft.y()), False);
        rubberBand.addPoint(upperright, False);
        rubberBand.addPoint(QgsPointXY(lowerleft.x(), upperright.y()), True);
