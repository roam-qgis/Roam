from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt4.QtCore import pyqtSignal, QSize, QUrl
from PyQt4.QtGui import QListWidgetItem, QPixmap, QWidget

from functools import partial
from roam.flickwidget import FlickCharm
from roam.ui.ui_projectwidget import Ui_Form
from roam.ui.ui_listmodules import Ui_ListModules

import zipfile
import os
import re
import roam.api

import roam.utils
import urllib2
from collections import defaultdict


class ProjectWidget(Ui_Form, QWidget):
    update_project = pyqtSignal(object, object)

    def __init__(self, parent, project):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self._serverversion = None
        self.project = project
        self.updateButton.clicked.connect(self.request_update)
        self.closeProjectButton.hide()
        self.closeProjectButton.pressed.connect(roam.api.RoamEvents.close_project)

    @property
    def name(self):
        return self.namelabel.text()

    @name.setter
    def name(self, value):
        self.namelabel.setText(value)

    @property
    def serverversion(self):
        return self._serverversion

    @serverversion.setter
    def serverversion(self, value):
        self._serverversion = value
        self.update_version_label()

    def update_version_label(self):
        if self.version == self.serverversion or self.serverversion is None:
            self.versionlabel.setText("Version: {}".format(self.version))
        else:
            self.versionlabel.setText("Version: {} -> {}".format(self.version, self.serverversion))

    @property
    def description(self):
        return self.descriptionlabel.text()

    @description.setter
    def description(self, value):
        self.descriptionlabel.setText(value)

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value
        self.update_version_label()

    @property
    def image(self):
        return self.imagelabel.pixmap()

    @image.setter
    def image(self, value):
        pix = QPixmap(value)
        self.imagelabel.setPixmap(pix)

    def show_close(self, showclose):
        self.closeProjectButton.setVisible(showclose)

    def request_update(self):
        self.update_project.emit(self.project, self.serverversion)


def checkversion(toversion, fromversion):
    def versiontuple(v):
        v = v.split('.')[:3]
        version = tuple(map(int, (v)))
        if len(version) == 2:
            version = (version[0], version[1], 0)
        return version

    return versiontuple(toversion) > versiontuple(fromversion)


def parse_serverprojects(content):
    reg = 'href="(?P<file>(?P<name>\w+)-(?P<version>\d+(\.\d+)+).zip)"'
    versions = defaultdict(dict)
    for match in re.finditer(reg, content, re.I):
        version = match.group("version")
        path = match.group("file")
        data = dict(path=path)
        versions[match.group("name")][version] = data
    return dict(versions)


def update_project(project, version):
    print "Updating project {}".format(project.name)

    filename = "{}-{}.zip".format(project.basefolder, version)
    content = urllib2.urlopen("http://localhost:8000/{}".format(filename)).read()
    rootfolder = os.path.join(project.folder, "..")
    tempfolder = os.path.join(rootfolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    zippath = os.path.join(tempfolder, filename)
    with open(zippath, "wb") as f:
        f.write(content)

    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(rootfolder)

    print "Project updated"


def get_project_info(projectname, projects):
    maxversion = max(projects[projectname])
    projectdata = projects[projectname][maxversion]
    path = projectdata['path']
    return path, maxversion, projects[projectname]


def can_update(projectname, currentversion, projects):
    try:
        maxversion = max(projects[projectname])
        return checkversion(maxversion, currentversion)
    except KeyError:
        return False
    except ValueError:
        return False


class ProjectsWidget(Ui_ListModules, QWidget):
    requestOpenProject = pyqtSignal(object)

    def __init__(self, parent=None):
        super(ProjectsWidget, self).__init__(parent)
        self.setupUi(self)
        self.flickcharm = FlickCharm()
        self.flickcharm.activateOn(self.moduleList)
        self.moduleList.itemClicked.connect(self.openProject)
        self.net = QNetworkAccessManager()
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
            projectwidget.image = QPixmap(project.splash)
            projectwidget.name = project.name
            projectwidget.description = project.description
            projectwidget.version = project.version
            projectwidget.update_project.connect(update_project)
            self.projectitems[project] = projectwidget

            self.moduleList.addItem(item)
            self.moduleList.setItemWidget(item, projectwidget)

        self.check_for_new_projects()

    def check_for_new_projects(self):
        req = QNetworkRequest(QUrl("http://localhost:8000"))
        reply = self.net.get(req)
        import functools

        reply.finished.connect(functools.partial(self.list_versions, reply))

    def list_versions(self, reply):
        content = reply.readAll().data()
        serverversions = parse_serverprojects(content)
        for project, widget in self.projectitems.iteritems():
            canupdate = can_update(project.basefolder, project.version, serverversions)
            if canupdate:
                path, version, projectdata = get_project_info(project.basefolder, serverversions)
                widget.serverversion = version

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
