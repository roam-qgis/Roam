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

import roam
import roam.utils
from roam.mainwindow import MainWindow


def excepthook(errorhandler, exctype, value, traceback):
    errorhandler(exctype, value, traceback)
    roam.utils.error("Uncaught exception", exc_info=(exctype, value, traceback))

start = time.time()
roam.utils.info("Loading Roam")
apppath = QDir(QCoreApplication.applicationDirPath())

if '__file__' in globals() and 'src' in __file__:
    # Setup the paths for OSGeo4w if we are running out of the src folder.
    QgsApplication.setPrefixPath(r"C:\OSGeo4W\apps\qgis-dev", True)
else:
    QgsApplication.setPrefixPath(apppath.absolutePath(), True)

QgsApplication.initQgis()

roam.utils.info(QgsProviderRegistry.instance().pluginList())
roam.utils.info(QImageReader.supportedImageFormats())
roam.utils.info(QImageWriter.supportedImageFormats())
roam.utils.info(QgsApplication.libraryPaths())

QApplication.setStyle("Plastique")
QApplication.setFont(QFont('Segoe UI'))

window = MainWindow()
sys.excepthook = partial(excepthook, window.raiseerror)

try:
    projectpath = sys.argv[1]
except IndexError:
    projectpath = os.path.join(os.getcwd(), "projects")

projects = roam.project.getProjects(projectpath)
window.loadprojects(projects)
roam.utils.settings_notify.settings_changed.connect(window.show)
roam.utils.settings_notify.settings_changed.connect(window.updateicons)

window.actionProject.toggle()
window.viewprojects()
window.updateUIState(1)
window.show()

roam.utils.info("Roam Loaded in {}".format(str(time.time() - start)))

app.exec_()
QgsApplication.exitQgis()
sys.exit()