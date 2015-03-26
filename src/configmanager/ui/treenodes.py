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

    nodetype = TreeNode

    def __init__(self, text, icon, project=None):
        super(Treenode, self).__init__(QIcon(icon), text)
        self.project = project
        self.canadd = False
        self.canremove = False
        self.addtext = ''
        self.removetext = ''

    def data(self, role=None):
        if role == Qt.UserRole:
            return self
        if role == ProjectRole:
            return self.project

        return super(Treenode, self).data(role)

    def type(self):
        return self.nodetype

    @property
    def page(self):
        return self.type() - QStandardItem.UserType

    def additem(self):
        pass


class RoamNode(Treenode):
    nodetype = Treenode.RoamNode

    def __init__(self, text="Roam", project=None):
        super(RoamNode, self).__init__(text, QIcon(":/icons/open"))


class MapNode(Treenode):
    nodetype = Treenode.MapNode

    def __init__(self, text, project):
        super(MapNode, self).__init__(text, QIcon(":/icons/map"), project=project)


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
        self.loadforms()

    def loadforms(self):
        forms = self.project.forms
        for form in forms:
            item = FormNode(form, self.project)
            self.appendRow(item)

    def data(self, role):
        if role == Qt.DisplayRole:
            return "{} ({})".format(self._text, self.rowCount())

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
                    roam.yaml.dump(data=config, stream=f, default_flow_style=False)

        except Exception as ex:
            logger.exception("Could not remove folder")
            return

        self.project.removeform(form.name)
        self.project.save()

    def additem(self):
        form = newform(self.project)
        self.project.save()
        item = FormNode(form, self.project)
        self.appendRow(item)
        return item


class ProjectNode(Treenode):
    nodetype = Treenode.ProjectNode

    def __init__(self, project):
        super(ProjectNode, self).__init__(project.name, QIcon(":/icons/folder"))
        self.project = project
        if project.valid:
            self.formsnode = FormsNode("Forms", project=project)
            self.mapnode = MapNode("Map", project=project)
            self.appendRows([self.mapnode, self.formsnode])

        self.removemessage = ("Delete Project?", ("Do you want to delete this project? <br><br> "
                                                  "Deleted projects will be moved to the _archive folder in projects folder<br><br>"
                                                  "<i>Projects can be recovered by moving the folder back to the projects folder</i>"))
        self.canremove = True
        self.canadd = True
        self.removetext = 'Remove selected project'
        self.addtext = 'Add new project'

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


class ProjectsNode(Treenode):
    nodetype = Treenode.ProjectsNode

    def __init__(self, text="Projects", folder=None):
        super(ProjectsNode, self).__init__(text, None)
        self.projectfolder = folder
        self.canadd = True
        self.addtext = 'Add new project'
        self._text = text

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
        self.appendRow(item)
        return item

    def data(self, role):
        if role == Qt.DisplayRole:
            return "{} ({})".format(self._text, self.rowCount())
        return super(ProjectsNode, self).data(role)

    def loadprojects(self, projects, projectsbase):
        self.removeRows(0, self.rowCount())
        self.projectfolder = projectsbase
        for project in projects:
            node = ProjectNode(project)
            self.appendRow(node)
