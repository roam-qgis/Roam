"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""
from __future__ import absolute_import

import sys

from qgis.core import QgsApplication

from qmap.mainwindow import MainWindow
import qmap.project as project
import qmap.utils
import time

start = time.time()
app = QgsApplication(sys.argv, True)
QgsApplication.initQgis()

window = MainWindow()
projects = project.getProjects(sys.argv[1])
window.loadProjectList(projects)
qmap.utils.settings_notify.settings_changed.connect(window.show)

window.actionProject.toggle()
window.updateUIState(1)
window.show()
print time.time() - start
app.exec_()
QgsApplication.exitQgis()