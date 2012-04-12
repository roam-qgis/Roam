from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import os
from ui_listmodules import Ui_ListModules
import glob

log = lambda msg: QgsMessageLog.logMessage(msg ,"SDRC")

# create the dialog for zoom to point
class ListProjectsDialog(QDialog):
    requestOpenProject = pyqtSignal(str)
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_ListModules()
        self.ui.setupUi(self)
        self.ui.moduleList.itemClicked.connect(self.openProject)
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = QApplication.desktop().screenGeometry(0)
        self.move( scr.center() - self.rect().center() )

    def loadProjectList(self, paths):
        log(paths[0])
        modules = []
        for path in paths:
            for modulepath in glob.glob(os.path.join(path, '*.qgs')):
                moduleName = os.path.basename(modulepath)[:-4]
                item = QListWidgetItem(moduleName, self.ui.moduleList, QListWidgetItem.UserType)
                item.setData(QListWidgetItem.UserType, modulepath)
                print modulepath
                self.ui.moduleList.addItem( item )
                    
    def openProject(self, item):
        path = item.data(QListWidgetItem.UserType).toString()
        self.requestOpenProject.emit(path)
        



