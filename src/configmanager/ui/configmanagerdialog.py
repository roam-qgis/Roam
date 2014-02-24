import os
import random

from PyQt4.QtGui import QDialog, QFont, QColor, QIcon
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt

from configmanager.ui import ui_configmanager

import shutil
import roam.project

class ProjectModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(ProjectModel, self).__init__(parent)
        self.projects = []

    def loadprojects(self, projects):
        self.beginResetModel()
        self.projects = list(projects)
        self.endResetModel()

    def addproject(self, project):
        count = self.rowCount()
        self.beginInsertRows(QModelIndex(), count, count + 1)
        self.projects.append(project)
        self.endInsertRows()
        return self.index(self.rowCount() - 1, 0)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def index(self, row, column, parent=QModelIndex()):
        try:
            layer = self.projects[row]
        except IndexError:
            return QModelIndex()

        return self.createIndex(row, column, layer)

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self.projects)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role):
        if not index.isValid() or index.internalPointer() is None:
            return

        project = index.internalPointer()
        if role == Qt.DisplayRole:
            return project.name
        elif role == Qt.DecorationRole:
            return QIcon(project.splash)
        elif role == Qt.UserRole:
            return project
        elif role == Qt.ForegroundRole:
            if not project.valid:
                return QColor(Qt.red)


class ConfigManagerDialog(ui_configmanager.Ui_ProjectInstallerDialog, QDialog):
    def __init__(self, projectfolder, parent=None):
        super(ConfigManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.projectmodel = ProjectModel()
        self.projectList.setModel(self.projectmodel)
        self.projectList.selectionModel().currentChanged.connect(self.updatecurrentproject)
        self.projectwidget.adjustSize()
        self.setWindowFlags(Qt.Window)
        self.projectfolder = projectfolder
        self.newProjectButton.pressed.connect(self.newproject)

    def newproject(self):
        templateProject = os.path.join(os.path.dirname(__file__), "..", "templates/templateProject")
        newfolder = os.path.join(self.projectfolder, "newProject{}".format(random.randint(1, 100)))
        shutil.copytree(templateProject, newfolder)
        project = roam.project.Project.from_folder(newfolder)
        project.settings['forms'] = {}
        newindex = self.projectmodel.addproject(project)
        self.projectList.setCurrentIndex(newindex)

    def loadprojects(self, projects):
        self.projectmodel.loadprojects(projects)
        index = self.projectmodel.index(0, 0)
        self.projectList.setCurrentIndex(index)

    def updatecurrentproject(self, index, _):
        project = index.data(Qt.UserRole)
        self.projectwidget.setproject(project, loadqgis=True)




