import sys
import os
import copy
import subprocess
import shutil
import functools

from datetime import datetime

from PyQt4.QtCore import Qt, QDir, QFileInfo, pyqtSignal, QModelIndex, QFileSystemWatcher, QUrl
from PyQt4.QtGui import (QWidget, QStandardItemModel, QStandardItem, QIcon, QMessageBox, QPixmap, QDesktopServices, QMenu,
                         QToolButton, QFileDialog)

from qgis.core import QgsProject, QgsMapLayerRegistry, QgsPalLabeling, QGis, QgsProjectBadLayerHandler
from qgis.gui import QgsMapCanvas, QgsExpressionBuilderDialog, QgsMessageBar

from configmanager.ui.ui_projectwidget import Ui_Form
from configmanager.models import widgeticon, WidgetItem, WidgetsModel, QgsLayerModel, QgsFieldModel, LayerTypeFilter, \
    CaptureLayerFilter, CaptureLayersModel
from configmanager.utils import openqgis, openfolder

from roam.api import FeatureForm
from roam import bundle

import configmanager.editorwidgets
import roam.editorwidgets
import roam.projectparser
import yaml
import roam
import roam.project
import roam.config
import configmanager.logger as logger


def layer(name):
    """
    Return a layer with the given name in the QGIS session
    :param name: The name of the layer to return.
    :return: A QgsMapLayer object with the given name.
    """
    return QgsMapLayerRegistry.instance.mapLayersByName(name)[0]


class BadLayerHandler(QgsProjectBadLayerHandler):
    """
    Handler class for any layers that fail to load when
    opening the project.
    """

    def __init__(self, callback):
        """
            callback - Any bad layers are passed to the callback so it
            can do what it wills with them
        """
        super(BadLayerHandler, self).__init__()
        self.callback = callback

    def handleBadLayers(self, domNodes, domDocument):
        layers = [node.namedItem("layername").toElement().text() for node in domNodes]
        self.callback(layers)


