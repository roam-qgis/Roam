from qgis.core import QgsWkbTypes, QgsPoint


def setRubberBand(canvas, selectRect, rubberBand):
    transform = canvas.getCoordinateTransform()
    lowerleft = transform.toMapCoordinates(selectRect.left(), selectRect.bottom())
    upperright = transform.toMapCoordinates(selectRect.right(), selectRect.top())

    if rubberBand:
        rubberBand.reset(QgsWkbTypes.PolygonGeometry);
        rubberBand.addPoint(lowerleft, False);
        rubberBand.addPoint(QgsPoint(upperright.x(), lowerleft.y()), False);
        rubberBand.addPoint(upperright, False);
        rubberBand.addPoint(QgsPoint(lowerleft.x(), upperright.y()), True);
