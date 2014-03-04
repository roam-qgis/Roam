import os
import sys

from functools import partial

from qgis.core import QgsApplication

from PyQt4.QtGui import QApplication, QFont, QIcon

import roam.environ
import roam.project
import roam.resources_rc

from configmanager.ui.configmanagerdialog import ConfigManagerDialog

prefixpath, settingspath = roam.environ.setup(sys.argv)

app = QgsApplication(sys.argv, True)
QgsApplication.setPrefixPath(prefixpath, True)
QgsApplication.initQgis()

QApplication.setStyle("Plastique")
QApplication.setFont(QFont('Segoe UI'))
QApplication.setWindowIcon(QIcon(':/branding/logo'))
QApplication.setApplicationName("IntraMaps Roam Config Manager")

projectpath = roam.environ.projectpath(sys.argv)
projects = list(roam.project.getProjects(projectpath))

def excepthook(errorhandler, exctype, value, traceback):
    errorhandler(exctype, value, traceback)

dialog = ConfigManagerDialog(projectpath)
sys.excepthook = partial(excepthook, dialog.raiseerror)
dialog.loadprojects(projects)
dialog.showMaximized()

app.exec_()
QgsApplication.exitQgis()
sys.exit()