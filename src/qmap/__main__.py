"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""
from qgis.core import QgsApplication

import sys

from qmap.mainwindow import MainWindow
import qmap.project as project
import qmap.utils

app = QgsApplication(sys.argv, True)
QgsApplication.initQgis()

window = MainWindow()
projects = project.getProjects(sys.argv[1])
window.loadProjectList(projects)
qmap.utils.settings_notify.settings_changed.connect(window.show)

window.actionProject.toggle()
window.show()
app.exec_()
QgsApplication.exitQgis()