import sys
import os
import copy
import subprocess
import shutil

from datetime import datetime

from PyQt4.QtCore import Qt, QDir, QFileInfo, pyqtSignal, QModelIndex, QFileSystemWatcher, QUrl
from PyQt4.QtGui import QWidget, QStandardItemModel, QStandardItem, QIcon, QMessageBox, QPixmap, QDesktopServices

from qgis.core import QgsProject, QgsMapLayerRegistry, QgsPalLabeling, QGis
from qgis.gui import QgsMapCanvas, QgsExpressionBuilderDialog, QgsMessageBar

from configmanager.ui.ui_projectwidget import Ui_Form
from configmanager.models import widgeticon, WidgetItem, WidgetsModel, QgsLayerModel, QgsFieldModel, LayerTypeFilter, \
    CaptureLayerFilter, CaptureLayersModel

from roam.api import FeatureForm

import configmanager.editorwidgets
import roam.editorwidgets
import roam.projectparser
import roam.yaml
import roam
import roam.project
import roam.config
import configmanager.logger as logger


def layer(name):
    return QgsMapLayerRegistry.instance.mapLayersByName(name)[0]


def openfolder(folder):
    QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


def openqgis(project, qgislocation):
    # TODO This needs to look in other places for QGIS.
    cmd = 'qgis'
    if sys.platform == 'win32':
        cmd = qgislocation
    subprocess.Popen([cmd, "--noplugins", project])


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
        self.mapisloaded = False
        self.bar = None

        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.canvas.mapRenderer().setLabelingEngine(QgsPalLabeling())

        # self.roamVersionLabel.setText("You are running IntraMaps Roam version {}".format(roam.__version__))

        self.openProjectFolderButton.pressed.connect(self.openprojectfolder)
        self.openinQGISButton.pressed.connect(self.openinqgis)

        self.filewatcher = QFileSystemWatcher()
        self.filewatcher.fileChanged.connect(self.qgisprojectupdated)

        self.projectupdatedlabel.linkActivated.connect(self.reloadproject)
        self.projectupdatedlabel.hide()

        # self.setpage(4)
        self.currentnode = None
        self.form = None

    def setpage(self, page, node):
        self.currentnode = node

        self.write_config_currentwidget()

        self.stackedWidget.setCurrentIndex(page)
        if self.project:
            print self.project.dump_settings()

        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, "set_project"):
            widget.set_project(self.project, self.currentnode)

    def write_config_currentwidget(self):
        widget = self.stackedWidget.currentWidget()
        if hasattr(widget, "write_config"):
            widget.write_config()

    def setaboutinfo(self):
        self.versionLabel.setText(roam.__version__)
        self.qgisapiLabel.setText(str(QGis.QGIS_VERSION))

    def checkcapturelayers(self):
        haslayers = self.project.hascapturelayers()
        self.formslayerlabel.setVisible(not haslayers)
        return haslayers


    def selectlayerschanged(self, *args):
        self.formlayers.setSelectLayers(self.project.selectlayers)
        self.checkcapturelayers()
        self.selectlayersupdated.emit(self.project.selectlayers)

    def reloadproject(self, *args):
        self.setproject(self.project)
        self.projectupdated.emit()

    def qgisprojectupdated(self, path):
        self.projectupdatedlabel.show()
        self.projectupdatedlabel.setText("The QGIS project has been updated. <a href='reload'> "
                                         "Click to reload</a>. <b style=\"color:red\">Unsaved data will be lost</b>")

    def openinqgis(self):
        projectfile = self.project.projectfile
        qgislocation = r'C:\OSGeo4W\bin\qgis.bat'
        qgislocation = roam.config.settings.setdefault('configmanager', {}) \
            .setdefault('qgislocation', qgislocation)

        try:
            openqgis(projectfile, qgislocation)
        except OSError:
            self.bar.pushMessage("Looks like I couldn't find QGIS",
                                 "Check qgislocation in roam.config", QgsMessageBar.WARNING)

    def openprojectfolder(self):
        folder = self.project.folder
        openfolder(folder)

    def setproject(self, project, loadqgis=True):
        """
        Set the widgets active project.
        """
        self.mapisloaded = False
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
        self.projectLocationLabel.setText("Project File: {}".format(os.path.basename(project.projectfile)))
        QgsProject.instance().read(fileinfo)

    def _closeqgisproject(self):
        if self.canvas.isDrawing():
            return

        self.canvas.freeze(True)
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        self.canvas.freeze(False)

    def loadmap(self):
        if self.mapisloaded:
            return

        # This is a dirty hack to work around the timer that is in QgsMapCanvas in 2.2.
        # Refresh will stop the canvas timer
        # Repaint will redraw the widget.
        # loadmap is only called once per project load so it's safe to do this here.
        self.canvas.refresh()
        self.canvas.repaint()

        parser = roam.projectparser.ProjectParser.fromFile(self.project.projectfile)
        canvasnode = parser.canvasnode
        self.canvas.mapRenderer().readXML(canvasnode)
        self.canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(self.canvaslayers)
        self.canvas.updateScale()
        self.canvas.refresh()

        self.mapisloaded = True

    def _saveproject(self):
        """
        Save the project config to disk.
        """
        self.write_config_currentwidget()
        self.project.dump_settings()
        self.project.save()
        self.projectsaved.emit()




