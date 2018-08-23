import os
import shutil
import random
import traceback

from datetime import datetime

from PyQt4.QtGui import QDialog, QFont, QColor, QIcon, QMessageBox, QStandardItem, QStandardItemModel, QInputDialog, QItemSelectionModel
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt


from configmanager.events import ConfigEvents

from configmanager.ui import ui_configmanager
import configmanager.logger as logger
from roam import resources_rc

import shutil
from qgis.core import QgsMapLayerRegistry, QgsProject
import roam.project
import roam.messagebaritems
import roam.utils

from configmanager.ui.treenodes import *


class ConfigManagerDialog(ui_configmanager.Ui_ProjectInstallerDialog, QDialog):
    def __init__(self, roamapp, parent=None):
        super(ConfigManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.bar = roam.messagebaritems.MessageBar(self)

        self.roamapp = roamapp
        self.reloadingProject = False
        self.loadedProject = None

        # Nope!
        self.projectwidget.roamapp = roamapp
        self.projectwidget.bar = self.bar

        self.treemodel = QStandardItemModel()
        self.projectList.setModel(self.treemodel)
        self.projectList.setHeaderHidden(True)

        self.projectList.selectionModel().currentChanged.connect(self.nodeselected)

        self.projectwidget.adjustSize()
        self.setWindowFlags(Qt.Window)

        self.projectwidget.projectupdated.connect(self.projectupdated)
        self.projectwidget.projectloaded.connect(self.projectLoaded)

        self.projectwidget.setaboutinfo()
        self.projectwidget.projects_page.projectlocationchanged.connect(self.loadprojects)
        self.setuprootitems()

        ConfigEvents.deleteForm.connect(self.delete_form)

        # ## If all the layers are gone we need to reset back to the top state to get the widgets
        # ## back into sync.
        # QgsMapLayerRegistry.instance().removeAll.connect(self.reset_project)

    # def reset_project(self):
    #     print(QgsProject.instance().fileName())
    #     print("ALL REMOVED")
    #     node = self.projectsnode.find_by_filename(QgsProject.instance().fileName())

    def raiseerror(self, *exinfo):
        self.bar.pushError(*exinfo)
        import roam.errors
        roam.errors.send_exception(exinfo)

    def setuprootitems(self):
        rootitem = self.treemodel.invisibleRootItem()
        self.roamnode = RoamNode()
        rootitem.appendRow(self.roamnode)

        self.datanode = DataNode(folder=None)
        rootitem.appendRow(self.datanode)
        self.projectsnode = ProjectsNode(folder=None)
        rootitem.appendRow(self.projectsnode)
        self.publishnode = PublishNode(folder=None)
        rootitem.appendRow(self.publishnode)

        self.pluginsnode = PluginsNode()
        pluginpath = os.path.join(self.roamapp.apppath, "plugins")
        rootitem.appendRow(self.pluginsnode)
        self.pluginsnode.add_plugin_paths([pluginpath])

    def delete_form(self):
        index = self.projectList.currentIndex()
        node = index.data(Qt.UserRole)
        if not node.type() == Treenode.FormNode:
            return

        title, removemessage = node.removemessage
        delete = node.canremove
        if node.canremove and removemessage:
            button = QMessageBox.warning(self, title, removemessage, QMessageBox.Yes | QMessageBox.No)
            delete = button == QMessageBox.Yes

        print "Delete"
        if delete:
            parentindex = index.parent()
            newindex = self.treemodel.index(index.row(), 0, parentindex)
            if parentindex.isValid():
                parent = parentindex.data(Qt.UserRole)
                parent.delete(index.row())

            print parentindex
            self.projectList.setCurrentIndex(parentindex)

    def delete_project(self):
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

    def projectLoaded(self, project):
        roam.utils.info("Project loaded: {}".format(project.name))
        node = self.projectsnode.find_by_name(project.name)
        node.create_children()
        self.projectwidget.setpage(node.page, node, refreshingProject=True)
        self.reloadingProject = False
        self.loadedProject = project
        self.projectList.setExpanded(node.index(), True )

    def nodeselected(self, index, last, reloadProject=False):
        node = index.data(Qt.UserRole)
        if node is None:
            return

        project = node.project

        if project:
            validateresults = list(project.validate())
            if validateresults:
                text = "Here are some reasons we found: \n\n"
                for message in validateresults:
                    text += "- {} \n".format(message)

                self.projectwidget.reasons_label.setText(text)
                return

        if node.nodetype == Treenode.ProjectNode and reloadProject:
            self.reloadingProject = True
            self.projectwidget.setproject(project)
            return

        if project and self.loadedProject != project:
            # Only load the project if it's different the current one.
            roam.utils.info("Swapping to project: {}".format(project.name))
            if self.loadedProject:
                lastnode = self.projectsnode.find_by_name(self.loadedProject.name)
                self.projectList.setExpanded(lastnode.index(), False )
            ## We are closing the open project at this point. Watch for null ref after this.
            self.projectwidget.setproject(project)
            return
        else:
            roam.utils.debug("Setting page")
            self.projectwidget.setpage(node.page, node)

        if node.nodetype == Treenode.RoamNode:
            self.projectwidget.projectlabel.setText("IntraMaps Roam Config Manager")

        if node.nodetype == Treenode.AddNew:
            try:
                item = node.additem()
            except ValueError:
                return
            newindex = self.treemodel.indexFromItem(item)
            self.projectList.setCurrentIndex(newindex)
            return

        self.projectwidget.projectbuttonframe.setVisible(not project is None)


    def projectupdated(self, project):
        # index = self.projectList.currentIndex()
        # node = find_node(index)
        # node.refresh()
        print "PROJECT UPDATED"
        node = self.projectsnode.find_by_name(project.name)
        self.projectList.selectionModel().select(node.index(), QItemSelectionModel.ClearAndSelect)
        self.nodeselected(node.index(), None, reloadProject=True)
