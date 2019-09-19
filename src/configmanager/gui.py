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
        self.btnNewProject.setEnabled(False)
        self.projectNameEdit.textChanged.connect(self._update_button)

    def _update_button(self, value):
        if not value:
            self.btnNewProject.setEnabled(False)

        folder = self.projectlocations.currentText()
        if configmanager.projects.directory_exsits(value, folder):
            self.btnNewProject.setEnabled(False)
        else:
            self.btnNewProject.setEnabled(True)

    def _create_project(self):
        name = configmanager.projects.new_directory_name(self.projectNameEdit.text(), "Project")

        if configmanager.projects.directory_exsits(name, self.projectlocations.currentText()):
            return

        project = configmanager.projects.create_project(self.projectlocations.currentText(), name)

        self.projectNameEdit.clear()

        ConfigEvents.emit_projectCreated(project)

    def setprojectfolders(self, folders):
        for folder in folders:
            self.projectlocations.addItem(folder)


