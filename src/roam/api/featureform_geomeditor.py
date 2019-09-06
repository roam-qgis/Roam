from PyQt5.QtWidgets import QStackedWidget
from qgis._core import QgsWkbTypes, QgsGeometry, QgsPoint

from roam.ui.ui_geomwidget import Ui_GeomWidget


class GeomWidget(Ui_GeomWidget, QStackedWidget):
    def __init__(self, parent=None):
        super(GeomWidget, self).__init__(parent)
        self.setupUi(self)
        self.geom = None
        self.edited = False

    def set_geometry(self, geom):
        if not geom:
            return

        self.geom = geom
        if self.geom.type() == QgsWkbTypes.PointGeometry:
            self.setCurrentIndex(0)
            point = geom.asPoint()
            self.xedit.setText(str(point.x()))
            self.yedit.setText(str(point.y()))
            self.xedit.textChanged.connect(self.mark_edited)
            self.yedit.textChanged.connect(self.mark_edited)
        else:
            self.setCurrentIndex(1)

    def geometry(self):
        if self.geom.type() == QgsWkbTypes.PointGeometry:
            x = float(self.xedit.text())
            y = float(self.yedit.text())
            return QgsGeometry.fromPointXY(QgsPoint(x, y))

    def mark_edited(self):
        self.edited = True