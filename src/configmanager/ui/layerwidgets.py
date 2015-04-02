__author__ = 'Nathan.Woodrow'

import os
from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import QWidget, QPixmap, QStandardItem, QStandardItemModel, QIcon, QDesktopServices
from PyQt4.Qsci import QsciLexerSQL, QsciScintilla

from qgis.core import QgsDataSourceURI
from qgis.gui import QgsExpressionBuilderDialog

from configmanager.ui.nodewidgets import ui_layersnode, ui_layernode, ui_infonode, ui_projectinfo, ui_formwidget
from configmanager.models import (CaptureLayersModel, LayerTypeFilter, QgsFieldModel, WidgetsModel,
                                  QgsLayerModel, CaptureLayerFilter, widgeticon)

import roam.editorwidgets
import configmanager.editorwidgets
from roam.api import FeatureForm, utils


class WidgetBase(QWidget):
    def set_project(self, project, treenode):
        self.project = project
        self.treenode = treenode

    def write_config(self):
        """
        Write the config back to the project settings.
        """
        pass


readonlyvalues = [('Never', 'never'),
                  ('Always', 'always'),
                  ('When editing', 'editing'),
                  ('When inserting', 'insert')]


class FormWidget(ui_formwidget.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(FormWidget, self).__init__(parent)
        self.setupUi(self)
        self.form = None

        self.fieldsmodel = QgsFieldModel()
        self.widgetmodel = WidgetsModel()
        self.possiblewidgetsmodel = QStandardItemModel()
        self.formlayersmodel = QgsLayerModel(watchregistry=True)
        self.formlayers = CaptureLayerFilter()
        self.formlayers.setSourceModel(self.formlayersmodel)

        self.layerCombo.setModel(self.formlayers)
        self.useablewidgets.setModel(self.possiblewidgetsmodel)
        self.fieldList.setModel(self.fieldsmodel)

        self.userwidgets.setModel(self.widgetmodel)
        self.userwidgets.selectionModel().currentChanged.connect(self.load_widget)
        self.widgetmodel.rowsRemoved.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.rowsInserted.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.modelReset.connect(self.setwidgetconfigvisiable)

        self.addWidgetButton.pressed.connect(self.newwidget)
        self.removeWidgetButton.pressed.connect(self.removewidget)

        self.formfolderLabel.linkActivated.connect(self.openformfolder)
        self.expressionButton.clicked.connect(self.opendefaultexpression)

        self.fieldList.currentIndexChanged.connect(self.updatewidgetname)
        self.fieldwarninglabel.hide()
        self.formtab.currentChanged.connect(self.formtabchanged)

        for item, data in readonlyvalues:
            self.readonlyCombo.addItem(item, data)

        self.loadwidgettypes()

        self.formLabelText.textChanged.connect(self.form_name_changed)
        self.layerCombo.currentIndexChanged.connect(self.layer_updated)

        self.fieldList.currentIndexChanged.connect(self._save_current_widget)
        self.nameText.textChanged.connect(self._save_current_widget)
        self.useablewidgets.currentIndexChanged.connect(self._save_current_widget)
        self.useablewidgets.currentIndexChanged.connect(self.swapwidgetconfig)

    def layer_updated(self, index):
        index = self.formlayers.index(index, 0)
        layer = index.data(Qt.UserRole)
        self.updatefields(layer)

    def form_name_changed(self, text):
        self.form.settings['label'] = self.formLabelText.text()
        self.treenode.emitDataChanged()

    def updatewidgetname(self, index):
        # Only change the edit text on name field if it's not already set to something other then the
        # field name.
        field = self.fieldsmodel.index(index, 0).data(QgsFieldModel.FieldNameRole)
        currenttext = self.nameText.text()
        foundfield = self.fieldsmodel.findfield(currenttext)
        if foundfield:
            self.nameText.setText(field)

    def opendefaultexpression(self):
        layer = self.form.QGISLayer
        dlg = QgsExpressionBuilderDialog(layer, "Create default value expression", self)
        text = self.defaultvalueText.text().strip('[%').strip('%]').strip()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.defaultvalueText.setText('[% {} %]'.format(dlg.expressionText()))

    def formtabchanged(self, index):
        def setformpreview(form):
            item = self.frame_2.layout().itemAt(0)
            if item and item.widget():
                item.widget().setParent(None)

            featureform = FeatureForm.from_form(form, form.settings, None, {})

            self.frame_2.layout().addWidget(featureform)

        if index == 1:
            self.form.settings['widgets'] = list(self.widgetmodel.widgets())
            setformpreview(self.form)

    def usedfields(self):
        """
        Return the list of fields that have been used by the the current form's widgets
        """
        for widget in self.currentform.widgets:
            yield widget['field']

    def openformfolder(self, url):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.form.folder))

    def loadwidgettypes(self):
        self.useablewidgets.blockSignals(True)
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
            self.useablewidgets.model().appendRow(item)
            self.widgetstack.addWidget(configwidget)
        self.useablewidgets.blockSignals(False)

    def setwidgetconfigvisiable(self, *args):
        haswidgets = self.widgetmodel.rowCount() > 0
        self.widgetConfigTabs.setVisible(haswidgets)

    def newwidget(self):
        """
        Create a new widget.  The default is a list.
        """
        widget = {}
        widget['widget'] = 'Text'
        # Grab the first field.
        widget['field'] = self.fieldsmodel.index(0, 0).data(QgsFieldModel.FieldNameRole)
        currentindex = self.userwidgets.currentIndex()
        currentitem = self.widgetmodel.itemFromIndex(currentindex)
        if currentitem and currentitem.iscontainor():
            parent = currentindex
        else:
            parent = currentindex.parent()
        index = self.widgetmodel.addwidget(widget, parent)
        self.userwidgets.setCurrentIndex(index)

    def removewidget(self):
        """
        Remove the selected widget from the widgets list
        """
        widget, index = self.currentuserwidget
        if index.isValid():
            self.widgetmodel.removeRow(index.row(), index.parent())

    def set_project(self, project, treenode):
        super(FormWidget, self).set_project(project, treenode)
        self.formlayers.setSelectLayers(self.project.selectlayers)
        form = self.treenode.form
        self.form = form
        self.setform(self.form)

    def updatefields(self, layer):
        """
        Update the UI with the fields for the selected layer.
        """
        self.fieldsmodel.setLayer(layer)

    def setform(self, form):
        """
        Update the UI with the currently selected form.
        """

        def getfirstlayer():
            index = self.formlayers.index(0, 0)
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
            self.userwidgets.setCurrentIndex(index)
            self.load_widget(index, None)

    def swapwidgetconfig(self, index):
        widgetconfig, _, _ = self.current_config_widget
        defaultvalue = widgetconfig.defaultvalue
        self.defaultvalueText.setText(defaultvalue)

        self.updatewidgetconfig({})

    def load_widget(self, index, last):
        """
        Update the UI with the config for the current selected widget.
        """
        self.fieldList.blockSignals(True)
        self.nameText.blockSignals(True)
        self.useablewidgets.blockSignals(True)

        if last:
            print "Save last widget"
            self._save_widget(last)

        print "Update with new widget"
        widget = index.data(Qt.UserRole)
        if not widget:
            self.fieldList.blockSignals(False)
            self.nameText.blockSignals(False)
            self.useablewidgets.blockSignals(False)
            return

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
        except IndexError:
            data = 'never'

        index = self.readonlyCombo.findData(data)
        self.readonlyCombo.setCurrentIndex(index)

        if not isinstance(default, dict):
            self.defaultvalueText.setText(default)
            self.defaultvalueText.setEnabled(True)
            self.expressionButton.setEnabled(True)
        else:
            # TODO Handle the more advanced default values.
            self.defaultvalueText.setText("Advanced default set in config")
            self.defaultvalueText.setEnabled(False)
            self.expressionButton.setEnabled(False)

        self.nameText.setText(name)
        self.requiredCheck.setChecked(required)
        self.savevalueCheck.setChecked(savevalue)
        self.hiddenCheck.setChecked(hidden)

        if field is not None:
            index = self.fieldList.findData(field.lower(), QgsFieldModel.FieldNameRole)
            if index > -1:
                self.fieldList.setCurrentIndex(index)
            else:
                self.fieldList.setEditText(field)

        index = self.useablewidgets.findText(widgettype)
        if index > -1:
            self.useablewidgets.setCurrentIndex(index)

        config = widget.get('config', {})
        self.updatewidgetconfig(config)

        self.fieldList.blockSignals(False)
        self.nameText.blockSignals(False)
        self.useablewidgets.blockSignals(False)

    @property
    def currentuserwidget(self):
        """
        Return the selected user widget.
        """
        index = self.userwidgets.currentIndex()
        return index.data(Qt.UserRole), index

    @property
    def current_config_widget(self):
        """
        Return the selected widget in the widget combo.
        """
        index = self.useablewidgets.currentIndex()
        index = self.possiblewidgetsmodel.index(index, 0)
        return index.data(Qt.UserRole), index, index.data(Qt.UserRole + 1)

    def updatewidgetconfig(self, config):
        configwidget, _, _ = self.current_config_widget
        self.setconfigwidget(configwidget, config)

    def setconfigwidget(self, configwidget, config):
        """
        Set the active config widget.
        """

        try:
            configwidget.widgetdirty.disconnect(self._save_current_widget)
        except TypeError:
            pass

        self.widgetstack.setCurrentWidget(configwidget)
        configwidget.setconfig(config)

        configwidget.widgetdirty.connect(self._save_current_widget)

    def _save_current_widget(self, *args):
        _, index = self.currentuserwidget
        self._save_widget(index)

    def _save_widget(self, index):
        widgetdata = self._get_widget_config()
        self.widgetmodel.setData(index, widgetdata, Qt.UserRole)

    def _get_widget_config(self):
        def current_field():
            row = self.fieldList.currentIndex()
            field = self.fieldsmodel.index(row, 0).data(QgsFieldModel.FieldNameRole)
            return field

        configwidget, _, widgettype = self.current_config_widget
        widget = {}
        widget['field'] = current_field()
        widget['default'] = self.defaultvalueText.text()
        widget['widget'] = widgettype
        widget['required'] = self.requiredCheck.isChecked()
        widget['rememberlastvalue'] = self.savevalueCheck.isChecked()
        widget['name'] = self.nameText.text()
        widget['read-only-rules'] = [self.readonlyCombo.itemData(self.readonlyCombo.currentIndex())]
        widget['hidden'] = self.hiddenCheck.isChecked()
        widget['config'] = configwidget.getconfig()
        return widget

    def write_config(self):
        self._save_current_widget()
        index = self.formlayers.index(self.layerCombo.currentIndex(), 0)
        layer = index.data(Qt.UserRole)
        self.form.settings['layer'] = layer.name()
        self.form.settings['type'] = self.formtypeCombo.currentText()
        self.form.settings['label'] = self.formLabelText.text()
        self.form.settings['widgets'] = list(self.widgetmodel.widgets())


