from PyQt4.QtCore import Qt
from PyQt4.QtGui import QActionGroup, QWidget, QSizePolicy, QLabel
from qgis.core import QgsPalLabeling

import sys
import os

from qmap.uifiles import mainwindow_widget, mainwindow_base
from qmap.listmodulesdialog import ProjectsWidget
import qmap.utils

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

        def createSpacer(width):
            widget = QWidget()
            widget.setMinimumWidth(width)
            return widget

        spacewidget = createSpacer(60)
        gpsspacewidget = createSpacer(30)
        sidespacewidget = createSpacer(30)
        sidespacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gpsspacewidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.projecttoolbar.insertWidget(self.actionSync, gpsspacewidget)
        self.projecttoolbar.insertWidget(self.actionHome, spacewidget)

        self.projectlabel = self._createSideLabel("Project: <br> {project}")
        self.userlabel = self._createSideLabel("User: <br> {user}")

        labelaction = self.menutoolbar.insertWidget(self.actionSettings, self.userlabel)

        self.menutoolbar.insertWidget(labelaction, sidespacewidget)
        self.menutoolbar.insertWidget(labelaction, self.projectlabel)

    def _createSideLabel(self, text):
        style = """
            QLabel {
                    color: #8c8c8c;
                    font: 10px "Calibri" ;
                    }"""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(style)

        return label

    def loadProjectList(self, projects):
        self.projectwidget.loadProjectList(projects)

    def updatePage(self, action):
        page = self.actionpages[action]
        self.stackedWidget.setCurrentIndex(page)

    def show(self):
        fullscreen = qmap.utils.settings.get("fullscreen", False)
        if fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()











