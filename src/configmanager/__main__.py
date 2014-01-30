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


def saveproject(oldsettings, project):
    """
    Save the project config to disk.
    """
    def writesettings(settings, path):
        with open(path, 'w') as f:
            roam.yaml.dump(data=settings, stream=f, default_flow_style=False)

    settingspath = os.path.join(project.folder, "settings.config")
    writesettings(oldsettings, settingspath + '~')
    writesettings(project.settings, settingspath)

dialog = ConfigManagerDialog()
dialog.projectwidget.projectsaved.connect(saveproject)
dialog.loadprojects(projects)
dialog.showMaximized()

app.exec_()
QgsApplication.exitQgis()
sys.exit()