class ProjectInfoWidget(ui_projectinfo.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(ProjectInfoWidget, self).__init__(parent)
        self.setupUi(self)
        self.titleText.textChanged.connect(self.updatetitle)

    def updatetitle(self, text):
        self.project.settings['title'] = text
        self.titleText.setText(text)

    def setsplash(self, splash):
        pixmap = QPixmap(splash)
        w = self.splashlabel.width()
        h = self.splashlabel.height()
        self.splashlabel.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

    def set_project(self, project, treenode):
        super(ProjectInfoWidget, self).set_project(project, treenode)
        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)
        self.setsplash(project.splash)
        self.versionText.setText(self.project.version)

    def write_config(self):
        title = self.titleText.text()
        description = self.descriptionText.toPlainText()
        version = str(self.versionText.text())

        settings = self.project.settings
        settings['title'] = title
        settings['description'] = description
        settings['version'] = version


class InfoNode(ui_infonode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(InfoNode, self).__init__(parent)
        self.setupUi(self)
        self.Editor.setLexer(QsciLexerSQL())
        self.Editor.setMarginWidth(0, 0)
        self.Editor.setWrapMode(QsciScintilla.WrapWord)
        self.layer = None
        self.message_label.setVisible(False)
        self.connectionCombo.currentIndexChanged.connect(self.update_panel_status)
        self.fromlayer_radio.toggled.connect(self.update_panel_status)
        self.thislayer_radio.toggled.connect(self.update_panel_status)
        self.connectionCombo.blockSignals(True)

    def update_panel_status(self, *args):
        if self.fromlayer_radio.isChecked():
            layer = self.connectionCombo.currentLayer()

        if self.thislayer_radio.isChecked():
            layer = self.treenode.layer

        source = layer.source()
        name = layer.dataProvider().name()
        if ".sqlite" in source or name == "mssql":
            self.queryframe.setEnabled(True)
            self.message_label.setVisible(False)
            return True
        else:
            self.queryframe.setEnabled(False)
            self.message_label.setVisible(True)
            return False

    def set_project(self, project, node):
        self.connectionCombo.blockSignals(False)
        super(InfoNode, self).set_project(project, node)
        self.layer = self.treenode.layer
        # uri = QgsDataSourceURI(self.layer.dataProvider().dataSourceUri())
        if not self.update_panel_status():
            pass

        infoblock = self.project.info_query(node.key, node.layer.name())
        caption = infoblock.get("caption", node.text())
        query = infoblock.get("query", "")
        connection = infoblock.get("connection", "from_layer")

        if connection == "from_layer":
            self.thislayer_radio.setChecked(True)
        else:
            layername = connection['layer']
            layer = utils.layer_by_name(layername)
            self.fromlayer_radio.setChecked(True)
            self.connectionCombo.setLayer(layer)

        self.caption_edit.setText(caption)
        self.Editor.setText(query)

    def write_config(self):
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        if self.fromlayer_radio.isChecked():
            layer = self.connectionCombo.currentLayer()
            connection = {"layer": layer.name()}
        else:
            connection = "from_layer"

        if self.Editor.text():
            infoconfig[self.treenode.key] = {
                "caption": self.caption_edit.text(),
                "query": self.Editor.text(),
                "connection": connection
            }
        else:
            try:
                del infoconfig[self.treenode.key]
            except KeyError:
                pass

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayerWidget(ui_layernode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(LayerWidget, self).__init__(parent)
        self.setupUi(self)

    def set_project(self, project, node):
        super(LayerWidget, self).set_project(project, node)
        self.layer = node.layer
        tools = self.project.layer_tools(self.layer)
        delete = 'delete' in tools
        capture = 'capture' in tools
        edit_attr = 'edit_attributes' in tools
        edit_geom = 'edit_geom' in tools
        self.capture_check.setChecked(capture)
        self.delete_check.setChecked(delete)
        self.editattr_check.setChecked(edit_attr)
        self.editgeom_check.setChecked(edit_geom)
        self.datasouce_label.setText(self.layer.publicSource())

    def write_config(self):
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        capture = self.capture_check.isChecked()
        delete = self.delete_check.isChecked()
        editattr = self.editattr_check.isChecked()
        editgoem = self.editgeom_check.isChecked()
        tools = []
        if capture:
            tools.append("capture")
        if delete:
            tools.append("delete")
        if editattr:
            tools.append("edit_attributes")
        if editgoem:
            tools.append("edit_geom")

        infoconfig['tools'] = tools

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayersWidget(ui_layersnode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(LayersWidget, self).__init__(parent)
        self.setupUi(self)

        self.selectlayermodel = CaptureLayersModel(watchregistry=True)
        self.selectlayerfilter = LayerTypeFilter(geomtypes=[])
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)
        self.selectlayermodel.dataChanged.connect(self.selectlayerschanged)

        self.selectLayers.setModel(self.selectlayerfilter)

    def selectlayerschanged(self):
        self.treenode.refresh()

    def set_project(self, project, node):
        super(LayersWidget, self).set_project(project, node)
        self.selectlayermodel.config = project.settings
        self.selectlayermodel.refresh()

