from qgis.core import QGis, QgsPoint


def setRubberBand(canvas, selectRect, rubberBand):
    transform = canvas.getCoordinateTransform()
    lowerleft = transform.toMapCoordinates( selectRect.left(), selectRect.bottom() )
    upperright = transform.toMapCoordinates( selectRect.right(), selectRect.top() )
    
    if rubberBand:
        rubberBand.reset( QGis.Polygon );
        rubberBand.addPoint( lowerleft, False);
        rubberBand.addPoint( QgsPoint( upperright.x(), lowerleft.y() ), False);
        rubberBand.addPoint( upperright, False);
        rubberBand.addPoint( QgsPoint( lowerleft.x(), upperright.y() ), True );
    