from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt4.QtCore import pyqtSignal, QSize, QUrl, Qt
from PyQt4.QtGui import QListWidgetItem, QPixmap, QWidget, QBrush, QColor

from functools import partial
from roam.flickwidget import FlickCharm
from roam.ui.ui_projectwidget import Ui_Form
from roam.ui.ui_listmodules import Ui_ListModules

import os
import roam.api
import roam.project
import roam.utils
import roam.updater


class ProjectWidget(Ui_Form, QWidget):
    update_project = pyqtSignal(dict)
    install_project = pyqtSignal(dict)

    def __init__(self, parent, project, is_new=False):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self._serverversion = None
        self.project = project
        self.serverinfo = {}
        self.is_new = is_new
        if self.is_new:
            self.updateButton.setText("Install project")

        self.updateButton.clicked.connect(self.request_update)
        self.closeProjectButton.hide()
        self.closeProjectButton.pressed.connect(roam.api.RoamEvents.close_project)
        self.refresh()

    def refresh(self):
        if self.is_new:
            name = self.project['title']
            desc = self.project['description']
            splash = ":icons/download"
            self.namelabel.setText(name)
            self.descriptionlabel.setText(desc)
        else:
            name = self.project.name
            desc = self.project.description
            splash = self.project.splash
            self.namelabel.setText(name)
            self.descriptionlabel.setText(desc)
            if not self.project.valid:
                self.namelabel.setText(name + " (Invalid)")
                self.descriptionlabel.setText(self.project.error)

        pix = QPixmap(splash)
        self.imagelabel.setPixmap(pix)
        self.update_version_status()

    def update_status(self, status):
        if status.lower() in ["complete", 'installed']:
            self.serverversion = None
            self.setEnabled(True)
            self.refresh()
        else:
            self.setEnabled(False)
            if self.is_new:
                name = self.project['title']
            else:
                name = self.project.name

            self.namelabel.setText("({}..) {}".format(status, name))
            self.updateButton.setText(status)

    @property
    def serverversion(self):
        return self._serverversion

    @serverversion.setter
    def serverversion(self, value):
        self._serverversion = value
        self.update_version_status()

    def update_version_status(self):
        if self.is_new:
            self.updateButton.show()
            self.versionlabel.setText("Version: {}".format(self.project['version']))
            return

        if self.serverversion is None:
            self.versionlabel.setText("Version: {}".format(self.project.version))
            self.updateButton.hide()
        else:
            self.versionlabel.setText("Version: {} -> {}".format(self.project.version, self.serverversion))
            self.updateButton.show()

    def show_close(self, showclose):
        self.closeProjectButton.setVisible(showclose)

    def request_update(self):
        if self.is_new:
            self.install_project.emit(self.serverinfo)
        else:
            self.update_project.emit(self.serverinfo)


class ProjectsWidget(Ui_ListModules, QWidget):
    requestOpenProject = pyqtSignal(object)
    projectUpdate = pyqtSignal(object)
    search_for_updates = pyqtSignal()
    projectInstall = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ProjectsWidget, self).__init__(parent)
        self.setupUi(self)
        self.serverurl = None
        self.flickcharm = FlickCharm()
        self.flickcharm.activateOn(self.moduleList)
        self.moduleList.itemClicked.connect(self.openProject)
        self.projectitems = {}
        self.project_base = None
        self.progressFrame.hide()

    def showEvent(self, event):
        self.search_for_updates.emit()

    def loadProjectList(self, projects):
        self.moduleList.clear()
        self.projectitems.clear()
        for project in projects:
            if not project.valid:
                roam.utils.warning("Project {0} is invalid because {1}".format(project.name, project.error))

            self.add_new_item(project.id, project, is_new=False, is_valid=project.valid)

    def show_new_updateable(self, updateprojects, newprojects):
        print(updateprojects, newprojects)
        for info in updateprojects:
            projectid = info['projectid']
            item = self.projectitems[projectid]
            widget = self.item_widget(item)
            widget.serverversion = info['version']
            widget.serverinfo = info

        for info in newprojects:
            projectid = info['projectid']
            if info['name'] in self.projectitems:
                self.update_item(projectid, info)
            else:
                self.add_new_item(projectid, info, is_new=True)

    def update_item(self, projectid, info):
        item = self.projectitems[projectid]
        item.setData(QListWidgetItem.UserType, info)
        widget = self.moduleList.itemWidget(item)
        widget.project = info
        widget.serverinfo = info

    def add_new_item(self, projectid, project, is_new=False, is_valid=True):
        item = QListWidgetItem(self.moduleList, QListWidgetItem.UserType)
        item.setData(QListWidgetItem.UserType, project)
        item.setSizeHint(QSize(150, 150))
        if not is_valid:
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        projectwidget = ProjectWidget(self.moduleList, project, is_new=is_new)
        projectwidget.install_project.connect(self.projectInstall.emit)
        projectwidget.update_project.connect(self.projectUpdate.emit)
        projectwidget.setEnabled(is_valid)
        projectwidget.serverinfo = project

        self.moduleList.addItem(item)
        self.moduleList.setItemWidget(item, projectwidget)

        self.projectitems[projectid] = item

    def item_widget(self, item):
        return self.moduleList.itemWidget(item)

    def openProject(self, item):
        # self.setDisabled(True)
        project = self.item_widget(item).project
        if isinstance(project, dict):
            return

        if not project.valid:
            return

        self.selectedProject = project
        self.requestOpenProject.emit(project)
        self.set_open_project(project)

    def set_open_project(self, currentproject):
        for projectid, item in self.projectitems.iteritems():
            widget = self.item_widget(item)
            if widget.is_new:
                continue

            project = widget.project
            if currentproject is None:
                widget.show_close(False)
            else:
                widget.show_close(currentproject.id == project.id)

    def project_installed(self, projectname):
        project = roam.project.Project.from_folder(os.path.join(self.project_base, projectname))
        item = self.projectitems[project.basefolder]
        widget = self.item_widget(item)
        widget.project = project
        widget.is_new = False
        widget.update_status("installed")

    def update_project_status(self, projectname, status):
        if status.lower() in ["complete", 'installed']:
            self.progressFrame.hide()
        else:
            self.progressFrame.show()
            self.statusLabel.setText("{}: {}".format(projectname, status))

        try:
            item = self.projectitems[projectname]
            widget = self.item_widget(item)
            widget.update_status(status)
        except KeyError:
            pass
