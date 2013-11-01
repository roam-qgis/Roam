from PyQt4.QtCore import Qt
from PyQt4.QtGui import QActionGroup
from qgis.core import QgsPalLabeling
from uifiles import mainwindow_widget, mainwindow_base

import sys


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


    def updatePage(self, action):
        page = self.actionpages[action]
        self.stackedWidget.setCurrentIndex(page)
