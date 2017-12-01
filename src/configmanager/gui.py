from PyQt4.QtGui import QWidget, QFileDialog
from PyQt4.QtCore import pyqtSignal


import roam.config

from configmanager.ui.nodewidgets.ui_projectswidget import Ui_projectsnode


class ProjectsNode(Ui_projectsnode, QWidget):
    projectlocationchanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ProjectsNode, self).__init__(parent)
        self.setupUi(self)

        self.projectlocations.currentIndexChanged[str].connect(self.projectlocationchanged.emit)
        path = roam.config.settings.get("publish", {}).get("path", '')
        self.deployLocationText.setText(path)
        self.deployLocationText.textChanged.connect(self.update_deploy_path)
        self.filePickerButton.pressed.connect(self.pick_folder)

    def pick_folder(self):
        path = QFileDialog().getExistingDirectory(self, "Select project publish location",
                                                  self.deployLocationText.text())
        self.deployLocationText.setText(path)
        self.update_deploy_path(self.deployLocationText.text())

    def setprojectfolders(self, folders):
        for folder in folders:
            self.projectlocations.addItem(folder)

    def update_deploy_path(self, text):
        roam.config.settings["publish"] = {"path": text}
        roam.config.save()

