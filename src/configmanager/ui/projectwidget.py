from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QStandardItemModel, QStandardItem, QIcon

from configmanager.ui.ui_projectwidget import Ui_Form


class ProjectWidget(Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.formmodel = QStandardItemModel()
        self.formlist.setModel(self.formmodel)

    def setproject(self, project):
        self.project = project
        self._updateforproject(self.project)

    def _updateforproject(self, project):
        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)
        self._loadforms(project.forms)

    def _loadforms(self, forms):
        self.formmodel.clear()
        for form in forms:
            item = QStandardItem(form.name)
            item.setIcon(QIcon(form.icon))
            item.setData(form, Qt.UserRole)
            self.formmodel.appendRow(item)




