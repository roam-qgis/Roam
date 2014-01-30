import os
import sys

print sys.path

from qgis.core import QgsApplication
import roam.environ
import roam.project

from configmanager.ui.configmanagerdialog import ConfigManagerDialog

prefixpath, settingspath = roam.environ.setup(sys.argv)

app = QgsApplication(sys.argv, True)
QgsApplication.setPrefixPath(prefixpath, True)
QgsApplication.initQgis()

projectpath = roam.environ.projectpath(sys.argv)
projects = list(roam.project.getProjects(projectpath))


def backupprojects(projects):
    """
    Backup the projects that are already there so we can just edit the
    settings in the config manager with no fear.
    """
    for project in projects:
        settingspath = os.path.join(project.folder, "settings.config")
        import shutil
        shutil.copy(settingspath, settingspath + '~')

dialog = ConfigManagerDialog()
# Backup before we load.
backupprojects(projects)
dialog.loadprojects(projects)
dialog.showMaximized()

app.exec_()
QgsApplication.exitQgis()
sys.exit()