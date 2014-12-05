from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt4.QtCore import pyqtSignal, QSize, QUrl
from PyQt4.QtGui import QListWidgetItem, QPixmap, QWidget

from functools import partial
from roam.flickwidget import FlickCharm
from roam.ui.ui_projectwidget import Ui_Form
from roam.ui.ui_listmodules import Ui_ListModules

import os
import roam.api

import roam.utils
import roam.updater


class ProjectWidget(Ui_Form, QWidget):
    update_project = pyqtSignal(object, object)

    def __init__(self, parent, project):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self._serverversion = None
        self.project = project
        self.project.projectUpdated.connect(self.project_updated)
        self.updateButton.clicked.connect(self.request_update)
        self.closeProjectButton.hide()
        self.closeProjectButton.pressed.connect(roam.api.RoamEvents.close_project)
        self.refresh()

    def refresh(self):
        self.namelabel.setText(self.project.name)
        self.descriptionlabel.setText(self.project.description)
        pix = QPixmap(self.project.splash)
        self.imagelabel.setPixmap(pix)
        self.update_version_status()

    def project_updated(self, project):
        self.serverversion = None
        self.refresh()
        print "Project updated"

    @property
    def serverversion(self):
        return self._serverversion

    @serverversion.setter
    def serverversion(self, value):
        self._serverversion = value
        self.update_version_status()

    def update_version_status(self):
        if self.serverversion is None:
            self.versionlabel.setText("Version: {}".format(self.project.version))
            self.updateButton.hide()
        else:
            self.versionlabel.setText("Version: {} -> {}".format(self.project.version, self.serverversion))
            self.updateButton.show()

    def show_close(self, showclose):
        self.closeProjectButton.setVisible(showclose)

    def request_update(self):
        self.update_project.emit(self.project, self.serverversion)


class ProjectsWidget(Ui_ListModules, QWidget):
    requestOpenProject = pyqtSignal(object)
    projectUpdate = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(ProjectsWidget, self).__init__(parent)
        self.setupUi(self)
        self.serverurl = None
        self.flickcharm = FlickCharm()
        self.flickcharm.activateOn(self.moduleList)
        self.moduleList.itemClicked.connect(self.openProject)
        self.projectitems = {}

    def loadProjectList(self, projects):
        self.moduleList.clear()
        self.projectitems.clear()
        for project in projects:
            if not project.valid:
                roam.utils.warning("Project {} is invalid because {}".format(project.name, project.error))
                continue

            item = QListWidgetItem(self.moduleList, QListWidgetItem.UserType)
            item.setData(QListWidgetItem.UserType, project)
            item.setSizeHint(QSize(150, 150))

            projectwidget = ProjectWidget(self.moduleList, project)
            projectwidget.update_project.connect(self.update_project)
            self.projectitems[project] = projectwidget

            self.moduleList.addItem(item)
            self.moduleList.setItemWidget(item, projectwidget)

    def show_updateable(self, projects):
        for project, info in projects:
            widget = self.projectitems[project]
            widget.serverversion = info['version']

    def openProject(self, item):
        # self.setDisabled(True)
        project = item.data(QListWidgetItem.UserType)
        self.selectedProject = project
        self.requestOpenProject.emit(project)
        self.set_open_project(project)

    def set_open_project(self, currentproject):
        for project, widget in self.projectitems.iteritems():
            if currentproject:
                showclose = currentproject == project
            else:
                showclose = False
            widget.show_close(showclose)

    def update_project(self, project, version):
        self.projectUpdate.emit(project, version)
