from qgis.core import QgsApplication

import sys

from mainwindow import MainWindow

app = QgsApplication(sys.argv, True)
QgsApplication.initQgis()
window = MainWindow()
window.show()
app.exec_()
QgsApplication.exitQgis()