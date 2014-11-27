from PyQt4.QtCore import pyqtSignal, QSize
from PyQt4.QtGui import QListWidgetItem, QPixmap, QWidget

from roam.flickwidget import FlickCharm
from roam.ui.ui_projectwidget import Ui_Form
from roam.ui.ui_listmodules import Ui_ListModules

import zipfile
import os
import re
import roam.utils
import urllib2


class ProjectWidget(Ui_Form, QWidget):
    update_project = pyqtSignal(object)

    def __init__(self, parent, project):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.project = project
        self.updateButton.clicked.connect(self.request_update)
    
    @property
    def name(self):
        return self.namelabel.text()
    
    @name.setter
    def name(self, value):
        self.namelabel.setText(value)
        
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
        self.versionlabel.setText("Version: {}".format(value))
        
    @property
    def image(self):
        return self.imagelabel.pixmap()
    
    @image.setter
    def image(self, value):
        pix = QPixmap(value)
        self.imagelabel.setPixmap(pix)

    def request_update(self):
        self.update_project.emit(self.project)


def update_project(project):
    content = urllib2.urlopen("http://localhost:8000").read()
    folder = os.path.basename(project.folder)
    reg = 'href="(?P<file>{}-(?P<version>\d+(\.\d+)+).zip)"'.format(folder)
    versions = {}
    for match in re.finditer(reg, content, re.I):
        version = match.group("version")
        path = match.group("file")
        versions[version] = path

    maxversion = max(versions)
    path = versions[maxversion]
    content = urllib2.urlopen("http://localhost:8000/{}".format(path)).read()
    rootfolder = os.path.join(project.folder, "..")
    tempfolder = os.path.join(rootfolder, "_updates")
    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    zippath = os.path.join(tempfolder, path)
    with open(zippath, "wb") as f:
        f.write(content)

    with zipfile.ZipFile(zippath, "r") as z:
        z.extractall(rootfolder)

class ProjectsWidget(Ui_ListModules, QWidget):
    requestOpenProject = pyqtSignal(object)

    def __init__(self, parent = None):
        super(ProjectsWidget, self).__init__(parent)
        self.setupUi(self)
        self.flickcharm = FlickCharm()
        self.flickcharm.activateOn(self.moduleList)
        self.moduleList.itemClicked.connect(self.openProject)

    def loadProjectList(self, projects):
        self.moduleList.clear()
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

            self.moduleList.addItem(item)
            self.moduleList.setItemWidget(item, projectwidget)
                              
    def openProject(self, item):
#        self.setDisabled(True)
        project = item.data(QListWidgetItem.UserType)
        self.selectedProject = project
        self.requestOpenProject.emit(project)
        
        

