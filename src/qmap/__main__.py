"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""
from __future__ import absolute_import
from functools import partial

import time
import os
import sys

from qgis.core import QgsApplication, QgsPythonRunner, QgsProviderRegistry
from PyQt4.QtGui import QApplication, QFont
from PyQt4.QtCore import QDir, QCoreApplication

from qmap.mainwindow import MainWindow
import qmap.project as project
import qmap.utils

start = time.time()

qmap.utils.info("Loading Roam")


def excepthook(errorhandler, exctype, value, traceback):
    errorhandler(exctype, value, traceback)
    qmap.utils.error("Uncaught exception", exc_info=(exctype, value, traceback))

with qmap.utils.Timer("Load time:", logging=qmap.utils.info):
    app = QgsApplication(sys.argv, True)
    apppath = QDir(QCoreApplication.applicationDirPath())
    pluginpath = os.path.join(apppath.absolutePath(), "libs")
    qmap.utils.info('MyPath: ' + pluginpath)
    QgsApplication.setPrefixPath(pluginpath, True)
    QgsApplication.initQgis()

    qmap.utils.info(QgsProviderRegistry.instance().libraryDirectory().path())
    qmap.utils.info(QgsProviderRegistry.instance().pluginList())

    QApplication.setStyle("Plastique")
    QApplication.setFont(QFont('Segoe UI'))

    window = MainWindow()
    sys.excepthook = partial(excepthook, window.raiseerror)

    try:
        projectpath = sys.argv[1]
    except IndexError:
        projectpath = os.path.join(os.getcwd(), "projects")

    projects = project.getProjects(projectpath)
    window.loadprojects(projects)
    qmap.utils.settings_notify.settings_changed.connect(window.show)
    qmap.utils.settings_notify.settings_changed.connect(window.updateicons)

    window.actionProject.toggle()
    window.viewprojects()
    window.updateUIState(1)
    window.show()

app.exec_()
QgsApplication.exitQgis()
sys.exit()