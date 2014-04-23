from qgis.core import QgsGeometry

class RoamGeometry(QgsGeometry):
    def __init__(self):
        super(RoamGeometry, self).__init__()
        self.z = None

    @classmethod
    def fromPointZ(cls, point, z):
        geom = cls.fromPoint(point)
        geom.z = z
        return geom