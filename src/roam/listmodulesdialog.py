from PyQt4.QtCore import pyqtSignal, QSize
from PyQt4.QtGui import QListWidgetItem, QPixmap, QWidget

from functools import partial
from roam.flickwidget import FlickCharm
from roam.ui.ui_projectwidget import Ui_Form
from roam.ui.ui_listmodules import Ui_ListModules

import roam.api

import roam.utils


class ProjectWidget(Ui_Form, QWidget):
    def __init__(self, project, parent):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.project = project
        self.closeProjectButton.hide()
        self.closeProjectButton.pressed.connect(roam.api.RoamEvents.close_project)
    
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

    def show_close(self, showclose):
        self.closeProjectButton.setVisible(showclose)


class ProjectsWidget(Ui_ListModules, QWidget):
    requestOpenProject = pyqtSignal(object)

    def __init__(self, parent = None):
        super(ProjectsWidget, self).__init__(parent)
        self.setupUi(self)
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
            
            projectwidget = ProjectWidget(project, self.moduleList)
            projectwidget.image = QPixmap(project.splash)
            projectwidget.name = project.name
            projectwidget.description = project.description
            projectwidget.version = project.version

            self.moduleList.addItem(item)
            self.moduleList.setItemWidget(item, projectwidget)
            self.projectitems[project] = projectwidget

    def openProject(self, item):
#        self.setDisabled(True)
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
