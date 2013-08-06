from PyQt4.QtCore import pyqtSignal, QSize
from PyQt4.QtGui import QWidget, QListWidgetItem, QPixmap, QIcon
from ui_listmodules import Ui_ListModules
from project import QMapProject  
from PyQt4 import uic
import os


basepath = os.path.dirname(__file__)
uipath = os.path.join(basepath,'ui_projectwidget.ui')
widgetForm, baseClass= uic.loadUiType(uipath)

class ProjectWidget(widgetForm, baseClass):
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

# create the dialog for zoom to point
class ProjectsWidget(QWidget):
    requestOpenProject = pyqtSignal(QMapProject)
    def __init__(self):
        QWidget.__init__(self )
        self.ui = Ui_ListModules()
        self.ui.setupUi(self)
        self.ui.moduleList.itemClicked.connect(self.openProject)

    def loadProjectList(self, projects):
        self.ui.moduleList.clear()
        for project in projects:
            if not project.vaild:
                continue
            
            item = QListWidgetItem(self.ui.moduleList, QListWidgetItem.UserType)
            item.setData(QListWidgetItem.UserType, project)
            item.setSizeHint(QSize(200, 200))
            
            projectwidget = ProjectWidget(self.ui.moduleList)
            projectwidget.image = QPixmap(project.splash)
            projectwidget.name = project.name
            projectwidget.description = project.description
            projectwidget.version = project.version
            
#             pix = QPixmap(project.splash)
#             icon = QIcon(pix.scaled(200,200))
#             item.setIcon(icon)
            self.ui.moduleList.addItem(item)
            self.ui.moduleList.setItemWidget(item, projectwidget)
                              
    def openProject(self, item):
#        self.setDisabled(True)
        project = item.data(QListWidgetItem.UserType)
        self.selectedProject = project
        self.requestOpenProject.emit(project)
        
        

