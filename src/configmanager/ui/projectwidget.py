import os
import copy

from PyQt5.QtCore import Qt, QDir, QFileInfo, pyqtSignal, QFileSystemWatcher
from PyQt5.QtWidgets import QWidget, QMessageBox, QMenu, QFileDialog

from qgis.core import QgsProject, QgsMapLayerRegistry, Qgis, QgsProjectBadLayerHandler
from qgis.gui import QgsMessageBar

from configmanager.ui.ui_projectwidget import Ui_Form
from configmanager.utils import openqgis, openfolder

from configmanager import bundle

import roam.editorwidgets
import roam.projectparser
import roam
import roam.project
import roam.config
import configmanager.QGIS as QGIS
import roam.utils

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
    projectupdated = pyqtSignal(object)
    projectloaded = pyqtSignal(object)
    selectlayersupdated = pyqtSignal(list)

    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.project = None
        self.bar = None
        self.roamapp = None
        self.logger = roam.utils.logger

        menu = QMenu()

        # self.roamVersionLabel.setText("You are running IntraMaps Roam version {}".format(roam.__version__))

        self.openProjectFolderButton.pressed.connect(self.openprojectfolder)
        self.openinQGISButton.pressed.connect(self.openinqgis)
        # TODO Move these to the publish page

        # self.depolyProjectButton.pressed.connect(self.deploy_project)
        # self.depolyInstallProjectButton.pressed.connect(functools.partial(self.deploy_project, True))
        self.savePageButton.pressed.connect(self.savePage)

        self.filewatcher = QFileSystemWatcher()
        self.filewatcher.fileChanged.connect(self.qgisprojectupdated)

        self.projectupdatedlabel.linkActivated.connect(self.reloadproject)
        self.projectupdatedlabel.hide()

        # self.setpage(4)
        self.currentnode = None
        self.form = None

        qgislocation = r'C:\OSGeo4W\bin\qgis.bat'
        qgislocation = roam.config.settings.setdefault('configmanager', {}) \
            .get('qgislocation', "")

        self.qgispathEdit.setText(qgislocation)
        self.qgispathEdit.textChanged.connect(self.save_qgis_path) 
        self.filePickerButton.pressed.connect(self.set_qgis_path)

        self.connect_page_events()

        QgsProject.instance().readProject.connect(self.projectLoaded)

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

    def setpage(self, page, node, refreshingProject=False):
        """
        Set the current page in the config manager.  We pass the project into the current
        page so that it knows what the project is.
        """
        self.currentnode = node

        if not refreshingProject and self.project:
            self.write_config_currentwidget()
        else:
            roam.utils.info("Reloading project. Not saving current config values")

        self.unload_current_widget()

        # Set the new widget for the selected page
        self.stackedWidget.setCurrentIndex(page)

        self.project = node.project

        widget = self.stackedWidget.currentWidget()
        widget.roamapp = self.roamapp
        if hasattr(widget, "set_project"):
            widget.set_project(self.project, self.currentnode)
        if hasattr(widget, "set_data"):
            widget.set_data({
                "project": node.project,
                "config": self.roamapp.config,
                "node": self.currentnode,
                "app_root": self.roamapp.approot,
                "data_root": self.roamapp.data_folder,
                "projects_root": self.roamapp.projectsroot,
                "profile_root": self.roamapp.profileroot
            })

        if node.title:
            title = node.title
        elif self.project:
            title = self.project.name
        else:
            title = "No title set"
        self.projectlabel.setText(title)

        if node.project:
            self.openProjectFolderButton.show()
            self.openinQGISButton.show()
        else:
            self.openProjectFolderButton.hide()
            self.openinQGISButton.hide()

        self.savePageButton.setVisible(node.saveable)

    @property
    def widget(self):
        """
        :return: The current widget that is set.
        """
        return self.stackedWidget.currentWidget()

    def unload_current_widget(self):
        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, "unload_project"):
            widget.unload_project()

    def write_config_currentwidget(self):
        """
        Call the write config command on the current widget.
        """
        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, "write_config"):
            roam.utils.debug("Write config for {} in project {}".format(widget.objectName(), self.project.name))
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

        self._saveproject(update_version=True, reset_save_point=True)
        options = {}

        bundle.bundle_project(self.project, path, options, as_install=with_data)

    def setaboutinfo(self):
        """
        Set the current about info on the widget
        """
        self.versionLabel.setText(roam.__version__)
        self.qgisapiLabel.setText(str(Qgis.QGIS_VERSION))

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
        self.projectupdated.emit(self.project)
        # self.setproject(self.project)

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

    def setproject(self, project):
        """
        Set the widgets active project.
        """
        self.unload_current_widget()

        if self.project:
            savelast = QMessageBox.question(self,
                                    "Save Current Project",
                                    "Save {}?".format(self.project.name),
                                    QMessageBox.Save | QMessageBox.No)
            if savelast == QMessageBox.Accepted:
                self._saveproject()

        self.filewatcher.removePaths(self.filewatcher.files())
        self.projectupdatedlabel.hide()
        self._closeqgisproject()

        if project.valid:
            self.startsettings = copy.deepcopy(project.settings)
            self.project = project
            self.loadqgisproject(project, self.project.projectfile)

    def projectLoaded(self):
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
        QGIS.close_project()

    def savePage(self, closing=False):
        """
        Save the current page settings.
        """
        if hasattr(self.widget, "write_config"):
            self.logger.debug("Saving widget")
            if closing:
                self.widget.on_closing()
            self.widget.write_config()
        else:
            self.logger.debug("Missing write_config for {}".format(self.widget.__class__.__name__))

        if self.project:
            self._saveproject()
            return

    def _saveproject(self, update_version=False, reset_save_point=False):
        """
        Save the project config to disk.
        """
        if not self.project:
            return

        self.logger.info("Saving project: {}".format(self.project.name))

        self.write_config_currentwidget()
        # self.project.dump_settings()
        self.project.save(update_version=update_version, reset_save_point=reset_save_point)
        self.filewatcher.removePaths(self.filewatcher.files())
        QgsProject.instance().write()
        self.filewatcher.addPath(self.project.projectfile)
        self.projectsaved.emit()
