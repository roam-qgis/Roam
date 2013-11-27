from PyQt4.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt4.QtGui import QIcon

from roam.uifiles import sync_widget, sync_base


class ProjectsSyncModel(QAbstractTableModel):
    def __init__(self, projects=None, parent=None):
        super(ProjectsSyncModel, self).__init__(parent)
        self.projects = list(projects)
        if self.projects:
            self.columns = max([len(list(project.syncprovders())) for project in self.projects])
        else:
            self.columns = 0

    def rowCount(self, index=QModelIndex()):
        """ Returns the number of rows the model holds. """
        return len(self.projects)

    def columnCount(self, index=QModelIndex()):
        """ Returns the number of columns the model holds. """
        return self.columns

    def data(self, index, role=Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
            returning data, return None
        """
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.projects):
            return None

        project = self.projects[index.row()]
        providers = list(project.syncprovders())
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return project.name

            try:
                provider = providers[index.column()]
                name = provider.name
                return name
            except IndexError:
                pass
        if role == Qt.DecorationRole:
            return None
            if index.column() == 0:
                pixmap = QPixMap()
                return QIcon(project.splash)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """ Set the headers to be displayed. """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Name"

        return None


class SyncWidget(sync_widget, sync_base):
    def __init__(self, parent=None):
        super(SyncWidget, self).__init__(parent)
        self.setupUi(self)

    def loadprojects(self, projects):
        model = ProjectsSyncModel(projects)
        self.synctable.setModel(model)
        self.synctable.resizeColumnsToContents()
        self.synctable.resizeRowsToContents()

