from PyQt4.QtCore import Qt
from PyQt4.QtGui import QActionGroup
from qgis.core import QgsPalLabeling

import sys
import os

from uifiles import mainwindow_widget, mainwindow_base
from listmodulesdialog import ProjectsWidget


class MainWindow(mainwindow_widget, mainwindow_base):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        pal = QgsPalLabeling()
        self.canvas.mapRenderer().setLabelingEngine(pal)
        self.menuGroup = QActionGroup(self)
        self.menuGroup.setExclusive(True)

        self.menuGroup.addAction(self.actionMap)
        self.menuGroup.addAction(self.actionProject)
        self.menuGroup.addAction(self.actionSettings)
        self.actionpages = {self.actionMap: 0,
                            self.actionProject: 1,
                            self.actionSettings: 2}

        self.menuGroup.triggered.connect(self.updatePage)

        self.projectwidget = ProjectsWidget(self)
        self.project_page.layout().addWidget(self.projectwidget)

    def loadProjectList(self, projects):
        self.projectwidget.loadProjectList(projects)

    def updatePage(self, action):
        page = self.actionpages[action]
        self.stackedWidget.setCurrentIndex(page)
