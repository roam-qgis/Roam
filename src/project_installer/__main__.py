import os
import sys
import sip
import logging

print sys.path

apis = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
for api in apis:
    sip.setapi(api, 2)

from PyQt4.QtGui import (QApplication, QDialog, QListWidgetItem, QIcon, QWidget,
                         QVBoxLayout, QLabel, QScrollArea, QFrame, QFormLayout,
                         QLineEdit)
from PyQt4.QtCore import Qt, pyqtSignal

from roam.project import getProjects

from project_installer.ui_installer import Ui_ProjectInstallerDialog
from project_installer.ui_project import Ui_ProjectWidget
from project_installer.postinstall import (get_project_tokens, sort_tokens, replace_templates_in_folder,
                         run_post_install_scripts, setuplogger, containsinstallscripts)


class ProjectPageWidget(Ui_ProjectWidget, QWidget):
    updateproject = pyqtSignal(dict)

    def __init__(self, project, parent=None):
        super(ProjectPageWidget, self).__init__(parent)
        self.setupUi(self)
        self.project = project
        self.projectlabel.setText(project.name)
        self.tokenwidgets = []

        tokens = sort_tokens(get_project_tokens(project.folder))
        self.createtokenwidgets(tokens, self.scrollAreaWidgetContents.layout())

        hasinstallscripts = containsinstallscripts(project.folder)
        self.postinstalllabel.setVisible(hasinstallscripts)

    def createtokenwidgets(self, tokens, layout):
        for token in tokens:
            label = QLabel(token)
            lineedit = QLineEdit()
            lineedit.setObjectName(token)
            self.tokenwidgets.append(lineedit)
            layout.addRow(label, lineedit)

    def save(self):
        tokenvalues = {}
        for widget in self.tokenwidgets:
            token = widget.objectName()
            value = widget.text()
            tokenvalues[token] = value

        self.updateproject.emit(tokenvalues)

    def runinstallscripts(self, _):
        logger.info("Run scripts for {}".format(self.project.name))
        run_post_install_scripts(self.project.folder)


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
            widget.updateproject.connect(self.updateproject)
            self.mOptionsStackedWidget.addWidget(widget)

        self.mOptionsListWidget.adjustSize()

    def updateproject(self, tokenvalues):
        currentproject = self.mOptionsListWidget.currentItem().data(Qt.UserRole)
        if not currentproject:
            return
        logger.info("Updating project {}".format(currentproject.name))
        logger.info(tokenvalues)
        replace_templates_in_folder(currentproject.folder, tokens=tokenvalues)
        run_post_install_scripts(currentproject.folder)

app = QApplication(sys.argv)
app.setApplicationName("Roam Project Installer")

setuplogger()
logger = logging.getLogger("Project Installer")

try:
    projectpath = sys.argv[1]
except IndexError:
    projectpath = os.path.join(os.getcwd(), "projects")

logger.info("Loading projects from {}".format(projectpath))

dialog = ProjectInstallerDialog()
projects = getProjects(projectpath)
dialog.loadprojects(projects)
app.setActiveWindow(dialog)
dialog.show()
sys.exit(app.exec_())

