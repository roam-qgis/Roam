import os
import copy
import subprocess

from PyQt4.QtCore import Qt, QDir, QFileInfo, pyqtSignal, QModelIndex, QFileSystemWatcher
from PyQt4.QtGui import QWidget, QStandardItemModel, QStandardItem, QIcon

from qgis.core import QgsProject, QgsMapLayerRegistry, QgsPalLabeling
from qgis.gui import QgsMapCanvas

from configmanager.ui.ui_projectwidget import Ui_Form
from configmanager.models import widgeticon, WidgetsModel, QgsLayerModel, QgsFieldModel, LayerFilter

from roam.featureform import FeatureForm

import configmanager.editorwidgets
import roam.editorwidgets
import roam.projectparser
import roam.yaml
import roam

def openfolder(folder):
    subprocess.Popen('explorer "{}"'.format(folder))

def openqgis(project):
    # TODO This needs to look in other places for QGIS.
    subprocess.Popen([r'C:\OSGeo4W\bin\qgis.bat', "--noplugins", project])

class ProjectWidget(Ui_Form, QWidget):
    SampleWidgetRole = Qt.UserRole + 1
    projectsaved = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.canvas.mapRenderer().setLabelingEngine(QgsPalLabeling())

        self.fieldsmodel = QgsFieldModel()
        self.formmodel = QStandardItemModel()
        self.widgetmodel = WidgetsModel()
        self.possiblewidgetsmodel = QStandardItemModel()
        self.layermodel = QgsLayerModel(watchregistry=False)
        self.selectlayermodel = QgsLayerModel(watchregistry=False, checkselect=True)
        self.selectlayermodel.layerchecked.connect(self._save_selectionlayers)

        self.layerfilter = LayerFilter()
        self.layerfilter.setSourceModel(self.layermodel)

        self.selectlayerfilter = LayerFilter()
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)

        self.layerCombo.setModel(self.layerfilter)
        self.widgetCombo.setModel(self.possiblewidgetsmodel)

        self.widgetlist.setModel(self.widgetmodel)
        self.widgetlist.selectionModel().currentChanged.connect(self.updatecurrentwidget)
        self.widgetmodel.rowsRemoved.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.rowsInserted.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.modelReset.connect(self.setwidgetconfigvisiable)

        self.formlist.setModel(self.formmodel)
        self.formlist.selectionModel().currentChanged.connect(self.updatecurrentform)

        self.formpreviewList.setModel(self.formmodel)
        self.formpreviewList.clicked.connect(self.updateformpreview)

        self.selectLayers.setModel(self.selectlayerfilter)

        self.fieldList.setModel(self.fieldsmodel)

        QgsProject.instance().readProject.connect(self._readproject)

        self.menuList.setCurrentRow(0)

        self.loadwidgettypes()

        self.addWidgetButton.pressed.connect(self.newwidget)
        self.removeWidgetButton.pressed.connect(self.removewidget)

        self.roamVersionLabel.setText("You are running IntraMaps Roam version {}".format(roam.__version__))

        self.openProjectFolderButton.pressed.connect(self.openprojectfolder)
        self.openDataButton.pressed.connect(self.opendatafolder)
        self.openinQGISButton.pressed.connect(self.openinqgis)

        self.filewatcher = QFileSystemWatcher()
        self.filewatcher.fileChanged.connect(self.projectupdated)

        self.projectupdatedlabel.linkActivated.connect(self.reloadproject)

    def reloadproject(self, *args):
        self.setproject(self.project)

    def projectupdated(self, path):
        self.projectupdatedlabel.setText("Project has been updated. <a href='reload'> Click to reload<a>")

    def openinqgis(self):
        projectfile = self.project.projectfile
        openqgis(projectfile)

    def opendatafolder(self):
        folder = self.project.folder
        folder = os.path.join(folder, "_data")
        openfolder(folder)

    def openprojectfolder(self):
        folder = self.project.folder
        openfolder(folder)

    def setwidgetconfigvisiable(self, *args):
        haswidgets = self.widgetmodel.rowCount() > 0
        self.groupBox_2.setVisible(haswidgets)

    def removewidget(self):
        """
        Remove the selected widget from the widgets list
        """
        widget, index = self.currentuserwidget
        if index.isValid():
            self.widgetmodel.removeRow(index.row())

    def newwidget(self):
        """
        Create a new widget.  The default is a list.
        """
        widget = {}
        widget['widget'] = 'List'
        # Grab the first field.
        widget['field'] = self.fieldsmodel.index(0, 0).data(QgsFieldModel.FieldNameRole)
        index = self.widgetmodel.addwidget(widget)
        self.widgetlist.setCurrentIndex(index)

    def loadwidgettypes(self):
        self.widgetCombo.blockSignals(True)
        for widgettype in roam.editorwidgets.supportedwidgets:
            try:
                configclass = configmanager.editorwidgets.widgetconfigs[widgettype.widgettype]
            except KeyError:
                continue

            configwidget = configclass()
            samplewidget = roam.editorwidgets.WidgetsRegistry.createwidget(widgettype.widgettype)
            item = QStandardItem(widgettype.widgettype)
            item.setData(configwidget, Qt.UserRole)
            item.setData(samplewidget, ProjectWidget.SampleWidgetRole)
            item.setIcon(QIcon(widgeticon(widgettype.widgettype)))
            self.widgetCombo.model().appendRow(item)
            self.widgetstack.addWidget(configwidget)
            self.samplestack.addWidget(samplewidget)
        self.widgetCombo.blockSignals(False)

    @property
    def currentform(self):
        """
        Return the current selected form.
        """
        index = self.formlist.selectionModel().currentIndex()
        return index.data(Qt.UserRole), index

    @property
    def currentuserwidget(self):
        """
        Return the selected user widget.
        """
        index = self.widgetlist.selectionModel().currentIndex()
        return index.data(Qt.UserRole), index

    @property
    def currentwidgetconfig(self):
        """
        Return the selected widget in the widget combo.
        """
        index = self.widgetCombo.currentIndex()
        index = self.possiblewidgetsmodel.index(index, 0)
        return index.data(Qt.UserRole), index, index.data(ProjectWidget.SampleWidgetRole), index.data(Qt.DisplayRole)

    def _save_selectedwidget(self, index):
        configwidget, index, _, widgetype = self.currentwidgetconfig
        widget, index = self.currentuserwidget
        if not widget:
            return

        widget['widget'] = widgetype
        widget['required'] = self.requiredCheck.isChecked()
        row = self.fieldList.currentIndex()
        field = self.fieldsmodel.index(row, 0).data(QgsFieldModel.FieldNameRole)
        widget['field'] = field
        widget['config'] = configwidget.getconfig()
        widget['name'] = self.nameText.text()

        self.widgetmodel.setData(index, widget, Qt.UserRole)

    def _save_default(self):
        widget, index = self.currentuserwidget
        default = self.defaultvalueText.text()
        widget['default'] = default
        self.widgetmodel.setData(index, widget, Qt.UserRole)

    def _save_selectionlayers(self, index, layer, value):
        config = self.project.settings
        selectlayers = config.get('selectlayers', [])
        layername = unicode(layer.name())
        if value == Qt.Checked:
            selectlayers.append(layername)
        else:
            selectlayers.remove(layername)

        self.selectlayermodel.dataChanged.emit(index, index)

    def _save_formtype(self, index):
        formtype = self.formtypeCombo.currentText()
        form, index = self.currentform
        form.settings['type'] = formtype

    def _save_formname(self, text):
        """
        Save the form label to the settings file.
        """
        try:
            form, index = self.currentform
            form.settings['label'] = text
            self.formmodel.dataChanged.emit(index, index)
        except IndexError:
            return

    def _save_layer(self, index):
        """
        Save the selected layer to the settings file.
        """
        index = self.layerfilter.index(index, 0)
        layer = index.data(Qt.UserRole)
        if not layer:
            return

        form, index = self.currentform
        form.settings['layer'] = layer.name()
        self.formmodel.dataChanged.emit(index, index)
        self.updatefields(layer)

    def setproject(self, project, loadqgis=True):
        """
        Set the widgets active project.
        """
        def connectsignals():
            # Form settings
            self.formLabelText.textChanged.connect(self._save_formname)
            self.layerCombo.currentIndexChanged.connect(self._save_layer)
            self.formtypeCombo.currentIndexChanged.connect(self._save_formtype)

        def disconnectsignals():
            try:
                 # Form settings
                self.formLabelText.textChanged.disconnect(self._save_formname)
                self.layerCombo.currentIndexChanged.disconnect(self._save_layer)
                self.formtypeCombo.currentIndexChanged.disconnect(self._save_formtype)
            except TypeError:
                pass

        disconnectsignals()
        self.filewatcher.removePaths(self.filewatcher.files())
        self.projectupdatedlabel.setText("")

        self.startsettings = copy.deepcopy(project.settings)
        self.project = project
        self.selectlayermodel.config = project.settings
        if loadqgis:
            self.loadqgisproject(project, self.project.projectfile)
        else:
            self._updateforproject(self.project)
        self.filewatcher.addPath(self.project.projectfile)
        connectsignals()

    def loadqgisproject(self, project, projectfile):
        self._closeqgisproject()
        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        QgsProject.instance().read(fileinfo)

    def _closeqgisproject(self):
        if self.canvas.isDrawing():
            return

        self.canvas.freeze(True)
        self.layermodel.removeall()
        self.selectlayermodel.removeall()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
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
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        self.layermodel.addlayers(layers, removeall=True)
        self.selectlayermodel.addlayers(layers, removeall=True)
        self._updateforproject(self.project)

    def _updateforproject(self, project):
        def _loadforms(forms):
            self.formmodel.clear()
            for form in forms:
                item = QStandardItem(form.name)
                item.setEditable(True)
                item.setIcon(QIcon(form.icon))
                item.setData(form, Qt.UserRole)
                self.formmodel.appendRow(item)

            index = self.formmodel.index(0, 0)
            if index.isValid():
                self.formlist.setCurrentIndex(index)
                self.formframe.show()
            else:
                self.formframe.hide()

        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)
        _loadforms(project.forms)

    def swapwidgetconfig(self, index):
        self.updatewidgetconfig({})

    def updatewidgetconfig(self, config):
        widgetconfig, index, sample, widgettype = self.currentwidgetconfig
        self.setconfigwidget(widgetconfig, config, sample, widgettype)

    def updateformpreview(self, index):

        def removewidget():
            item = self.frame_2.layout().itemAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        removewidget()
        form = index.data(Qt.UserRole)

        featureform = FeatureForm.from_form(form, form.settings, None, {})

        self.frame_2.layout().addWidget(featureform)


    def updatecurrentform(self, index, _):
        """
        Update the UI with the currently selected form.
        """
        def connectsignals():
            #widget settings
            self.fieldList.currentIndexChanged.connect(self._save_selectedwidget)
            self.fieldList.editTextChanged.connect(self._save_selectedwidget)
            self.requiredCheck.toggled.connect(self._save_selectedwidget)
            self.defaultvalueText.textChanged.connect(self._save_default)
            self.widgetCombo.currentIndexChanged.connect(self._save_selectedwidget)
            self.widgetCombo.currentIndexChanged.connect(self.swapwidgetconfig)
            self.nameText.textChanged.connect(self._save_selectedwidget)

        def disconnectsignals():
            try:
                #widget settings
                self.fieldList.currentIndexChanged.disconnect(self._save_selectedwidget)
                self.fieldList.editTextChanged.disconnect(self._save_selectedwidget)
                self.requiredCheck.toggled.disconnect(self._save_selectedwidget)
                self.defaultvalueText.textChanged.disconnect(self._save_default)
                self.widgetCombo.currentIndexChanged.disconnect(self._save_selectedwidget)
                self.widgetCombo.currentIndexChanged.disconnect(self.swapwidgetconfig)
                self.nameText.textChanged.disconnect(self._save_selectedwidget)
            except TypeError:
                pass

        disconnectsignals()

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
            self.layerCombo.setCurrentIndex(index.row())
            self.updatefields(index.data(Qt.UserRole))

        index = self.formtypeCombo.findText(formtype)
        if index == -1:
            self.formtypeCombo.insertItem(0, formtype)
            self.formtypeCombo.setCurrentIndex(0)
        else:
            self.formtypeCombo.setCurrentIndex(index)

        self.widgetmodel.loadwidgets(widgets)

        # Set the first widget
        index = self.widgetmodel.index(0, 0)
        if index.isValid():
            self.widgetlist.setCurrentIndex(index)
            self.updatecurrentwidget(index, None)


        connectsignals()

    def updatefields(self, layer):
        """
        Update the UI with the fields for the selected layer.
        """
        self.fieldsmodel.setLayer(layer)

    def setconfigwidget(self, configwidget, config, samplewidget, widgettype):
        """
        Set the active config widget.
        """

        self.samplewrapper = roam.editorwidgets.WidgetsRegistry.widgetwrapper(widgettype,
                                                                             samplewidget,
                                                                             {},
                                                                             None,
                                                                             None,
                                                                             None)
        try:
            configwidget.widgetdirty.disconnect(self.samplewrapper.setconfig)
            configwidget.widgetdirty.disconnect(self._save_selectedwidget)
        except TypeError:
            pass

        self.descriptionLabel.setText(configwidget.description)
        self.samplestack.setCurrentWidget(samplewidget)
        self.widgetstack.setCurrentWidget(configwidget)
        configwidget.setconfig(config)
        self.samplewrapper.setconfig(config)

        configwidget.widgetdirty.connect(self._save_selectedwidget)
        configwidget.widgetdirty.connect(self.samplewrapper.setconfig)

    def updatecurrentwidget(self, index, _):
        """
        Update the UI with the config for the current selected widget.
        """
        if not index.isValid():
            return

        widget = index.data(Qt.UserRole)
        widgettype = widget['widget']
        field = widget['field']
        required = widget.get('required', False)
        name = widget.get('name', field)
        default = widget.get('default', '')

        self.defaultvalueText.blockSignals(True)
        if not isinstance(default, dict):
            self.defaultvalueText.setText(default)
        else:
            # TODO Handle the more advanced default values.
            pass
        self.defaultvalueText.blockSignals(False)

        self.nameText.blockSignals(True)
        self.nameText.setText(name)
        self.nameText.blockSignals(False)

        self.requiredCheck.blockSignals(True)
        self.requiredCheck.setChecked(required)
        self.requiredCheck.blockSignals(False)

        if not field is None:
            self.fieldList.blockSignals(True)
            index = self.fieldList.findData(field.lower(), QgsFieldModel.FieldNameRole)
            if index > -1:
                self.fieldList.setCurrentIndex(index)
            else:
                self.fieldList.setEditText(field)
            self.fieldList.blockSignals(False)

        index = self.widgetCombo.findText(widgettype)
        self.widgetCombo.blockSignals(True)
        if index > -1:
            self.widgetCombo.setCurrentIndex(index)
        self.widgetCombo.blockSignals(False)

        self.updatewidgetconfig(config=widget.get('config', {}))

    def _saveproject(self):
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

        self.projectsaved.emit(self.startsettings, self.project)

        self.startsettings = copy.deepcopy(settings)