class ProjectWidget(Ui_Form, QWidget):
    SampleWidgetRole = Qt.UserRole + 1
    projectsaved = pyqtSignal()
    projectupdated = pyqtSignal()
    projectloaded = pyqtSignal(object)
    selectlayersupdated = pyqtSignal(list)

    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.project = None
        self.bar = None
        self.roamapp = None

        menu = QMenu()

        # self.roamVersionLabel.setText("You are running IntraMaps Roam version {}".format(roam.__version__))

        self.openProjectFolderButton.pressed.connect(self.openprojectfolder)
        self.openinQGISButton.pressed.connect(self.openinqgis)
        self.depolyProjectButton.pressed.connect(self.deploy_project)
        self.depolyInstallProjectButton.pressed.connect(functools.partial(self.deploy_project, True))

        self.filewatcher = QFileSystemWatcher()
        self.filewatcher.fileChanged.connect(self.qgisprojectupdated)

        self.projectupdatedlabel.linkActivated.connect(self.reloadproject)
        self.projectupdatedlabel.hide()

        # self.setpage(4)
        self.currentnode = None
        self.form = None

        qgislocation = r'C:\OSGeo4W\bin\qgis.bat'
        qgislocation = roam.config.settings.setdefault('configmanager', {}) \
            .setdefault('qgislocation', qgislocation)

        self.qgispathEdit.setText(qgislocation)
        self.qgispathEdit.textChanged.connect(self.save_qgis_path) 
        self.filePickerButton.pressed.connect(self.set_qgis_path)

        self.connect_page_events()

    def connect_page_events(self):
        """
        Connect the events from all the pages back to here
        """
        for index in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if hasattr(widget, "raiseMessage"):
                widget.raiseMessage.connect(self.bar.pushMessage)

    def set_qgis_path(self):
        """
        Set the location of the QGIS install.  We need the path to be able to create Roam
        projects
        """
        path = QFileDialog.getOpenFileName(self, "Select QGIS install file", filter="(*.bat)")
        if not path:
            return
        self.qgispathEdit.setText(path)
        self.save_qgis_path(path)

    def save_qgis_path(self, path):
        """
        Save the QGIS path back to the Roam config.
        """
        roam.config.settings['configmanager'] = {'qgislocation': path}
        roam.config.save()

    def setpage(self, page, node):
        """
        Set the current page in the config manager.  We pass the project into the current
        page so that it knows what the project is.
        """
        self.currentnode = node

        self.write_config_currentwidget()

        self.stackedWidget.setCurrentIndex(page)

        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, "set_project"):
            widget.set_project(self.project, self.currentnode)

    def write_config_currentwidget(self):
        """
        Call the write config command on the current widget.
        """
        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, "write_config"):
            widget.write_config()

    def deploy_project(self, with_data=False):
        """
        Run the step to deploy a project. Projects are deplyed as a bundled zip of the project folder.
        """
        if self.roamapp.sourcerun:
            base = os.path.join(self.roamapp.apppath, "..")
        else:
            base = self.roamapp.apppath

        default = os.path.join(base, "roam_serv")
        path = roam.config.settings.get("publish", {}).get("path", '')
        if not path:
            path = default

        path = os.path.join(path, "projects")

        if not os.path.exists(path):
            os.makedirs(path)

        self._saveproject()
        options = {}

        bundle.bundle_project(self.project, path, options, as_install=with_data)

    def setaboutinfo(self):
        """
        Set the current about info on the widget
        """
        self.versionLabel.setText(roam.__version__)
        self.qgisapiLabel.setText(unicode(QGis.QGIS_VERSION))

    def selectlayerschanged(self, *args):
        """
        Run the updates when the selection layers have changed
        """
        self.formlayers.setSelectLayers(self.project.selectlayers)
        self.selectlayersupdated.emit(self.project.selectlayers)

    def reloadproject(self, *args):
        """
        Reload the project. At the moment this will drop any unsaved changes to the config.
        Note: Should look at making sure it doesn't do that because it's not really needed.
        """
        self.setproject(self.project)
        self.projectupdated.emit()

    def qgisprojectupdated(self, path):
        """
        Show a message when the QGIS project file has been updated.
        """
        self.projectupdatedlabel.show()
        self.projectupdatedlabel.setText("The QGIS project has been updated. <a href='reload'> "
                                         "Click to reload</a>. <b style=\"color:red\">Unsaved data will be lost</b>")

    def openinqgis(self):
        """
        Open a QGIS session for the user to config the project layers.
        """
        try:
            openqgis(self.project.projectfile)
        except OSError:
            self.bar.pushMessage("Looks like I couldn't find QGIS",
                                 "Check qgislocation in roam.config", QgsMessageBar.WARNING)

    def openprojectfolder(self):
        """
        Open the project folder in the file manager for the OS.
        """
        folder = self.project.folder
        openfolder(folder)

    def setproject(self, project, loadqgis=True):
        """
        Set the widgets active project.
        """
        self.filewatcher.removePaths(self.filewatcher.files())
        self.projectupdatedlabel.hide()
        self._closeqgisproject()

        if project.valid:
            self.startsettings = copy.deepcopy(project.settings)
            self.project = project
            self.projectlabel.setText(project.name)
            self.loadqgisproject(project, self.project.projectfile)
            self.filewatcher.addPath(self.project.projectfile)
            self.projectloaded.emit(self.project)

    def loadqgisproject(self, project, projectfile):
        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        # No idea why we have to set this each time.  Maybe QGIS deletes it for
        # some reason.
        self.badLayerHandler = BadLayerHandler(callback=self.missing_layers)
        QgsProject.instance().setBadLayerHandler(self.badLayerHandler)
        QgsProject.instance().read(fileinfo)

    def missing_layers(self, missinglayers):
        """
        Handle any and show any missing layers.
        """
        self.project.missing_layers = missinglayers

    def _closeqgisproject(self):
        """
        Close the current QGIS project and clean up after..
        """
        QgsMapLayerRegistry.instance().removeAllMapLayers()

    def _saveproject(self):
        """
        Save the project config to disk.
        """
        self.write_config_currentwidget()
        # self.project.dump_settings()
        self.project.save(update_version=True)
        self.filewatcher.removePaths(self.filewatcher.files())
        QgsProject.instance().write()
        self.filewatcher.addPath(self.project.projectfile)
        self.projectsaved.emit()
