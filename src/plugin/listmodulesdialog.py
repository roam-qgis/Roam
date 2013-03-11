from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
import glob
from ui_listmodules import Ui_ListModules
from utils import log
import qmap

from collections import namedtuple

Project = namedtuple('Project', 'name file splash folder')
 

def getProjects(projectpath):
    folders = (sorted( [os.path.join(projectpath, item) 
                       for item in os.walk(projectpath).next()[1]]))
    
    for folder in folders:
        # The folder name is the display name
        # Grab the first project file
        # Look for splash.png
        # Path to project folder.
        name = os.path.basename(folder)
        try:
            projectfile = glob.glob(os.path.join(folder, '*.qgs'))[0]
        except IndexError:
            log("No project file found.")
            continue
        try:
            splash = glob.glob(os.path.join(folder, 'splash.png'))[0]
        except IndexError:
            splash = ''
        
        yield Project(name, projectfile, splash, folder )
    

# create the dialog for zoom to point
class ListProjectsDialog(QDialog):
    requestOpenProject = pyqtSignal(Project)
    def __init__(self):
        QDialog.__init__(self )
        self.ui = Ui_ListModules()
        self.ui.setupUi(self)
        self.ui.moduleList.itemClicked.connect(self.openProject)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ui.pushButton.clicked.connect(self.reject)
        scr = QApplication.desktop().screenGeometry(0)
        self.move( scr.center() - self.rect().center() )

    def loadProjectList(self, path):
        for project in getProjects(path):
            item = QListWidgetItem(project.name, self.ui.moduleList, QListWidgetItem.UserType)
            item.setData(QListWidgetItem.UserType, project)
            pix = QPixmap(project.splash)
            icon = QIcon(pix.scaled(200,200))
            item.setIcon(icon)
            self.ui.moduleList.addItem( item )
                              
    def openProject(self, item):
        self.setDisabled(True)
        project = item.data(QListWidgetItem.UserType).toPyObject()
        self.requestOpenProject.emit(project)
        



