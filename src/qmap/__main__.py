"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""
from qgis.core import QgsApplication

import sys

from mainwindow import MainWindow
import project

app = QgsApplication(sys.argv, True)
QgsApplication.initQgis()
window = MainWindow()
projectfolder = sys.argv[1]
projects = project.getProjects(projectfolder)
window.loadProjectList(projects)
window.show()
app.exec_()
QgsApplication.exitQgis()