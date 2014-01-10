import sys
import sip

apis = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
for api in apis:
    sip.setapi(api, 2)

from PyQt4.QtGui import (QApplication, QDialog, QListWidgetItem, QIcon, QWidget,
                         QVBoxLayout, QLabel, QScrollArea, QFrame, QFormLayout,
                         QLineEdit)
from PyQt4.QtCore import Qt
from ui_installer import Ui_ProjectInstallerDialog
from roam.project import getProjects
from postinstall import get_project_tokens, sort_tokens

class ProjectPageWidget(QWidget):
    def __init__(self, project, parent=None):
        super(ProjectPageWidget, self).__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        label = QLabel("<b>{}</b>".format(project.name))
        layout.addWidget(label)
        self.scollarea = QScrollArea()
        self.scollarea.setLayout(QFormLayout())
        self.scollarea.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.scollarea)

        tokens = sort_tokens(get_project_tokens(project.folder))

        self.createtokenwidgets(tokens, self.scollarea.layout())

    def createtokenwidgets(self, tokens, layout):
        for token in tokens:
            label = QLabel(token)
            lineedit = QLineEdit()
            lineedit.setObjectName(token)
            layout.addRow(label, QLineEdit())





class ProjectInstallerDialog(Ui_ProjectInstallerDialog, QDialog):
    def __init__(self, parent=None):
        super(ProjectInstallerDialog, self).__init__( parent)
        self.setupUi(self)

    def loadprojects(self, projects):
        for project in projects:
            item = QListWidgetItem(project.name, self.mOptionsListWidget)
            item.setData(Qt.UserRole, project)
            item.setIcon(QIcon(project.splash))
            widget = ProjectPageWidget(project)
            self.mOptionsStackedWidget.addWidget(widget)

        self.mOptionsListWidget.adjustSize()

app = QApplication([])

dialog = ProjectInstallerDialog()
projects = getProjects(sys.argv[1])
dialog.loadprojects(projects)
dialog.exec_()

app.exec_()
app.exit(0)