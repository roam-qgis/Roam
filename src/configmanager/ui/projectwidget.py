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
from configmanager.models import widgeticon, WidgetItem, WidgetsModel, QgsLayerModel, QgsFieldModel, LayerTypeFilter, CaptureLayerFilter, CaptureLayersModel

from roam.api import FeatureForm

import configmanager.editorwidgets
import roam.editorwidgets
import roam.projectparser
import roam.yaml
import roam
import roam.project
import roam.config
import configmanager.logger as logger

readonlyvalues = [('Never', 'never'),
                  ('Always', 'always'),
                  ('When editing', 'editing'),
                  ('When inserting', 'insert')]

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

        self.fieldsmodel = QgsFieldModel()
        self.widgetmodel = WidgetsModel()
        self.possiblewidgetsmodel = QStandardItemModel()

        self.formlayersmodel = QgsLayerModel(watchregistry=False)
        self.formlayers = CaptureLayerFilter()
        self.formlayers.setSourceModel(self.formlayersmodel)

        self.selectlayermodel = CaptureLayersModel(watchregistry=False)
        self.selectlayerfilter = LayerTypeFilter(geomtypes=[])
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)
        self.selectlayermodel.dataChanged.connect(self.selectlayerschanged)

        self.layerCombo.setModel(self.formlayers)
        self.widgetCombo.setModel(self.possiblewidgetsmodel)
        self.selectLayers.setModel(self.selectlayerfilter)
        self.selectLayers_2.setModel(self.selectlayerfilter)
        self.fieldList.setModel(self.fieldsmodel)

        self.widgetlist.setModel(self.widgetmodel)
        self.widgetlist.selectionModel().currentChanged.connect(self.updatecurrentwidget)
        self.widgetmodel.rowsRemoved.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.rowsInserted.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.modelReset.connect(self.setwidgetconfigvisiable)

        self.titleText.textChanged.connect(self.updatetitle)

        QgsProject.instance().readProject.connect(self._readproject)

        self.loadwidgettypes()

        self.addWidgetButton.pressed.connect(self.newwidget)
        self.removeWidgetButton.pressed.connect(self.removewidget)

        self.roamVersionLabel.setText("You are running IntraMaps Roam version {}".format(roam.__version__))

        self.openProjectFolderButton.pressed.connect(self.openprojectfolder)
        self.openinQGISButton.pressed.connect(self.openinqgis)

        self.filewatcher = QFileSystemWatcher()
        self.filewatcher.fileChanged.connect(self.qgisprojectupdated)

        self.formfolderLabel.linkActivated.connect(self.openformfolder)
        self.projectupdatedlabel.linkActivated.connect(self.reloadproject)
        self.projectupdatedlabel.hide()
        self.formtab.currentChanged.connect(self.formtabchanged)

        self.expressionButton.clicked.connect(self.opendefaultexpression)

        self.fieldList.currentIndexChanged.connect(self.updatewidgetname)
        self.fieldwarninglabel.hide()

        for item, data in readonlyvalues:
            self.readonlyCombo.addItem(item, data)

        self.setpage(4)
        self.form = None

    def setaboutinfo(self):
        self.versionLabel.setText(roam.__version__)
        self.qgisapiLabel.setText(str(QGis.QGIS_VERSION))

    def checkcapturelayers(self):
        haslayers = self.project.hascapturelayers()
        self.formslayerlabel.setVisible(not haslayers)
        return haslayers

    def opendefaultexpression(self):
        layer = self.currentform.QGISLayer
        dlg = QgsExpressionBuilderDialog(layer, "Create default value expression", self)
        text = self.defaultvalueText.text().strip('[%').strip('%]').strip()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.defaultvalueText.setText('[% {} %]'.format(dlg.expressionText()))

    def openformfolder(self, url):
        openfolder(url)

    def selectlayerschanged(self, *args):
        self.formlayers.setSelectLayers(self.project.selectlayers)
        self.checkcapturelayers()
        self.selectlayersupdated.emit(self.project.selectlayers)

    def formtabchanged(self, index):
        # preview
        if index == 1:
            self.form.settings['widgets'] = list(self.widgetmodel.widgets())
            self.setformpreview(self.form)


    def setpage(self, page):
        self.stackedWidget.setCurrentIndex(page)

    def reloadproject(self, *args):
        self.setproject(self.project)

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

    def setwidgetconfigvisiable(self, *args):
        haswidgets = self.widgetmodel.rowCount() > 0
        self.widgetframe.setEnabled(haswidgets)

    def removewidget(self):
        """
        Remove the selected widget from the widgets list
        """
        widget, index = self.currentuserwidget
        if index.isValid():
            self.widgetmodel.removeRow(index.row(), index.parent())

    def newwidget(self):
        """
        Create a new widget.  The default is a list.
        """
        widget = {}
        widget['widget'] = 'Text'
        # Grab the first field.
        widget['field'] = self.fieldsmodel.index(0, 0).data(QgsFieldModel.FieldNameRole)
        currentindex = self.widgetlist.currentIndex()
        currentitem = self.widgetmodel.itemFromIndex(currentindex)
        if currentitem and currentitem.iscontainor():
            parent = currentindex
        else:
            parent = currentindex.parent()
        index = self.widgetmodel.addwidget(widget, parent)
        self.widgetlist.setCurrentIndex(index)

    def loadwidgettypes(self):
        self.widgetCombo.blockSignals(True)
        for widgettype in roam.editorwidgets.core.supportedwidgets():
            try:
                configclass = configmanager.editorwidgets.widgetconfigs[widgettype]
            except KeyError:
                continue

            configwidget = configclass()
            item = QStandardItem(widgettype)
            item.setData(configwidget, Qt.UserRole)
            item.setData(widgettype, Qt.UserRole + 1)
            item.setIcon(QIcon(widgeticon(widgettype)))
            self.widgetCombo.model().appendRow(item)
            self.widgetstack.addWidget(configwidget)
        self.widgetCombo.blockSignals(False)

    def usedfields(self):
        """
        Return the list of fields that have been used by the the current form's widgets
        """
        for widget in self.currentform.widgets:
            yield widget['field']

    @property
    def currentform(self):
        """
        Return the current selected form.
        """
        return self.form

    @property
    def currentuserwidget(self):
        """
        Return the selected user widget.
        """
        index = self.widgetlist.currentIndex()
        return index.data(Qt.UserRole), index

    @property
    def currentwidgetconfig(self):
        """
        Return the selected widget in the widget combo.
        """
        index = self.widgetCombo.currentIndex()
        index = self.possiblewidgetsmodel.index(index, 0)
        return index.data(Qt.UserRole), index, index.data(Qt.UserRole + 1)

    def updatewidgetname(self, index):
        # Only change the edit text on name field if it's not already set to something other then the
        # field name.
        field = self.fieldsmodel.index(index, 0).data(QgsFieldModel.FieldNameRole)
        currenttext = self.nameText.text()
        foundfield = self.fieldsmodel.findfield(currenttext)
        if foundfield:
            self.nameText.setText(field)

    def _save_widgetfield(self, index):
        """
        Save the selected field for the current widget.

        Shows a error if the field is already used but will allow
        the user to still set it in the case of extra logic for that field
        in the forms Python logic.
        """
        widget, index = self.currentuserwidget
        row = self.fieldList.currentIndex()
        field = self.fieldsmodel.index(row, 0).data(QgsFieldModel.FieldNameRole)
        showwarning = field in self.usedfields()
        self.fieldwarninglabel.setVisible(showwarning)
        widget['field'] = field
        self.widgetmodel.setData(index, widget, Qt.UserRole)

    def _save_selectedwidget(self, index):
        configwidget, index, widgettype = self.currentwidgetconfig
        widget, index = self.currentuserwidget
        if not widget:
            return

        widget['widget'] = widgettype
        widget['required'] = self.requiredCheck.isChecked()
        widget['rememberlastvalue'] = self.savevalueCheck.isChecked()
        widget['config'] = configwidget.getconfig()
        widget['name'] = self.nameText.text()
        widget['read-only-rules'] = [self.readonlyCombo.itemData(self.readonlyCombo.currentIndex())]
        widget['hidden'] = self.hiddenCheck.isChecked()

        self.widgetmodel.setData(index, widget, Qt.UserRole)

    def _save_default(self):
        widget, index = self.currentuserwidget
        default = self.defaultvalueText.text()
        widget['default'] = default
        self.widgetmodel.setData(index, widget, Qt.UserRole)

    def _save_selectionlayers(self, index, layer, value):
        config = self.project.settings

        self.selectlayermodel.dataChanged.emit(index, index)

    def _save_formtype(self, index):
        formtype = self.formtypeCombo.currentText()
        form = self.currentform
        form.settings['type'] = formtype

    def _save_formname(self, text):
        """
        Save the form label to the settings file.
        """
        try:
            form = self.currentform
            if form is None:
                return
            form.settings['label'] = text
            self.projectupdated.emit()
        except IndexError:
            return

    def _save_layer(self, index):
        """
        Save the selected layer to the settings file.
        """
        index = self.formlayers.index(index, 0)
        layer = index.data(Qt.UserRole)
        if not layer:
            return

        form = self.currentform
        if form is None:
            return

        form.settings['layer'] = layer.name()
        self.updatefields(layer)

    def setsplash(self, splash):
        pixmap = QPixmap(splash)
        w = self.splashlabel.width()
        h = self.splashlabel.height()
        self.splashlabel.setPixmap(pixmap.scaled(w,h, Qt.KeepAspectRatio))

    def setproject(self, project, loadqgis=True):
        """
        Set the widgets active project.
        """
        self.disconnectsignals()
        self.mapisloaded = False
        self.filewatcher.removePaths(self.filewatcher.files())
        self.projectupdatedlabel.hide()
        self._closeqgisproject()

        if project.valid:
            self.startsettings = copy.deepcopy(project.settings)
            self.project = project
            self.projectlabel.setText(project.name)
            self.versionText.setText(project.version)
            self.selectlayermodel.config = project.settings
            self.formlayers.setSelectLayers(self.project.selectlayers)
            self.setsplash(project.splash)
            self.loadqgisproject(project, self.project.projectfile)
            self.filewatcher.addPath(self.project.projectfile)
            self.projectloaded.emit(self.project)

    def loadqgisproject(self, project, projectfile):
        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        QgsProject.instance().read(fileinfo)

    def _closeqgisproject(self):
        if self.canvas.isDrawing():
            return

        self.canvas.freeze(True)
        self.formlayersmodel.removeall()
        self.selectlayermodel.removeall()
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

    def _readproject(self, doc):
        self.formlayersmodel.refresh()
        self.selectlayermodel.refresh()
        self._updateforproject(self.project)

    def _updateforproject(self, project):
        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)

    def swapwidgetconfig(self, index):
        widgetconfig, _, _ = self.currentwidgetconfig
        defaultvalue = widgetconfig.defaultvalue
        self.defaultvalueText.setText(defaultvalue)

        self.updatewidgetconfig({})

    def updatetitle(self, text):
        self.project.settings['title'] = text
        self.projectlabel.setText(text)
        self.projectupdated.emit()

    def updatewidgetconfig(self, config):
        widgetconfig, index, widgettype = self.currentwidgetconfig
        self.setconfigwidget(widgetconfig, config)

    def setformpreview(self, form):
        def removewidget():
            item = self.frame_2.layout().itemAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        removewidget()

        featureform = FeatureForm.from_form(form, form.settings, None, {})

        self.frame_2.layout().addWidget(featureform)

    def connectsignals(self):
        self.formLabelText.textChanged.connect(self._save_formname)
        self.layerCombo.currentIndexChanged.connect(self._save_layer)
        self.formtypeCombo.currentIndexChanged.connect(self._save_formtype)

        #widget settings
        self.fieldList.currentIndexChanged.connect(self._save_widgetfield)
        self.requiredCheck.toggled.connect(self._save_selectedwidget)
        self.savevalueCheck.toggled.connect(self._save_selectedwidget)
        self.defaultvalueText.textChanged.connect(self._save_default)
        self.widgetCombo.currentIndexChanged.connect(self._save_selectedwidget)
        self.widgetCombo.currentIndexChanged.connect(self.swapwidgetconfig)
        self.nameText.textChanged.connect(self._save_selectedwidget)
        self.readonlyCombo.currentIndexChanged.connect(self._save_selectedwidget)
        self.hiddenCheck.toggled.connect(self._save_selectedwidget)

    def disconnectsignals(self):
        try:
            self.formLabelText.textChanged.disconnect(self._save_formname)
            self.layerCombo.currentIndexChanged.disconnect(self._save_layer)
            self.formtypeCombo.currentIndexChanged.disconnect(self._save_formtype)

            #widget settings
            self.fieldList.currentIndexChanged.disconnect(self._save_widgetfield)
            self.requiredCheck.toggled.disconnect(self._save_selectedwidget)
            self.savevalueCheck.toggled.disconnect(self._save_selectedwidget)
            self.defaultvalueText.textChanged.disconnect(self._save_default)
            self.widgetCombo.currentIndexChanged.disconnect(self._save_selectedwidget)
            self.widgetCombo.currentIndexChanged.disconnect(self.swapwidgetconfig)
            self.nameText.textChanged.disconnect(self._save_selectedwidget)
            self.readonlyCombo.currentIndexChanged.disconnect(self._save_selectedwidget)
            self.hiddenCheck.toggled.disconnect(self._save_selectedwidget)
        except TypeError:
            pass

    def setform(self, form):
        """
        Update the UI with the currently selected form.
        """

        def getfirstlayer():
            index = self.formlayers.index(0,0)
            layer = index.data(Qt.UserRole)
            layer = layer.name()
            return layer

        def loadwidgets(widget):
            """
            Load the widgets into widgets model
            """
            self.widgetmodel.clear()
            self.widgetmodel.loadwidgets(form.widgets)

        def findlayer(layername):
            index = self.formlayersmodel.findlayer(layername)
            index = self.formlayers.mapFromSource(index)
            layer = index.data(Qt.UserRole)
            return index, layer


        self.disconnectsignals()

        self.form = form

        settings = form.settings
        label = form.label
        layername = settings.setdefault('layer', getfirstlayer())
        layerindex, layer = findlayer(layername)
        if not layer or not layerindex.isValid():
            return

        formtype = settings.setdefault('type', 'auto')
        widgets = settings.setdefault('widgets', [])

        self.formLabelText.setText(label)
        folderurl = "<a href='{path}'>{name}</a>".format(path=form.folder, name=os.path.basename(form.folder))
        self.formfolderLabel.setText(folderurl)
        self.layerCombo.setCurrentIndex(layerindex.row())
        self.updatefields(layer)

        index = self.formtypeCombo.findText(formtype)
        if index == -1:
            self.formtypeCombo.insertItem(0, formtype)
            self.formtypeCombo.setCurrentIndex(0)
        else:
            self.formtypeCombo.setCurrentIndex(index)

        loadwidgets(widgets)

        # Set the first widget
        index = self.widgetmodel.index(0, 0)
        if index.isValid():
            self.widgetlist.setCurrentIndex(index)
            self.updatecurrentwidget(index, None)

        self.connectsignals()

    def updatefields(self, layer):
        """
        Update the UI with the fields for the selected layer.
        """
        self.fieldsmodel.setLayer(layer)

    def setconfigwidget(self, configwidget, config):
        """
        Set the active config widget.
        """

        try:
            configwidget.widgetdirty.disconnect(self._save_selectedwidget)
        except TypeError:
            pass

        #self.descriptionLabel.setText(configwidget.description)
        self.widgetstack.setCurrentWidget(configwidget)
        configwidget.setconfig(config)

        configwidget.widgetdirty.connect(self._save_selectedwidget)

    def updatecurrentwidget(self, index, _):
        """
        Update the UI with the config for the current selected widget.
        """
        if not index.isValid():
            return

        widget = index.data(Qt.UserRole)
        widgettype = widget['widget']
        field = widget['field']
        required = widget.setdefault('required', False)
        savevalue = widget.setdefault('rememberlastvalue', False)
        name = widget.setdefault('name', field)
        default = widget.setdefault('default', '')
        readonly = widget.setdefault('read-only-rules', [])
        hidden = widget.setdefault('hidden', False)

        try:
            data = readonly[0]
        except:
            data = 'never'

        self.readonlyCombo.blockSignals(True)
        index = self.readonlyCombo.findData(data)
        self.readonlyCombo.setCurrentIndex(index)
        self.readonlyCombo.blockSignals(False)

        self.defaultvalueText.blockSignals(True)
        if not isinstance(default, dict):
            self.defaultvalueText.setText(default)
            self.defaultvalueText.setEnabled(True)
            self.expressionButton.setEnabled(True)
        else:
            # TODO Handle the more advanced default values.
            self.defaultvalueText.setText("Advanced default set in config")
            self.defaultvalueText.setEnabled(False)
            self.expressionButton.setEnabled(False)
        self.defaultvalueText.blockSignals(False)

        self.nameText.blockSignals(True)
        self.nameText.setText(name)
        self.nameText.blockSignals(False)

        self.requiredCheck.blockSignals(True)
        self.requiredCheck.setChecked(required)
        self.requiredCheck.blockSignals(False)

        self.savevalueCheck.blockSignals(True)
        self.savevalueCheck.setChecked(savevalue)
        self.savevalueCheck.blockSignals(False)

        self.hiddenCheck.blockSignals(True)
        self.hiddenCheck.setChecked(hidden)
        self.hiddenCheck.blockSignals(False)

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

        self.updatewidgetconfig(config=widget.setdefault('config', {}))

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

        form = self.currentform
        if form:
            form.settings['widgets'] = list(self.widgetmodel.widgets())
            logger.debug(form.settings)

        self.project.save()
        self.projectsaved.emit()




