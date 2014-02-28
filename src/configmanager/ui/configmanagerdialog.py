import os
import shutil
import random

from datetime import datetime

from PyQt4.QtGui import QDialog, QFont, QColor, QIcon, QMessageBox
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt

from configmanager.ui import ui_configmanager
import roam.resources_rc

import shutil
import roam.project

class Treenode(object):
    ProjectNode = 0
    FormNode = 1
    MapNode = 2
    TreeNode = 3
    FormsNode = 3
    RoamNode = 4

    nodetype = TreeNode

    def __init__(self, text, icon=None, project=None, parent=None):
        self._text = text
        self.parent = parent
        self.children = []
        self.icon = None
        self.project = project
        self.removemessage = (None, None)
        self.canremove = False

    def appendchild(self, child):
        child.parent = self
        self.children.append(child)

    @property
    def text(self):
        return self._text

    def __getitem__(self, item):
        return self.children[item]

    def __delitem__(self, key):
        passed = self.removerow(key)
        if passed:
            del self.children[key]

    def __len__(self):
        return len(self.children)

    def row(self):
        if self.parent:
            return self.parent.children.index(self)

        return 0

    def removerow(self, index):
        return False

class RoamNode(Treenode):
    nodetype = Treenode.RoamNode

    def __init__(self, text, parent, project=None):
        super(RoamNode, self).__init__(text, parent=parent, project=project)
        self.icon = QIcon(":/icons/open")


class MapNode(Treenode):
    nodetype = Treenode.MapNode

    def __init__(self, text, parent, project):
        super(MapNode, self).__init__(text, parent=parent, project=project)
        self.icon = QIcon(":/icons/map")


class FormNode(Treenode):
    nodetype = Treenode.FormNode

    def __init__(self, form, parent, project):
        super(FormNode, self).__init__(form.label, parent=parent, project=project)
        self.icon = QIcon(form.icon)
        self.form = form
        self.canremove = True

        configname = "{}.config".format(form.name)
        self.removemessage = ("Remove form?", ("<b>Do you want to delete this form from the project?</b> <br><br> "
                                               "Deleted forms will be moved to the _archive folder in {}<br><br>"
                                               "<i>Forms can be restored by moving the folder back to the project folder"
                                               " and restoring the content in {} to the settings.config</i>".format(self.project.folder, configname)))



class FormsNode(Treenode):
    nodetype = Treenode.FormsNode

    def __init__(self, text, parent, project):
        super(FormsNode, self).__init__(text, parent=parent, project=project)
        self.forms = []
        self.icon = QIcon(":/icons/dataentry")

    def addforms(self, forms):
        forms = list(forms)
        for form in forms:
            formnode = FormNode(form, parent=self, project=self.project)
            self.appendchild(formnode)

    @property
    def text(self):
        return "{} ({})".format(self._text, len(self))

    def removerow(self, index):
        """
        Removes the given form at the index from the project.
        """
        formnode = self.children[index]
        form = formnode.form

        archivefolder = os.path.join(self.project.folder, "_archive")
        formachivefolder = os.path.join(archivefolder, form.name)
        configname = "{}.config".format(form.name)
        config = {form.name : form.settings}
        try:
            shutil.move(form.folder, formachivefolder)
            configlocation = os.path.join(archivefolder, configname)

            with open(configlocation, 'w') as f:
                roam.yaml.dump(data=config, stream=f, default_flow_style=False)
            del self.project.settings['forms'][form.name]
            self.project.save()
        except Exception as ex:
            print ex
            return False

        return True

class ProjectNode(Treenode):
    nodetype = Treenode.ProjectNode

    def __init__(self, project, parent=None):
        super(ProjectNode, self).__init__(project.name, parent)
        self.icon = QIcon(":/icons/open")
        self.project = project
        self.formsnode = self.createnode(FormsNode, "Forms")
        self.formsnode.addforms(project.forms)
        self.mapnode = self.createnode(MapNode, "Map")
        self.appendchild(self.formsnode)
        self.appendchild(self.mapnode)
        self.removemessage = ("Delete Project?", ("Do you want to delete this project? <br><br> "
                               "Deleted projects will be moved to the _archive folder in projects folder<br><br>"
                               "<i>Projects can be recovered by moving the folder back to the projects folder</i>"))
        self.canremove = True

    def createnode(self, nodeclass, text):
        node = nodeclass(text, parent=self, project=self.project)
        return node

    @property
    def text(self):
        return self.project.name


class ProjectsNode(Treenode):
    def __init__(self, text, parent=None):
        super(ProjectsNode, self).__init__(text, parent)

    def removerow(self, index):
        projectnode = self[index]
        project = projectnode.project
        print "Delete", project
        try:
            archivefolder = os.path.join(project.basepath, "_archive")
            shutil.move(project.folder, archivefolder)
        except Exception as ex:
            print ex.message
            return False

        return True

class ConfigTreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(ConfigTreeModel, self).__init__(parent)
        self.rootitem = ProjectsNode("Projects")
        self.roamnode = RoamNode("Roam", parent=self.rootitem)
        self.rootitem.appendchild(self.roamnode)

    def columnCount(self, QModelIndex_parent=None, *args, **kwargs):
        return 1

    def headerData(self, p_int, Qt_Orientation, int_role=None):
        return "Projects"

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            node = self.rootitem
        else:
            node = parent.internalPointer()

        try:
            childitem = node[row]
        except IndexError:
            return QModelIndex()

        if childitem is None:
            return QModelIndex()
        else:
            return self.createIndex(row, column, childitem)

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.text
        elif role == Qt.DecorationRole:
            return item.icon
        elif role == Qt.UserRole:
            return item
        else:
            return None

    def parent(self, index=None):
        if not index.isValid():
            return QModelIndex()

        childitem = index.internalPointer()
        parent = childitem.parent

        if parent == self.rootitem:
            return QModelIndex()

        return self.createIndex(parent.row(), 0, parent)

    def rowCount(self, parent=None, *args, **kwargs):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            node = self.rootitem
        else:
            node = parent.internalPointer()

        return len(node)

    def loadprojects(self, projects):
        """
        Bulk load a list of project into the widget.
        :param projects: list of projects to be loaded.
        """
        self.beginInsertRows(QModelIndex(), self.roamnode.row(), len(projects))
        for project in projects:
            node = ProjectNode(project, self.rootitem)
            self.rootitem.appendchild(node)
        self.endInsertRows()

    def addproject(self, project):
        """
        Add a new project to the model.
        :param project:
        :return: The index of the newly added project.
        """
        count = self.rowCount(QModelIndex())
        self.beginInsertRows(QModelIndex(), count, count + 1)
        node = ProjectNode(project, self.rootitem)
        self.rootitem.appendchild(node)
        self.endInsertRows()
        return self.index(count, 0, QModelIndex())

    def getnode(self, index):
        if not index.isValid():
            return self.rootitem

        item = index.internalPointer()
        if item:
            return item

    def removeRow(self, row, parent=None):
        node = self.getnode(parent)
        self.beginRemoveRows(parent, row, row)
        del node[row]
        self.endRemoveRows()

    def nextindex(self, index):
        """
        Return the next index under the given one, or wrap to the top.
        :param index:
        :return:
        """
        newindex = self.index(index.row(), 0, index.parent())
        if not newindex.isValid():
            newindex = self.index(index.row() - 1, 0, index.parent())
        return newindex


class ConfigManagerDialog(ui_configmanager.Ui_ProjectInstallerDialog, QDialog):
    def __init__(self, projectfolder, parent=None):
        super(ConfigManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.projectmodel = ConfigTreeModel()
        self.projectList.setModel(self.projectmodel)

        self.projectList.selectionModel().currentChanged.connect(self.nodeselected)

        self.projectwidget.adjustSize()
        self.setWindowFlags(Qt.Window)
        self.projectfolder = projectfolder

        self.newProjectButton.pressed.connect(self.newproject)
        self.removeProjectButton.pressed.connect(self.deletebuttonpressed)
        self.projectwidget.projectupdated.connect(self.projectupdated)

    def deletebuttonpressed(self):
        index = self.projectList.currentIndex()
        node = index.data(Qt.UserRole)
        if node.nodetype == Treenode.ProjectNode:
            self.projectwidget._closeqgisproject()

        title, removemessage = node.removemessage
        delete = node.canremove
        if node.canremove and removemessage:
            button = QMessageBox.warning(self, title, removemessage, QMessageBox.Yes | QMessageBox.No)
            delete = button == QMessageBox.Yes

        if delete:
            self.projectmodel.removeRow(index.row(), index.parent())
            newindex = self.projectmodel.nextindex(index)
            self.projectList.setCurrentIndex(newindex)

    def newproject(self):
        templateProject = os.path.join(os.path.dirname(__file__), "..", "templates/templateProject")
        newfolder = os.path.join(self.projectfolder, "newProject{}".format(datetime.today().strftime('%d%m%y%f')))
        shutil.copytree(templateProject, newfolder)
        project = roam.project.Project.from_folder(newfolder)
        project.settings['forms'] = {}
        newindex = self.projectmodel.addproject(project)
        self.projectList.setCurrentIndex(newindex)

    def loadprojects(self, projects):
        self.projectmodel.loadprojects(projects)
        index = self.projectmodel.index(0, 0, QModelIndex())
        self.projectList.setCurrentIndex(index)
        self.projectwidget.setprojectsfolder(self.projectfolder)

    def nodeselected(self, index, _):
        node = index.data(Qt.UserRole)
        if node is None:
            return

        self.projectwidget.setpage(node.nodetype)
        project = node.project
        if project and not self.projectwidget.project == project:
            # Only load the project if it's different the current one.
            self.projectwidget.setproject(project)

        if node.nodetype == Treenode.FormNode:
            self.projectwidget.setform(node.form)
        elif node.nodetype == Treenode.RoamNode:
            self.projectwidget.projectlabel.setText("IntraMaps Roam Config Manager")

        self.projectwidget.projectbuttonframe.setVisible(not project is None)

    def projectupdated(self):
        index = self.projectList.currentIndex()
        self.projectmodel.dataChanged.emit(index, index)
