from qgis.core import QgsWkbTypes, QgsPointXY


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
