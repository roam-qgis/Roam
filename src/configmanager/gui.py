from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtCore import pyqtSignal


import roam.config

from configmanager.ui.nodewidgets.ui_projectswidget import Ui_projectsnode


class ProjectsNode(Ui_projectsnode, QWidget):
    projectlocationchanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ProjectsNode, self).__init__(parent)
        self.setupUi(self)

        self.projectlocations.currentIndexChanged[str].connect(self.projectlocationchanged.emit)

    def setprojectfolders(self, folders):
        for folder in folders:
            self.projectlocations.addItem(folder)


