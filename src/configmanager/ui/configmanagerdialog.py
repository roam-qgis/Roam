from PyQt4.QtGui import QDialog, QFont, QColor, QIcon
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt

from configmanager.ui import ui_configmanager


class ProjectModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(ProjectModel, self).__init__(parent)
        self.projects = []

    def loadprojects(self, projects):
        self.beginResetModel()
        self.projects = list(projects)
        self.endResetModel()

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
    def __init__(self, parent=None):
        super(ConfigManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.projectmodel = ProjectModel()
        self.projectList.setModel(self.projectmodel)
        self.projectList.selectionModel().currentChanged.connect(self.updatecurrentproject)
        self.projectwidget.adjustSize()

    def loadprojects(self, projects):
        self.projectmodel.loadprojects(projects)

    def updatecurrentproject(self, index, _):
        project = index.data(Qt.UserRole)
        self.projectwidget.setproject(project, loadqgis=True)




