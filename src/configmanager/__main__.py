import os
import sys
import functools

srcpath = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(srcpath)

import roam.environ
import roam.config

roamapp = roam.environ.setup(sys.argv)
roam.config.load(roamapp.settingspath)

import roam
import roam.project
import roam.resources_rc
import configmanager.logger as logger

import roam.editorwidgets.core
roam.editorwidgets.core.registerallwidgets()

from PyQt4.QtGui import QApplication, QFont, QIcon
from qgis.core import QGis
from configmanager.ui.configmanagerdialog import ConfigManagerDialog

logger.info("Loading Roam Config Manager")
logger.info("Roam Version: {}".format(roam.__version__))
logger.info("QGIS Version: {}".format(str(QGis.QGIS_VERSION)))

QApplication.setWindowIcon(QIcon(':/branding/logo'))
QApplication.setApplicationName("IntraMaps Roam Config Manager")

projectpaths = roam.environ.projectpaths(sys.argv, roamapp, roam.config.settings)
#projects = list(roam.project.getProjects(projectpaths))

def excepthook(errorhandler, exctype, value, traceback):
    logger.error("Uncaught exception", exc_info=(exctype, value, traceback))
    errorhandler(exctype, value, traceback)

dialog = ConfigManagerDialog()
sys.excepthook = functools.partial(excepthook, dialog.raiseerror)
dialog.addprojectfolders(projectpaths)
#dialog.loadprojects(projects)
dialog.showMaximized()

roamapp.exec_()
roam.config.save()
roamapp.exit()
