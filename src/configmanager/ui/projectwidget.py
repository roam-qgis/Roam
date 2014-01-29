from PyQt4.QtGui import QWidget
from configmanager.ui.ui_projectwidget import Ui_Form


class ProjectWidget(Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)

    def setproject(self, project):
        self.project = project
        self._updateforproject(self.project)

    def _updateforproject(self, project):
        self.titleText.setText(project.name)


