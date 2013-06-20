from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QWidget, QListWidgetItem, QPixmap, QIcon
from ui_listmodules import Ui_ListModules
from project import QMapProject  

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
            item = QListWidgetItem(project.name, self.ui.moduleList, QListWidgetItem.UserType)
            item.setData(QListWidgetItem.UserType, project)
            pix = QPixmap(project.splash)
            icon = QIcon(pix.scaled(200,200))
            item.setIcon(icon)
            self.ui.moduleList.addItem( item )
                              
    def openProject(self, item):
#        self.setDisabled(True)
        project = item.data(QListWidgetItem.UserType)
        self.selectedProject = project
        self.requestOpenProject.emit(project)
        
        

