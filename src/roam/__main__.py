"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""
from functools import partial
import time
import os
import sys
import logging


from qgis.core import QgsApplication, QgsPythonRunner, QgsProviderRegistry
from PyQt4 import uic
from PyQt4.QtGui import QApplication, QFont, QImageReader, QImageWriter
from PyQt4.QtCore import QDir, QCoreApplication, QLibrary
# We have to import QtSql or else the MSSQL driver will fail to load.
import PyQt4.QtSql

uic.uiparser.logger.setLevel(logging.INFO)
uic.properties.logger.setLevel(logging.INFO)

import roam.yaml as yaml

RUNNING_FROM_FILE = '__file__' in globals()
apppath = os.path.dirname(os.path.realpath(sys.argv[0]))
prefixpath = os.path.join(apppath, "libs", "qgis")
settingspath = os.path.join(apppath, "settings.config")

if RUNNING_FROM_FILE:
    print "Running from file"
    # Setup the paths for OSGeo4w if we are running from a file
    # this means that we are not running from a frozen app.
    os.environ['PATH'] += r";C:\OSGeo4W\bin;C:\OSGeo4W\apps\qgis\bin"
    sys.path.append(r"C:\OSGeo4W\apps\qgis\python")
    os.environ["GDAL_DATA"] = r"C:\OSGeo4W\share\gdal"
    os.environ["GDAL_DRIVER_PATH"] = r"C:\OSGeo4W\bin\gdalplugins"
    os.environ["QT_PLUGIN_PATH"] = r"C:\OSGeo4W\apps\Qt4\plugins"
    prefixpath = r"C:\OSGeo4W\apps\qgis"
    settingspath = os.path.join(apppath, "..", "settings.config")

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

QgsApplication.setPrefixPath(prefixpath, True)
QgsApplication.initQgis()

roam.utils.info(QgsApplication.showSettings())
roam.utils.info(QgsProviderRegistry.instance().pluginList())
roam.utils.info(QImageReader.supportedImageFormats())
roam.utils.info(QImageWriter.supportedImageFormats())
roam.utils.info(QgsApplication.libraryPaths())

QApplication.setStyle("Plastique")
QApplication.setFont(QFont('Segoe UI'))

class Settings:
    def __init__(self, path):
        self.path = path
        self.settings = {}

    def load(self):
        settingspath = self.path
        with open(settingspath, 'r') as f:
            self.settings = yaml.load(f)

    def save(self):
        with open(self.path, 'w') as f:
            yaml.dump(data=self.settings, stream=f, default_flow_style=False)

settings = Settings(settingspath)
settings.load()

window = MainWindow(settings=settings)
sys.excepthook = partial(excepthook, window.raiseerror)

try:
    projectpath = sys.argv[1]
except IndexError:
    projectpath = os.path.join(os.getcwd(), "projects")

sys.path.append(projectpath)

projects = roam.project.getProjects(projectpath)
window.loadprojects(projects)

window.actionProject.toggle()
window.viewprojects()
window.updateUIState(1)
window.show()

roam.utils.info("Roam Loaded in {}".format(str(time.time() - start)))

app.exec_()
QgsApplication.exitQgis()
sys.exit()