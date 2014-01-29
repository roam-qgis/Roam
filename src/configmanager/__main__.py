import sys

print sys.path

from qgis.core import QgsApplication
import roam.environ
import roam.project

from configmanager.ui import ConfigManagerDialog

prefixpath, settingspath = roam.environ.setup(sys.argv)

app = QgsApplication(sys.argv, True)
QgsApplication.setPrefixPath(prefixpath, True)
QgsApplication.initQgis()

projectpath = roam.environ.projectpath(sys.argv)
projects = roam.project.getProjects(projectpath)

dialog = ConfigManagerDialog()
dialog.loadprojects(projects)
dialog.exec_()

app.exec_()
QgsApplication.exitQgis()
sys.exit()