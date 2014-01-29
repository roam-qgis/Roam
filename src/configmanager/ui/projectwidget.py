import os

from PyQt4.QtCore import Qt, QDir, QFileInfo
from PyQt4.QtGui import QWidget, QStandardItemModel, QStandardItem, QIcon

from qgis.core import QgsProject, QgsMapLayerRegistry, QgsPalLabeling
from qgis.gui import QgsMapCanvas

from configmanager.ui.ui_projectwidget import Ui_Form
from configmanager.models import widgeticon, WidgetsModel, QgsLayerModel, QgsFieldModel

import roam.projectparser


class ProjectWidget(Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.canvas.mapRenderer().setLabelingEngine(QgsPalLabeling())

        self.formmodel = QStandardItemModel()
        self.widgetmodel = QStandardItemModel()
        self.possiblewidgetsmodel = WidgetsModel()
        self.layermodel = QgsLayerModel(watchregistry=False)

        self.layerCombo.setModel(self.layermodel)
        self.widgetCombo.setModel(self.possiblewidgetsmodel)

        self.widgetlist.setModel(self.widgetmodel)
        self.widgetlist.selectionModel().currentChanged.connect(self.updatecurrentwidget)

        self.formlist.setModel(self.formmodel)
        self.formlist.selectionModel().currentChanged.connect(self.updatecurrentform)

        QgsProject.instance().readProject.connect(self._readproject)

    def setproject(self, project, loadqgis=True):
        self.project = project
        if loadqgis:
            self.loadqgisproject(project, self.project.projectfile)
        else:
            self._updateforproject(self.project)

    def loadqgisproject(self, project, projectfile):
        self._closeqgisproject()
        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        QgsProject.instance().read(fileinfo)

    def _closeqgisproject(self):
        self.canvas.freeze()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        self.canvas.clear()
        self.canvas.freeze(False)

    def _readproject(self, doc):
        parser = roam.projectparser.ProjectParser(doc)
        canvasnode = parser.canvasnode
        self.canvas.mapRenderer().readXML(canvasnode)
        self.canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(self.canvaslayers)
        self.canvas.updateScale()
        self.canvas.freeze(False)
        self.canvas.refresh()
        self.layermodel.updateLayerList(QgsMapLayerRegistry.instance().mapLayers().values())
        self._updateforproject(self.project)

    def _updateforproject(self, project):
        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)
        self._loadforms(project.forms)

    def _loadforms(self, forms):
        self.formmodel.clear()
        for form in forms:
            item = QStandardItem(form.name)
            item.setEditable(False)
            item.setIcon(QIcon(form.icon))
            item.setData(form, Qt.UserRole)
            self.formmodel.appendRow(item)

    def updatecurrentform(self, index, _):
        form = index.data(Qt.UserRole)
        self.formNameText.setText(form.name)
        formtype = form.settings.get("type", "auto")
        index = self.formtypeCombo.findText(formtype)
        if index == -1:
            self.formtypeCombo.insertItem(0, formtype)
            self.formtypeCombo.setCurrentIndex(0)
        else:
            self.formtypeCombo.setCurrentIndex(index)

        def loadwidgets(widgets):
            self.widgetmodel.clear()
            for widget in widgets:
                widgettype = widget['widget']
                item = QStandardItem(widgettype)
                item.setIcon(widgeticon(widgettype))
                item.setData(widget, Qt.UserRole)
                self.widgetmodel.appendRow(item)

        loadwidgets(form.widgets)

    def updatecurrentwidget(self, index, _):
        widget = index.data(Qt.UserRole)
        widgettype = widget['widget']
        print widgettype
        field = widget['field']
        pass





