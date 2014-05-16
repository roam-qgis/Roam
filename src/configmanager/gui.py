from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSignal
from configmanager.ui.nodewidgets.ui_projectswidget import Ui_projectsnode


class ProjectsNode(Ui_projectsnode, QWidget):
    projectlocationchanged = pyqtSignal(str)
    newproject = pyqtSignal()

    def __init__(self, parent=None):
        super(ProjectsNode, self).__init__(parent)
        self.setupUi(self)

        self.newprojectButton.clicked.connect(self.newproject.emit)
        self.projectlocations.currentIndexChanged[str].connect(self.projectlocationchanged.emit)

    def setprojectfolders(self, folders):
        for folder in folders:
            self.projectlocations.addItem(folder)

