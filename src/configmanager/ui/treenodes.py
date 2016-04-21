import os
import shutil
import random
import traceback

from datetime import datetime

from qgis.core import QgsMapLayerRegistry, QgsMapLayer, QGis

from PyQt4.QtGui import QDialog, QFont, QColor, QIcon, QMessageBox, QStandardItem, QStandardItemModel, QInputDialog
from PyQt4.QtCore import QAbstractItemModel, QModelIndex, Qt

from configmanager.ui import ui_configmanager
import configmanager.logger as logger
from roam import resources_rc

import shutil
import roam.project
import roam.messagebaritems
import roam.api.plugins

templatefolder = os.path.join(os.path.dirname(__file__), "..", "templates")


def newfoldername(basetext, basefolder, formtype, alreadyexists=False):
    message = "Please enter a new folder name for the {}".format(formtype)
    if alreadyexists:
        logger.log("Folder {} already exists.")
        message += "<br> {} folder already exists please select a new one.".format(formtype)

    name, ok = QInputDialog.getText(None, "New {} folder name".format(formtype), message)
    if not ok:
        raise ValueError

    if not name:
        return "{}_{}".format(basetext, datetime.today().strftime('%d%m%y%f'))
    else:
        name = name.replace(" ", "_")

    if os.path.exists(os.path.join(basefolder, name)):
        return newfoldername(basetext, basefolder, formtype, alreadyexists=True)

    return name


def newproject(projectfolder):
    """
    Create a new folder in the projects folder.
    :param projectfolder: The root project folder
    :return: The new project that was created
    """
    foldername = newfoldername("project", projectfolder, "Project")
    templateproject = os.path.join(templatefolder, "templateProject")
    newfolder = os.path.join(projectfolder, foldername)
    shutil.copytree(templateproject, newfolder)
    project = roam.project.Project.from_folder(newfolder)
    project.settings['title'] = foldername
    return project


def newform(project):
    folder = project.folder
    foldername = newfoldername("form", folder, "Form")

    formfolder = os.path.join(folder, foldername)
    templateform = os.path.join(templatefolder, "templateform")
    shutil.copytree(templateform, formfolder)

    config = dict(label=foldername, type='auto', widgets=[])
    form = project.addformconfig(foldername, config)
    logger.debug(form.settings)
    logger.debug(form.settings == config)
    return form


ProjectRole = Qt.UserRole + 20


class Treenode(QStandardItem):
    ProjectNode = QStandardItem.UserType + 0
    FormNode = QStandardItem.UserType + 1
    MapNode = QStandardItem.UserType + 2
    TreeNode = QStandardItem.UserType + 3
    RoamNode = QStandardItem.UserType + 4
    FormsNode = QStandardItem.UserType + 5
    ProjectsNode = QStandardItem.UserType + 6
    ProjectsNode_Invalid = QStandardItem.UserType + 7
    SelectLayerNode = QStandardItem.UserType + 9
    SelectLayersNode = QStandardItem.UserType + 8
    InfoNode = QStandardItem.UserType + 10
    LayerSearchNode = QStandardItem.UserType + 11
    LayerSearchConfigNode = QStandardItem.UserType + 12
    PluginsNode = QStandardItem.UserType + 13
    PluginNode = QStandardItem.UserType + 14
    LayerNode = TreeNode
    AddNew = TreeNode

    nodetype = TreeNode

    def __init__(self, text, icon, project=None):
        super(Treenode, self).__init__(QIcon(icon), text)
        self._text = text
        self.project = project
        self.canadd = False
        self.canremove = False
        self.addtext = ''
        self.removetext = ''
        self.hascount = False

    def data(self, role=None):
        if role == Qt.UserRole:
            return self
        if role == ProjectRole:
            return self.project
        if role == Qt.DisplayRole:
            if self.hascount:
                return "{} ({})".format(self._text, self.rowCount())
            else:
                return self._text

        return super(Treenode, self).data(role)

    def type(self):
        return self.nodetype

    @property
    def page(self):
        return self.type() - QStandardItem.UserType

    def additem(self):
        pass

    def walk(self):
        count = self.rowCount()
        for row in range(count):
            yield self.child(row, 0), row

    def create_children(self):
        for child, row in self.walk():
            child.create_children()

    def refresh(self):
        print "Refreshing child nodes"
        for child, row in self.walk():
            child.refresh()


class SelectLayersNode(Treenode):
    nodetype = Treenode.SelectLayersNode

    def __init__(self, text="Layers", project=None):
        super(SelectLayersNode, self).__init__(text, QIcon(":/icons/map"), project)
        self._text = text
        self.nodes = {}
        self.hascount = True

    def create_children(self):
        self.removeRows(0, self.rowCount())
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue

            if not layer.name() in self.project.selectlayers:
                continue

            node = SelectLayerNode(layer, self.project)
            self.appendRow(node)

        super(SelectLayersNode, self).create_children()

    def refresh(self):
        # TODO Make this smarter and only do what we really need.
        self.create_children()
        super(SelectLayersNode, self).refresh()

