import os
import sys

from functools import partial

from qgis.core import QgsApplication, QgsProviderRegistry, QGis

from PyQt4.QtGui import QApplication, QFont, QIcon

import roam
import roam.environ
import roam.project
import roam.resources_rc

from configmanager.ui.configmanagerdialog import ConfigManagerDialog

import configmanager.settings
import configmanager.logger as logger

logger.info("Loading Roam Config Manager")
prefixpath, settingspath = roam.environ.setup(sys.argv)

app = QgsApplication(sys.argv, True)
QgsApplication.setPrefixPath(prefixpath, True)
QgsApplication.initQgis()

logger.info(QgsApplication.showSettings())
logger.info(QgsProviderRegistry.instance().pluginList())
logger.info(QgsApplication.libraryPaths())

logger.info("Roam Version: {}".format(roam.__version__))
logger.info("QGIS Version: {}".format(str(QGis.QGIS_VERSION)))

QApplication.setStyle("Plastique")
QApplication.setFont(QFont('Segoe UI'))
QApplication.setWindowIcon(QIcon(':/branding/logo'))
QApplication.setApplicationName("IntraMaps Roam Config Manager")

configmanager.settings.load(settingspath)

projectpath = roam.environ.projectpath(sys.argv)
projects = list(roam.project.getProjects(projectpath))

def excepthook(errorhandler, exctype, value, traceback):
    logger.error("Uncaught exception", exc_info=(exctype, value, traceback))
    errorhandler(exctype, value, traceback)

dialog = ConfigManagerDialog(projectpath)
sys.excepthook = partial(excepthook, dialog.raiseerror)
dialog.loadprojects(projects)
dialog.showMaximized()

app.exec_()

configmanager.settings.save(settingspath)

QgsApplication.exitQgis()
sys.exit()