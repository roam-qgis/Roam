import os
import copy
from PyQt4.Qsci import QsciLexerYAML

from PyQt4.QtCore import Qt, QDir, QFileInfo
from PyQt4.QtGui import QWidget, QStandardItemModel, QStandardItem, QIcon

from qgis.core import QgsProject, QgsMapLayerRegistry, QgsPalLabeling
from qgis.gui import QgsMapCanvas

from configmanager.ui.ui_projectwidget import Ui_Form
from configmanager.models import widgeticon, WidgetsModel, QgsLayerModel, QgsFieldModel, LayerFilter

import roam.projectparser
import roam.yaml
import roam


class ProjectWidget(Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.canvas.mapRenderer().setLabelingEngine(QgsPalLabeling())

        self.fieldsmodel = QgsFieldModel()
        self.formmodel = QStandardItemModel()
        self.widgetmodel = QStandardItemModel()
        self.possiblewidgetsmodel = WidgetsModel()
        self.layermodel = QgsLayerModel(watchregistry=True)
        self.selectlayermodel = QgsLayerModel(watchregistry=True, checkselect=True)

        self.layerfilter = LayerFilter()
        self.layerfilter.setSourceModel(self.layermodel)

        self.selectlayerfilter = LayerFilter()
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)

        self.layerCombo.setModel(self.layerfilter)
        self.widgetCombo.setModel(self.possiblewidgetsmodel)

        self.widgetlist.setModel(self.widgetmodel)
        self.widgetlist.selectionModel().currentChanged.connect(self.updatecurrentwidget)

        self.formlist.setModel(self.formmodel)
        self.formlist.selectionModel().currentChanged.connect(self.updatecurrentform)

        self.selectLayers.setModel(self.selectlayerfilter)

        self.fieldList.setModel(self.fieldsmodel)

        QgsProject.instance().readProject.connect(self._readproject)

        self.menuList.setCurrentRow(0)

        # Form settings
        self.formLabelText.textChanged.connect(self._save_formname)
        self.layerCombo.currentIndexChanged.connect(self._save_layer)

    @property
    def currentform(self):
        """
        Return the current selected form.
        """
        index = self.formlist.selectedIndexes()[0]
        return index.data(Qt.UserRole)

    def _save_formname(self, text):
        """
        Save the form label to the settings file.
        """
        try:
            form = self.currentform
            form.settings['label'] = text
            print form.settings
        except IndexError:
            return

    def _save_layer(self, index):
        """
        Save the selected layer to the settings file.
        """
        index = self.layerfilter.index(index, 0)
        layer = index.data(Qt.UserRole)
        form = self.currentform
        form.settings['layer'] = layer.name()
        self.updatefields(layer)

    def setproject(self, project, loadqgis=True):
        """
        Set the widgets active project.
        """
        self.project = project
        self.selectlayermodel.config = project.settings
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
        self.selectlayermodel.updateLayerList(QgsMapLayerRegistry.instance().mapLayers().values())
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

        index = self.formmodel.index(0, 0)
        if index.isValid():
            self.formlist.setCurrentIndex(index)
            self.formframe.show()
        else:
            self.formframe.hide()

    def updatecurrentform(self, index, _):
        """
        Update the UI with the currently selected form.
        """
        form = index.data(Qt.UserRole)
        settings = form.settings
        label = settings['label']
        layer = settings['layer']
        version = settings.get('version', roam.__version__)
        formtype = settings.get('type', 'auto')
        widgets = settings.get('widgets', [])

        self.formLabelText.setText(label)
        self.versionText.setText(version)
        index = self.layermodel.findlayer(layer)
        index = self.layerfilter.mapFromSource(index)
        if index.isValid():
            self.layerCombo.blockSignals(True)
            self.layerCombo.setCurrentIndex(index.row())
            self.updatefields(index.data(Qt.UserRole))
            self.layerCombo.blockSignals(False)

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

        loadwidgets(widgets)

        index = self.widgetmodel.index(0, 0)
        if index.isValid():
            self.widgetlist.setCurrentIndex(index)

    def updatefields(self, layer):
        """
        Update the UI with the fields for the selected layer.
        """
        self.fieldsmodel.setLayer(layer)

    def updatecurrentwidget(self, index, _):
        """
        Update the UI with the config for the current selected widget.
        """
        widget = index.data(Qt.UserRole)
        widgettype = widget['widget']
        field = widget['field']

        self.fieldList.setEditText(field)
        index = self.possiblewidgetsmodel.findwidget(widgettype)
        if index.isValid():
            self.widgetCombo.setCurrentIndex(index.row())

    def saveproject(self):
        """
        Save the project config to disk.
        """
        title = self.titleText.text()
        description = self.descriptionText.toPlainText()
        version = str(self.versionText.text())

        settings = self.project.settings
        settings['title'] = title
        settings['description'] = description
        settings['version'] = version

        settingspath = os.path.join(self.project.folder, "settings.config")

        with open(settingspath, 'w') as f:
            roam.yaml.dump(data=settings, stream=f, default_flow_style=False)