class InfoNode(Treenode):
    nodetype = Treenode.InfoNode

    def __init__(self, text, key, layer, project):
        self.key = key
        self.layer = layer
        super(InfoNode, self).__init__(text, QIcon(":/icons/map"), project)


class LayerNode(Treenode):
    nodetype = Treenode.MapNode

    def __init__(self, layer, project):
        self.layer = layer
        text = layer.name()
        super(LayerNode, self).__init__(text, QIcon(":/icons/map"), project)


class SelectLayerNode(Treenode):
    nodetype = Treenode.SelectLayerNode

    def __init__(self, layer, project):
        self.layer = layer
        text = layer.name()
        super(SelectLayerNode, self).__init__(text, QIcon(":/icons/map"), project)

    def create_children(self):
        self.removeRows(0, self.rowCount())
        info1 = InfoNode("Info 1", "info1", self.layer, self.project)
        info2 = InfoNode("Info 2", "info2", self.layer, self.project)
        self.appendRow(info1)
        self.appendRow(info2)


class RoamNode(Treenode):
    nodetype = Treenode.RoamNode

    def __init__(self, text="Roam", project=None):
        super(RoamNode, self).__init__(text, QIcon(":/icons/open"))

    def data(self, role=None):
        if role == Qt.DisplayRole:
            return self._text

        return super(RoamNode, self).data(role)

class LayerSearchNode(Treenode):
    nodetype = Treenode.LayerSearchNode
    def __init__(self, text="Searching", project=None):
        super(LayerSearchNode, self).__init__(text, QIcon(":/icons/search"), project)
        self._text = text

    def data(self, role):
        if role == Qt.DisplayRole:
            return "{} ({})".format(self._text, self.rowCount())
        return super(LayerSearchNode, self).data(role)

    def create_children(self):
        self.removeRows(0, self.rowCount())
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if not layer.type() == QgsMapLayer.VectorLayer:
                continue

            node = LayerSearchConfigNode(layer, self.project)
            self.appendRow(node)

        super(LayerSearchNode, self).create_children()

class LayerSearchConfigNode(Treenode):
    nodetype = Treenode.LayerSearchConfigNode

    def __init__(self, layer, project):
        self.layer = layer
        text = layer.name()
        super(LayerSearchConfigNode, self).__init__(text, QIcon(":/icons/search"), project)

class MapNode(Treenode):
    nodetype = Treenode.MapNode

    def __init__(self, text, project):
        self._text = text
        super(MapNode, self).__init__(text, QIcon(":/icons/map"), project=project)
        self.hascount = True

    def data(self, role):
        if role == Qt.DisplayRole:
            return "{} ({})".format(self._text, self.rowCount())
        return super(MapNode, self).data(role)

    def create_children(self):
        self.removeRows(0, self.rowCount())
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.NoGeometry:
                continue

            node = LayerNode(layer, self.project)
            self.appendRow(node)

        super(MapNode, self).create_children()

    def refresh(self):
        self.create_children()


class AddNewNode(Treenode):
    nodetype = Treenode.AddNew

    def __init__(self, text):
        super(AddNewNode, self).__init__(text, QIcon(":/icons/add"))

    def additem(self):
        return self.parent().additem()


class FormNode(Treenode):
    nodetype = Treenode.FormNode

    def __init__(self, form, project):
        super(FormNode, self).__init__(form.label, QIcon(form.icon), project=project)
        self.form = form
        self.canremove = True
        self.canadd = True
        self.addtext = 'Add new form'
        self.removetext = 'Remove selected form'

        configname = "{}.config".format(form.name)
        self.removemessage = ("Remove form?", ("<b>Do you want to delete this form from the project?</b> <br><br> "
                                               "Deleted forms will be moved to the _archive folder in {}<br><br>"
                                               "<i>Forms can be restored by moving the folder back to the project folder"
                                               " and restoring the content in {} to the settings.config</i>".format(
            self.project.folder, configname)))

    def data(self, role):
        if role == Qt.DisplayRole:
            return self.form.label
        elif role == Qt.DecorationRole:
            return QIcon(self.form.icon)

        return super(FormNode, self).data(role)

    def additem(self):
        return self.parent().additem()


class FormsNode(Treenode):
    nodetype = Treenode.FormsNode

    def __init__(self, text, project):
        super(FormsNode, self).__init__(text, QIcon(":/icons/dataentry"), project)
        self.forms = []
        self.canadd = True
        self._text = text
        self.addtext = 'Add new form'
        self.hascount = True

    def create_children(self):
        forms = self.project.forms
        self.removeRows(0, self.rowCount())
        node = AddNewNode("New Form")
        self.appendRow(node)
        for form in forms:
            item = FormNode(form, self.project)
            self.appendRow(item)
        super(FormsNode, self).create_children()

    def data(self, role):
        if role == Qt.DisplayRole:
            return "{} ({})".format(self._text, self.rowCount() - 1)

        return super(FormsNode, self).data(role)

    def delete(self, index):
        """
        Removes the given form at the index from the project.
        """
        formnode = self.takeRow(index)[0]
        form = formnode.form

        archivefolder = os.path.join(self.project.folder, "_archive")
        formachivefolder = os.path.join(archivefolder, form.name)
        try:
            shutil.move(form.folder, formachivefolder)

            if self.project.oldformconfigstlye:
                configname = "{}.config".format(form.name)
                config = {form.name: form.settings}
                configlocation = os.path.join(archivefolder, configname)
                with open(configlocation, 'w') as f:
                    yaml.dump(data=config, stream=f, default_flow_style=False)

        except Exception as ex:
            logger.exception("Could not remove folder")
            return

        self.project.removeform(form.name)
        self.project.save()

    def additem(self):
        form = newform(self.project)
        self.project.save()
        item = FormNode(form, self.project)
        count = self.rowCount()
        self.insertRow(count - 1, item)
        return item


