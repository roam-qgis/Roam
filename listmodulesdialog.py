from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
from ui_listmodules import Ui_ListModules

log = lambda msg: QgsMessageLog.logMessage(msg ,"SDRC")

# create the dialog for zoom to point
class ListProjectsDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_ListModules()
        self.ui.setupUi(self)
        self.ui.moduleList.itemClicked.connect(self.openProject)

    def loadProjectList(self, paths):
        modules = []
        for path in paths:
            for modulepath in os.listdir(path.toString()):
                if modulepath[-3:] == 'qgs':
                    moduleName = os.basename(modulepath)[:-4]
                    item = QListWidgetItem(moduleName, self.ui.moduleList, QListWidgetItem.UserType)
                    item.setData(modulepath)
                    log(modulepath)
                    self.ui.moduleList.addItem( featureitem )
                    
    def openProject(self, item):
        path = item.data(QListWidgetItem.UserType).toString()
        print path
        



