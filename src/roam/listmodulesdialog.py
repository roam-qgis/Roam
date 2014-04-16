from PyQt4.QtCore import pyqtSignal, QSize
from PyQt4.QtGui import QListWidgetItem, QPixmap

from roam.flickwidget import FlickCharm
from roam.ui.uifiles import (project_widget, project_base,
                         modules_widget, modules_base)


class ProjectWidget(project_widget, project_base):
    def __init__(self, parent):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
    
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


class ProjectsWidget(modules_widget, modules_base):
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
                continue
            
            item = QListWidgetItem(self.moduleList, QListWidgetItem.UserType)
            item.setData(QListWidgetItem.UserType, project)
            item.setSizeHint(QSize(150, 150))
            
            projectwidget = ProjectWidget(self.moduleList)
            projectwidget.image = QPixmap(project.splash)
            projectwidget.name = project.name
            projectwidget.description = project.description
            projectwidget.version = project.version
            
            self.moduleList.addItem(item)
            self.moduleList.setItemWidget(item, projectwidget)
                              
    def openProject(self, item):
#        self.setDisabled(True)
        project = item.data(QListWidgetItem.UserType)
        self.selectedProject = project
        self.requestOpenProject.emit(project)
        
        

