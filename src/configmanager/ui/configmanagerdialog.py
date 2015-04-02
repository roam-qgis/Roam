import os
import shutil
import random
import traceback

from datetime import datetime

from PyQt4.QtGui import QDialog, QFont, QColor, QIcon, QMessageBox, QStandardItem, QStandardItemModel, QInputDialog
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt


from configmanager.ui import ui_configmanager
import configmanager.logger as logger
from roam import resources_rc

import shutil
import roam.project
import roam.messagebaritems

from configmanager.ui.treenodes import *


class ConfigManagerDialog(ui_configmanager.Ui_ProjectInstallerDialog, QDialog):
    def __init__(self, roamapp, parent=None):
        super(ConfigManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.bar = roam.messagebaritems.MessageBar(self)

        # Nope!
        self.projectwidget.roamapp = roamapp
        self.projectwidget.bar = self.bar

        self.treemodel = QStandardItemModel()
        self.projectList.setModel(self.treemodel)
        self.projectList.setHeaderHidden(True)

        self.projectList.selectionModel().currentChanged.connect(self.nodeselected)

        self.projectwidget.adjustSize()
        self.setWindowFlags(Qt.Window)

        self.newProjectButton.pressed.connect(self.newproject)
        self.removeProjectButton.pressed.connect(self.deletebuttonpressed)
        self.projectwidget.projectupdated.connect(self.projectupdated)
        # self.projectwidget.projectsaved.connect(self.projectupdated)
        self.projectwidget.projectloaded.connect(self.updateformsnode)
        self.projectwidget.selectlayersupdated.connect(self.updateformsnode)

        self.projectwidget.setaboutinfo()
        self.projectwidget.projects_page.newproject.connect(self.newproject)
        self.projectwidget.projects_page.projectlocationchanged.connect(self.loadprojects)
        self.setuprootitems()

    def updateformsnode(self, *args):
        pass
        # haslayers = self.projectwidget.checkcapturelayers()
        # index = self.projectList.currentIndex()
        # node = index.data(Qt.UserRole)
        # if node.nodetype == Treenode.FormsNode:
        #     self.newProjectButton.setEnabled(haslayers)

    def raiseerror(self, *exinfo):
        info = traceback.format_exception(*exinfo)
        self.bar.pushError('Seems something has gone wrong. Press for more details',
                                  info)

    def setuprootitems(self):
        rootitem = self.treemodel.invisibleRootItem()
        self.roamnode = RoamNode()
        rootitem.appendRow(self.roamnode)

        self.projectsnode = ProjectsNode(folder=None)
        rootitem.appendRow(self.projectsnode)

    def newproject(self):
        index = self.projectList.currentIndex()
        node = index.data(Qt.UserRole)
        if node and node.canadd:
            try:
                item = node.additem()
            except ValueError:
                return
            newindex = self.treemodel.indexFromItem(item)
            self.projectList.setCurrentIndex(newindex)

    def deletebuttonpressed(self):
        index = self.projectList.currentIndex()
        node = index.data(Qt.UserRole)
        if node.type() == Treenode.ProjectNode:
            self.projectwidget._closeqgisproject()

        title, removemessage = node.removemessage
        delete = node.canremove
        if node.canremove and removemessage:
            button = QMessageBox.warning(self, title, removemessage, QMessageBox.Yes | QMessageBox.No)
            delete = button == QMessageBox.Yes

        if delete:
            parentindex = index.parent()
            newindex = self.treemodel.index(index.row(), 0, parentindex)
            if parentindex.isValid():
                parent = parentindex.data(Qt.UserRole)
                parent.delete(index.row())

            self.projectList.setCurrentIndex(newindex)

    def addprojectfolders(self, folders):
        self.projectwidget.projects_page.setprojectfolders(folders)

    def loadprojects(self, projectpath):
        projects = roam.project.getProjects([projectpath])
        self.projectsnode.loadprojects(projects, projectsbase=projectpath)

        index = self.treemodel.indexFromItem(self.projectsnode)
        self.projectList.setCurrentIndex(index)
        self.projectList.expand(index)

    def nodeselected(self, index, _):
        node = index.data(Qt.UserRole)
        if node is None:
            return

        self.removeProjectButton.setEnabled(node.canremove)
        self.newProjectButton.setEnabled(node.canadd)
        #self.newProjectButton.setText(node.addtext)
        #self.removeProjectButton.setText(node.removetext)

        project = node.project
        if project and not self.projectwidget.project == project:
            # Only load the project if it's different the current one.
            self.projectwidget.setproject(project)
            node.create_children()

            validateresults = list(project.validate())
            if validateresults:
                text = "Here are some reasons we found: \n\n"
                for message in validateresults:
                    text += "- {} \n".format(message)

                self.projectwidget.reasons_label.setText(text)

        if node.nodetype == Treenode.RoamNode:
            self.projectwidget.projectlabel.setText("IntraMaps Roam Config Manager")
        elif node.nodetype == Treenode.MapNode:
            self.projectwidget.loadmap()
        elif node.nodetype == Treenode.FormsNode:
            haslayers = self.projectwidget.checkcapturelayers()
            self.newProjectButton.setEnabled(haslayers)

        self.projectwidget.projectbuttonframe.setVisible(not project is None)
        self.projectwidget.setpage(node.page, node)

    def projectupdated(self):
        index = self.projectList.currentIndex()
        node = find_node(index)
        node.refresh()