class ProjectNode(Treenode):
    nodetype = Treenode.ProjectNode

    def __init__(self, project):
        super(ProjectNode, self).__init__(project.name, QIcon(":/icons/folder"))
        self.project = project
        self.removemessage = ("Delete Project?", ("Do you want to delete this project? <br><br> "
                                                  "Deleted projects will be moved to the _archive folder in projects folder<br><br>"
                                                  "<i>Projects can be recovered by moving the folder back to the projects folder</i>"))
        self.canremove = True
        self.canadd = True
        self.removetext = 'Remove selected project'
        self.addtext = 'Add new project'

    def create_children(self):
        self.removeRows(0, self.rowCount())
        if self.project.valid:
            self.searchnode = LayerSearchNode("Searching", project=self.project)
            self.formsnode = FormsNode("Forms", project=self.project)
            self.mapnode = MapNode("Map", project=self.project)
            self.layersnode = SelectLayersNode("Select Layers", project=self.project)
            self.appendRows([self.mapnode, self.layersnode, self.formsnode, self.searchnode])

        super(ProjectNode, self).create_children()

    def additem(self):
        return self.parent().additem()

    @property
    def page(self):
        if not self.project.valid:
            return Treenode.ProjectsNode_Invalid - QStandardItem.UserType
        else:
            return self.type() - QStandardItem.UserType

    def data(self, role=None):
        if role == Qt.DisplayRole:
            return self.project.name
        elif role == Qt.DecorationRole:
            if not self.project.valid:
                return QIcon(":/icons/folder_broken")
        return super(ProjectNode, self).data(role)

class PluginNode(Treenode):
    nodetype = Treenode.PluginNode

    def __init__(self, text, pluginlocation):
        super(PluginNode, self).__init__(text, QIcon(":/icons/plugin"))
        self.canadd = False
        self.pluginlocation = pluginlocation


class PluginsNode(Treenode):
    nodetype = Treenode.PluginsNode

    def __init__(self, text="Installed plugins"):
        super(PluginsNode, self).__init__(text, QIcon(":/icons/plugin"))
        self.canadd = False
        self.hascount = True

    def add_plugin_paths(self, paths):
        for path in paths:
            for plugin in roam.api.plugins.find_plugins([path]):
                pluginlocation = os.path.join(path, plugin)
                node = PluginNode(plugin, pluginlocation)
                self.appendRow(node)


class ProjectsNode(Treenode):
    nodetype = Treenode.ProjectsNode

    def __init__(self, text="Projects", folder=None):
        super(ProjectsNode, self).__init__(text, None)
        self.projectfolder = folder
        self.canadd = True
        self.addtext = 'Add new project'
        self._text = text
        self.hascount = True

    def delete(self, index):
        nodes = self.takeRow(index)
        if not nodes:
            return
        projectnode = nodes[0]
        project = projectnode.project
        try:
            archivefolder = os.path.join(project.basepath, "_archive")
            shutil.move(project.folder, archivefolder)
        except Exception as ex:
            logger.exception("Could not remove form folder")

    def removeRow(self, index):
        return True

    def additem(self):
        project = newproject(self.projectfolder)
        item = ProjectNode(project)
        count = self.rowCount()
        self.insertRow(count - 1, item)
        return item

    def loadprojects(self, projects, projectsbase):
        self.removeRows(0, self.rowCount())
        self.projectfolder = projectsbase
        node = AddNewNode("New Project")
        self.appendRow(node)
        for project in projects:
            node = ProjectNode(project)
            self.appendRow(node)


def find_node(index, nodetype=Treenode.ProjectNode):
    """
    Walk up the nodes until we find the right node type.
    :param node:
    :param nodetype:
    :return:
    """
    parent = index.parent()
    if parent is None:
        return index.data(Qt.UserRole)

    node = parent.data(Qt.UserRole)
    if node is None:
        return index.data(Qt.UserRole)

    if not node.nodetype == nodetype:
        return find_node(parent, nodetype)
    else:
        return node


def walk_tree(node, nodetype):
    """
    Walk the tree looking for a given node type.
    """
    for child in node.walk():
        if not child.nodetype == nodetype:
            return walk_tree(child, nodetype)
        else:
            return child
