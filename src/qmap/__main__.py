"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""
from __future__ import absolute_import

import time
import sys

from qgis.core import QgsApplication, QgsPythonRunner
from PyQt4.QtGui import QApplication

from qmap.mainwindow import MainWindow
import qmap.project as project
import qmap.utils

start = time.time()

qmap.utils.info("Loading Roam")

with qmap.utils.Timer("Load time:", logging=qmap.utils.info):
    app = QgsApplication(sys.argv, True)
    QgsApplication.initQgis()
    QApplication.setStyle("Plastique")

    window = MainWindow()
    projects = project.getProjects(sys.argv[1])
    window.loadProjectList(projects)
    qmap.utils.settings_notify.settings_changed.connect(window.show)

    window.actionProject.toggle()
    window.updateUIState(1)
    window.show()

app.exec_()
QgsApplication.exitQgis()