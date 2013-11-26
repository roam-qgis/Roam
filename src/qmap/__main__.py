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

from PyQt4.QtGui import QApplication, QFont, QImageReader, QImageWriter
from PyQt4.QtCore import QDir, QCoreApplication, QLibrary
# We have to import QtSql or else the MSSQL driver will fail to load.
import PyQt4.QtSql

# We have to start this here or else the image drivers don't load for some reason
app = QgsApplication(sys.argv, True)

import qmap
import qmap.utils
from qmap.mainwindow import MainWindow


def excepthook(errorhandler, exctype, value, traceback):
    errorhandler(exctype, value, traceback)
    qmap.utils.error("Uncaught exception", exc_info=(exctype, value, traceback))

start = time.time()
qmap.utils.info("Loading Roam")
apppath = QDir(QCoreApplication.applicationDirPath())

QgsApplication.setPrefixPath(apppath.absolutePath(), True)
QgsApplication.initQgis()

qmap.utils.info(QgsProviderRegistry.instance().pluginList())
qmap.utils.info(QImageReader.supportedImageFormats())
qmap.utils.info(QImageWriter.supportedImageFormats())
qmap.utils.info(QgsApplication.libraryPaths())

QApplication.setStyle("Plastique")
QApplication.setFont(QFont('Segoe UI'))

window = MainWindow()
sys.excepthook = partial(excepthook, window.raiseerror)

try:
    projectpath = sys.argv[1]
except IndexError:
    projectpath = os.path.join(os.getcwd(), "projects")

projects = qmap.project.getProjects(projectpath)
window.loadprojects(projects)
qmap.utils.settings_notify.settings_changed.connect(window.show)
qmap.utils.settings_notify.settings_changed.connect(window.updateicons)

window.actionProject.toggle()
window.viewprojects()
window.updateUIState(1)
window.show()

qmap.utils.info("Roam Loaded in {}".format(str(time.time() - start)))

app.exec_()
QgsApplication.exitQgis()
sys.exit()