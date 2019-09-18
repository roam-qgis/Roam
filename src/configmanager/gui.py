from qgis.PyQt.QtWidgets import QWidget, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal


from configmanager.events import ConfigEvents
import roam.config
import configmanager.projects

from configmanager.ui.nodewidgets.ui_projectswidget import Ui_projectsnode


class ProjectsNode(Ui_projectsnode, QWidget):
    projectlocationchanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ProjectsNode, self).__init__(parent)
        self.setupUi(self)

        self.projectlocations.currentIndexChanged[str].connect(self.projectlocationchanged.emit)
        self.btnNewProject.pressed.connect(self._create_project)

    def _create_project(self):
        project = configmanager.projects.newproject(self.projectlocations.currentText())
        ConfigEvents.emit_projectCreated(project)

    def setprojectfolders(self, folders):
        for folder in folders:
            self.projectlocations.addItem(folder)


