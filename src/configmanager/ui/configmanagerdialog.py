import os
import shutil
import random

from datetime import datetime

from PyQt4.QtGui import QDialog, QFont, QColor, QIcon, QMessageBox
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

    def removeRow(self, row, parent=None):
        self.beginRemoveRows(QModelIndex(), row, row)
        del self.projects[row]
        self.endRemoveRows()
        return True

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
        self.removeProjectButton.pressed.connect(self.removeproject)
        self.projectwidget.projectupdated.connect(self.projectupdated)

    def removeproject(self):
        index = self.projectList.currentIndex()
        currentproject = index.data(Qt.UserRole)
        archivefolder = os.path.join(self.projectfolder, "_archive")

        message = ("Do you want to delete this project? <br><br> "
                   "Deleted projects will be moved to the _archive folder in {}<br><br>"
                   "<i>Projects can be recovered by moving the folder back to the projects folder</i>".format(self.projectfolder))
        button = QMessageBox.warning(self, "Remove project?", message,
                                         QMessageBox.Yes | QMessageBox.No)
        if button == QMessageBox.Yes:
            newindex = self.projectmodel.index(index.row() + 1, 0)
            if not newindex.isValid():
                newindex = self.projectmodel.index(0, 0)

            # Move to a different project to unlock the current one.
            self.projectList.setCurrentIndex(newindex)

            shutil.move(currentproject.folder, archivefolder)
            self.projectmodel.removeRow(index.row())

    def newproject(self):
        templateProject = os.path.join(os.path.dirname(__file__), "..", "templates/templateProject")
        newfolder = os.path.join(self.projectfolder, "newProject{}".format(datetime.today().strftime('%d%m%y%f')))
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
        self.projectwidget.setproject(project)

    def projectupdated(self):
        index = self.projectList.currentIndex()
        self.projectmodel.dataChanged.emit(index, index)
