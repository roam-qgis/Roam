__author__ = 'Nathan.Woodrow'

import markdown
import uuid
import os
import shutil
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtCore import Qt, QUrl, QVariant, pyqtSignal
from qgis.PyQt.QtWidgets import QWidget, QComboBox, QGridLayout, QMenu, QToolButton, QFileDialog
from qgis.PyQt.QtGui import QPixmap, QStandardItem, QStandardItemModel, QIcon, QDesktopServices, QColor
from qgis.PyQt.Qsci import QsciLexerSQL, QsciScintilla

from qgis.core import QgsPalLabeling, QgsStyle, QgsMapLayer, Qgis, QgsProject, QgsExpression, QgsFeatureRequest, QgsWkbTypes
from qgis.gui import QgsExpressionBuilderDialog, QgsMapCanvas, QgsRendererPropertiesDialog, QgsLayerTreeMapCanvasBridge

from configmanager.ui.nodewidgets import (ui_layersnode, ui_layernode, ui_infonode, ui_projectinfo, ui_formwidget,
                                          ui_searchsnode, ui_searchnode, ui_mapwidget, ui_publishwidget)
from configmanager.models import (CaptureLayersModel, LayerTypeFilter, QgsFieldModel, WidgetsModel,
                                  QgsLayerModel, CaptureLayerFilter, SearchFieldsModel)
from configmanager.icons import widgeticon

from configmanager.events import ConfigEvents
import roam.editorwidgets
import configmanager.editorwidgets
from roam.api import FeatureForm, utils
from roam.utils import log

from configmanager.utils import openqgis, render_tample, openfolder, QGISNotFound
import roam.utils
from roam.dataaccess.database import Database

# ========= Imports to not break .ui widget files.
from configmanager.ui.widgets.datawidget import DataWidget
from configmanager.ui.widgets.publishwidget import PublishWidget
# ========= Imports to not break .ui widget files

from configmanager.ui.widgets.widgetbase import WidgetBase
from configmanager.widgetconfig import WidgetConfig
from configmanager.ui.nodewidgets import ui_eventwidget

readonlyvalues = [('Never', 'never'),
                  ('Always', 'always'),
                  ('When editing', 'editing'),
                  ('When inserting', 'insert')]

defaultevents = [('Capture Only', ['capture']),
                 ('Save Only', ['save']),
                 ('Capture and Save', ['capture', 'save'])]


class EventWidget(ui_eventwidget.Ui_Form, QWidget):
    removeItem = pyqtSignal(QWidget)

    def __init__(self, layer, model, parent=None):
        super(EventWidget, self).__init__(parent=None)
        self.setupUi(self)
        self.layer = layer
        self.model = model
        self.removeEvent.pressed.connect(self.remove)
        self.sourceFieldCombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.targetFieldCombo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.condtionTextButton.pressed.connect(self.add_expression_condition)
        self.newValueButton.pressed.connect(self.add_expression_newvalue)
        self.sourceFieldCombo.setModel(model)
        self.targetFieldCombo.setModel(model)
        self.eventCombo.setCurrentIndex(0)
        self.actionCombo.setCurrentIndex(0)
        self.newValueFrame.hide()
        self.actionCombo.currentIndexChanged.connect(self.update_controls)

    def update_controls(self, index):
        action = self.actionCombo.currentText()
        showframe = action.lower() == 'set value'
        self.newValueFrame.setVisible(showframe)

    def remove(self):
        self.removeItem.emit(self)

    def add_expression_newvalue(self):
        dlg = QgsExpressionBuilderDialog(self.layer, "Set expression for new value", self)
        text = self.newValueText.text()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.newValueText.setText(dlg.expressionText())

    def add_expression_condition(self):
        dlg = QgsExpressionBuilderDialog(self.layer, "Set condition expression", self)
        text = self.condtionText.text()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.condtionText.setText(dlg.expressionText())

    def set_data(self, data):
        if not data:
            return

        source = data['source']
        dest = data['target']
        action = data['action']
        event = data['event']
        condition = data['condition']
        value = data['value']

        sourcewidgetindex = self.model.indexFromId(source)
        destwidgetindex = self.model.indexFromId(dest)
        self.sourceFieldCombo.setCurrentIndex(sourcewidgetindex)
        self.targetFieldCombo.setCurrentIndex(destwidgetindex)
        index = self.actionCombo.findText(action)
        self.actionCombo.setCurrentIndex(index)
        index = self.eventCombo.findText(event)
        self.eventCombo.setCurrentIndex(index)
        self.condtionText.setText(condition)
        self.newValueText.setText(value)

    def get_data(self):
        sourcewidgetid = self.model.idFromIndex(self.sourceFieldCombo.currentIndex())
        destwidgetid = self.model.idFromIndex(self.targetFieldCombo.currentIndex())
        data = {}
        data['source'] = sourcewidgetid
        data['target'] = destwidgetid
        data['action'] = self.actionCombo.currentText()
        data['event'] = self.eventCombo.currentText()
        data['condition'] = self.condtionText.text()
        data['value'] = self.newValueText.text()
        return data



class PluginsWidget(WidgetBase):
    def __init__(self, parent=None):
        super(PluginsWidget, self).__init__(parent)


class PluginWidget(WidgetBase):
    def __init__(self, parent=None):
        super(PluginWidget, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.webpage = QWebView(self)
        self.layout().addWidget(self.webpage)

    def set_project(self, project, treenode):
        super(PluginWidget, self).set_project(project, treenode)
        self.webpage.setHtml("")
        pluginhome = treenode.pluginlocation
        readme = os.path.join(pluginhome, "README")
        if os.path.exists(readme):
            with open(readme) as f:
                data = f.read()
                self.webpage.setHtml(markdown.markdown(data))


class FormWidget(ui_formwidget.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(FormWidget, self).__init__(parent)
        self.setupUi(self)
        self.form = None

        self.iconlabel.mouseReleaseEvent = self.change_icon

        self._currentwidgetid = ''
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
        self.widgetmodel.rowsRemoved.connect(self.set_widget_config_state)
        self.widgetmodel.rowsInserted.connect(self.set_widget_config_state)
        self.widgetmodel.modelReset.connect(self.set_widget_config_state)

        self.addWidgetButton.pressed.connect(self.newwidget)
        self.addSectionButton.pressed.connect(self.add_section)
        self.removeWidgetButton.pressed.connect(self.removewidget)

        self.formfolderLabel.linkActivated.connect(self.openformfolder)
        self.expressionButton.clicked.connect(self.opendefaultexpression)
        self.expressionButton_2.clicked.connect(self.opendefaultexpression_advanced)

        self.fieldList.currentIndexChanged.connect(self.updatewidgetname)
        self.fieldwarninglabel.hide()
        self.formtab.currentChanged.connect(self.formtabchanged)

        for item, data in readonlyvalues:
            self.readonlyCombo.addItem(item, data)

        for item, data in defaultevents:
            self.defaultEventsCombo.addItem(item, data)

        self.loadwidgettypes()

        self.formLabelText.textChanged.connect(self.form_name_changed)
        self.newStyleCheck.stateChanged.connect(self.form_style_changed)
        self.layerCombo.currentIndexChanged.connect(self.layer_updated)

        # Gross but ok for now.
        self.blockWidgets = [
            self.fieldList,
            self.nameText,
            self.sectionNameText,
            self.useablewidgets,
            self.hiddenCheck,
            self.requiredCheck,
            self.readonlyCombo,
            self.defaultEventsCombo,
            self.defaultvalueText,
            self.defaultLayerCombo,
            self.defaultFieldCombo,
            self.defaultValueExpression,
            self.savevalueCheck
        ]

        for widget in self.blockWidgets:
            self._connect_save_event(widget)

        self.blockWidgetSignels(True)

        self.useablewidgets.currentIndexChanged.connect(self.swapwidgetconfig)

        menu = QMenu("Field Actions")
        action = menu.addAction("Auto add all fields")
        action.triggered.connect(self.auto_add_fields)

        self.addWidgetButton.setMenu(menu)
        self.addWidgetButton.setPopupMode(QToolButton.MenuButtonPopup)

        self.defaultLayerCombo.layerChanged.connect(self.defaultFieldCombo.setLayer)
        self.addEvent.pressed.connect(self.addEventItem)
        self.btnDeleteForm.pressed.connect(ConfigEvents.deleteForm.emit)

    def on_closing(self):
        self.blockWidgetSignels(True)

    def unload_project(self):
        self.blockWidgetSignels(True)

    def _connect_save_event(self, widget):
        if hasattr(widget, "textChanged"):
            widget.textChanged.connect(self._save_current_widget)
        if hasattr(widget, "currentIndexChanged"):
            widget.currentIndexChanged.connect(self._save_current_widget)
        if hasattr(widget, "stateChanged"):
            widget.stateChanged.connect(self._save_current_widget)

    def change_icon(self, *args):
        """
        Change the icon for the form
        """
        icon, selected = QFileDialog.getOpenFileName(self, "Select form icon image", filter="Images (*.png *.svg)")
        if not selected:
            return
        ext = os.path.splitext(icon)[1]
        shutil.copy(icon, os.path.join(self.form.folder, "icon" + ext))
        self.set_icon(self.form.icon)
        self.treenode.emitDataChanged()

    def set_icon(self, path):
        """
        Set the forms icon preview
        :param path: The path to icon.
        """
        pixmap = QPixmap(path)
        w = self.iconlabel.width()
        h = self.iconlabel.height()
        self.iconlabel.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

    def layer_updated(self, index):
        """
        Called when the forms layer has changed.
        :param index: The index of the new layer.
        """
        if not self.selected_layer:
            return

        self.updatefields(self.selected_layer)

    def form_style_changed(self, newstyle):
        """
        Called when the form style has changed from label-above style to label-beside style.
        :param newstyle: True if to use the new label-above style forms.
        """
        self.form.settings['newstyle'] = newstyle
        self.treenode.emitDataChanged()

    def form_name_changed(self, text):
        """
        Called when the forms name has changed. Also updates the tree view to reflect the new name.
        :param text: The new text of the label.
        :return:
        """
        self.form.settings['label'] = text
        self.treenode.emitDataChanged()

    def updatewidgetname(self, index):
        """
        Update the widget name if the field has changed. Doesn't change the name if it has been user set already.
        :param index: index of the new field.
        """
        # Only change the edit text on name field if it's not already set to something other then the
        # field name.
        field = self.fieldsmodel.index(index, 0).data(QgsFieldModel.FieldNameRole)
        currenttext = self.nameText.text()
        foundfield = self.fieldsmodel.findfield(currenttext)
        if foundfield:
            self.nameText.setText(field)

    def opendefaultexpression_advanced(self):
        """
        Open the default expression builder for setting advanced default values based on QGIS Expressions.
        """
        layer = self.form.QGISLayer
        dlg = QgsExpressionBuilderDialog(layer, "Create default value expression", self)
        text = self.defaultValueExpression.text()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.defaultValueExpression.setText(dlg.expressionText())

    def opendefaultexpression(self):
        """
        Open the default expression builder for setting default values based on QGIS Expressions.
        """
        layer = self.form.QGISLayer
        dlg = QgsExpressionBuilderDialog(layer, "Create default value expression", self)
        text = self.defaultvalueText.text().strip('[%').strip('%]').strip()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.defaultvalueText.setText('[% {} %]'.format(dlg.expressionText()))

    def formtabchanged(self, index):
        """
        Called when the tab widget changes tab.  Normally used to control when to render the form preview on demand.
        :param index: The index of the new tab.
        """
        # Don't generate the form preview if we are not on the preview tab.
        if index == 3:
            self.generate_form_preview()

    def generate_form_preview(self):
        """
        Create the form preview to show to the user.
        """
        form = self.form.copy()
        form.settings['widgets'] = list(self.widgetmodel.widgets())
        item = self.frame_2.layout().itemAt(0)
        if item and item.widget():
            item.widget().setParent(None)

        featureform = FeatureForm.from_form(form, form.settings, None, {})
        from roam import defaults
        defaultwidgets = form.widgetswithdefaults()
        layer = form.QGISLayer
        try:
            values = {}
            feature = next(layer.getFeatures())
            defaultvalues = defaults.default_values(defaultwidgets, feature, layer)
            values.update(defaultvalues)
            featureform.bindvalues(values)
        except StopIteration:
            pass

        self.frame_2.layout().addWidget(featureform)

    def usedfields(self):
        """
        Return the list of fields that have been used by the the current form's widgets
        """
        widgets = self.widgetmodel.widgets()
        for widget in widgets:
            if 'field' in widget:
                yield widget['field']

    def openformfolder(self, url):
        """
        Open the form folder using the OS file manager.
        :param url:
        :return:
        """
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.form.folder))

    def loadwidgettypes(self):
        """
        Load all supported widgets into the combobox for the form designer.
        :return:
        """
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
            item.setIcon(widgeticon(widgettype))
            self.useablewidgets.model().appendRow(item)
            self.widgetstack.addWidget(configwidget)
        self.useablewidgets.blockSignals(False)

    def set_widget_config_state(self, *args):
        """
        Enable or disable the widget config section based on widget count
        :param args: Unused.
        :return:
        """
        haswidgets = self.widgetmodel.rowCount() > 0
        self.widgetConfigTabs.setEnabled(haswidgets)

    def add_section(self):
        """
        Add a new widget section into the form. Widget sections can be used to group
        widgets on the form together.
        """
        currentindex = self.userwidgets.currentIndex()
        widget = {"widget": "Section",
                  "name": "default"}
        index = self.widgetmodel.addwidget(widget, currentindex.parent())
        self.userwidgets.setCurrentIndex(index)

    def newwidget(self, field=None):
        """
        Create a new widget. Tries to match the field type to the right kind of widget as a best guess.
        """
        mapping = {QVariant.String: "Text",
                   QVariant.Int: "Number",
                   QVariant.Double: "Number(Double)",
                   QVariant.ByteArray: "Image",
                   QVariant.Date: "Date",
                   QVariant.DateTime: "Date"}
        widget = {}
        if not field:
            field = self.fieldsmodel.index(0, 0).data(Qt.UserRole)
            if not field:
                return
            widget['field'] = field.name()
        else:
            widget['field'] = field.name()

        try:
            widget['widget'] = mapping[field.type()]
        except KeyError:
            widget['widget'] = 'Text'
        # Grab the first field.

        widget['name'] = field.name().replace("_", " ").title()

        currentindex = self.userwidgets.currentIndex()
        currentitem = self.widgetmodel.itemFromIndex(currentindex)
        if currentitem and currentitem.iscontainor():
            parent = currentindex
        else:
            parent = currentindex.parent()
        index = self.widgetmodel.addwidget(widget, parent)
        self.userwidgets.setCurrentIndex(index)

    def auto_add_fields(self):
        """
        Auto add all fields to the form config. Any missing fields will be added.
        """
        used = list(self.usedfields())
        for field in self.selected_layer.fields():
            if field.name().lower() in used:
                continue

            self.newwidget(field)

    def removewidget(self):
        """
        Remove the selected widget from the widgets list
        """
        widget, index = self.currentuserwidget
        if index.isValid():
            self.widgetmodel.removeRow(index.row(), index.parent())

    def set_project(self, project, treenode):
        """
        Set the project for this widget also sets the form from the tree node.

        :note: This method is called from the parent node when the page and widget is loaded.
        :param project: The current project.j
        :param treenode: The current tree node.  Can be used to signel a update back to the tree for it to update it
        self.
        """
        roam.utils.debug("FormWidget: Set Project")

        self.blockWidgetSignels(True)

        super(FormWidget, self).set_project(project, treenode)
        self.formlayers.setSelectLayers(self.project.selectlayers)
        form = self.treenode.form
        self.form = form
        self.setform(self.form)

        self.blockWidgetSignels(False)

    def blockWidgetSignels(self, blocking):
        for widget in self.blockWidgets:
            widget.blockSignals(blocking)

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
            """
            Get the first layer from the forms layer combo box
            """
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
            """
            Find the layer with the same name in the layer combobox widget
            """
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
        newstyleform = settings.setdefault('newstyle', True)
        self.set_icon(form.icon)

        self.formLabelText.setText(label)
        folderurl = "<a href='{path}'>{name}</a>".format(path=form.folder, name=os.path.basename(form.folder))
        self.formfolderLabel.setText(folderurl)
        self.newStyleCheck.setChecked(newstyleform)
        self.layerCombo.setCurrentIndex(layerindex.row())
        self.updatefields(layer)

        if formtype == "auto":
            formtype = "Auto Generated"
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
            # self.load_widget(index, None)

        for i in reversed(range(self.eventsLayout.count())):
            child = self.eventsLayout.itemAt(i)
            if child.widget() and isinstance(child.widget(), EventWidget):
                child = self.eventsLayout.takeAt(i)
                child.widget().deleteLater()

        events = settings.get('events', [])
        self.load_events(events)

        ## This has overhead so only do it when the tab is active.
        if self.formtab.currentIndex() == 3:
            self.generate_form_preview()

    def load_events(self, events):
        for event in events:
            self.addEventItem(data=event)

    def addEventItem(self, data=None):
        widget = EventWidget(self.form.QGISLayer, self.widgetmodel, self.eventsWidget)
        widget.removeItem.connect(self.removeEventItem)
        widget.set_data(data)
        self.eventsLayout.addWidget(widget)

    def removeEventItem(self, widget):
        child = self.eventsLayout.removeWidget(widget)
        widget.deleteLater()

    def swapwidgetconfig(self, index):
        widgetconfig, _, _ = self.current_config_widget
        defaultvalue = widgetconfig.defaultvalue
        self.defaultvalueText.setText(defaultvalue)

        self.updatewidgetconfig({})

    def load_widget(self, index, last):
        """
        Update the UI with the config for the current selected widget.
        """
        self.blockWidgetSignels(True)

        if last:
            roam.utils.debug("Saving last widget")
            self._save_widget(last)

        widget = index.data(Qt.UserRole)
        if not widget:
            self.blockWidgetSignels(False)
            return

        try:
            roam.utils.debug("Loading widget: {0}".format(widget['_id']))
        except KeyError:
            pass
        widgettype = widget['widget']
        if widgettype == "Section":
            self.propertiesStack.setCurrentIndex(1)
            self.sectionNameText.blockSignals(True)
            name = widget['name']
            self.sectionNameText.setText(name)
            self.sectionNameText.blockSignals(False)
            return
        else:
            self.propertiesStack.setCurrentIndex(0)

        widgetconfig = WidgetConfig.from_config(widget)

        field = widget['field']
        self._currentwidgetid = widget.setdefault('_id', str(uuid.uuid4()))
        required = widget.setdefault('required', False)
        savevalue = widget.setdefault('rememberlastvalue', False)
        name = widget.setdefault('name', field)
        default = widget.setdefault('default', '')
        readonly = widget.setdefault('read-only-rules', [])
        hidden = widget.setdefault('hidden', False)
        defaultevents = widget.setdefault('default_events', ['capture'])

        try:
            data = readonly[0]
        except IndexError:
            data = 'never'

        index = self.readonlyCombo.findData(data)
        self.readonlyCombo.setCurrentIndex(index)

        index = self.defaultEventsCombo.findData(defaultevents)
        self.defaultEventsCombo.setCurrentIndex(index)

        self.defaultValueExpression.setText("")
        self.defaultFieldCombo.setLayer(None)
        self.defaultFieldCombo.setLayer(None)

        if widgetconfig.default_type == WidgetConfig.DEFAULT_LAYER_VALUE:
            self.defaultTab.setCurrentIndex(1)
            layer = default['layer']
            # TODO Handle the case of many layer fall though with defaults
            # Not sure how to handle this in the UI just yet
            if isinstance(layer, list):
                layer = layer[0]
            else:
                defaultfield = default['field']
                expression = default['expression']
                self.logger.info(defaultfield)
                self.defaultValueExpression.setText(expression)
                self.logger.debug("Layer from name: {}".format(layer))
                layer = roam.api.utils.layer_by_name(layer)
                self.logger.debug(layer)
                self.defaultLayerCombo.setLayer(layer)
                self.defaultFieldCombo.setLayer(layer)
                self.defaultFieldCombo.setField(defaultfield)
        else:
            self.defaultTab.setCurrentIndex(0)
            self.defaultvalueText.setText(default)

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

        self.blockWidgetSignels(False)

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
        # roam.utils.debug("FormWidget: Save widget")
        if not self.project:
            return
        widgetdata = self._get_widget_config()
        try:
            roam.utils.debug("Saving widget {} in project {}".format(widgetdata['_id'], self.project.name))
        except KeyError:
            pass
        self.widgetmodel.setData(index, widgetdata, Qt.UserRole)

    def _get_default_config(self):
        if self.defaultTab.currentIndex() == 0:
            return self.defaultvalueText.text()
        else:
            default = {}
            default['layer'] = self.defaultLayerCombo.currentLayer().name()
            default['field'] = self.defaultFieldCombo.currentField()
            default['expression'] = self.defaultValueExpression.text()
            default['type'] = 'layer-value'
            return default

    def _get_widget_config(self):
        def current_field():
            row = self.fieldList.currentIndex()
            field = self.fieldsmodel.index(row, 0).data(QgsFieldModel.FieldNameRole)
            return field

        configwidget, _, widgettype = self.current_config_widget
        if self.propertiesStack.currentIndex() == 1:
            return {'name': self.sectionNameText.text(),
                    "widget": "Section"}

        widget = {}
        widget['field'] = current_field()
        widget[
            'default-type'] = WidgetConfig.DEFAULT_SIMPLE if self.defaultTab.currentIndex() == 0 else WidgetConfig.DEFAULT_LAYER_VALUE
        widget['default'] = self._get_default_config()
        widget['widget'] = widgettype
        widget['required'] = self.requiredCheck.isChecked()
        widget['rememberlastvalue'] = self.savevalueCheck.isChecked()
        widget['_id'] = self._currentwidgetid
        widget['name'] = self.nameText.text()
        widget['read-only-rules'] = [self.readonlyCombo.itemData(self.readonlyCombo.currentIndex())]
        widget['default_events'] = self.defaultEventsCombo.itemData(self.defaultEventsCombo.currentIndex())
        widget['hidden'] = self.hiddenCheck.isChecked()
        widget['config'] = configwidget.getconfig()
        return widget

    @property
    def selected_layer(self):
        index = self.formlayers.index(self.layerCombo.currentIndex(), 0)
        layer = index.data(Qt.UserRole)
        return layer

    def write_config(self):
        roam.utils.debug("Write form config")
        if not self.selected_layer:
            return

        self._save_current_widget()
        self.form.settings['layer'] = self.selected_layer.name()
        formtype = self.formtypeCombo.currentText()
        self.form.settings['type'] = "auto" if formtype == "Auto Generated" else formtype
        self.form.settings['label'] = self.formLabelText.text()
        self.form.settings['newstyle'] = self.newStyleCheck.isChecked()
        self.form.settings['widgets'] = list(self.widgetmodel.widgets())
        events = []
        for i in range(self.eventsLayout.count()):
            child = self.eventsLayout.itemAt(i)
            if child.widget() and isinstance(child.widget(), EventWidget):
                widget = child.widget()
                eventdata = widget.get_data()
                events.append(eventdata)
        self.form.settings['events'] = events


class ProjectInfoWidget(ui_projectinfo.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(ProjectInfoWidget, self).__init__(parent)
        self.setupUi(self)
        self.titleText.textChanged.connect(self.updatetitle)
        self.splashlabel.mouseReleaseEvent = self.change_splash
        self.btnAddLayers.pressed.connect(self.open_qgis)
        self.btnAddData.pressed.connect(self.open_data_folder)

    def open_data_folder(self):
        """
        Open the data folder of the project using the OS
        """
        path = os.path.join(self.project.folder, "_data")
        openfolder(path)

    def open_qgis(self):
        """
        Open a instance of QGIS to add new layers and config the project.
        """
        try:
            openqgis(self.project.projectfile)
        except QGISNotFound as ex:
            self.bar.pushMessage(ex.message, Qgis.Warning)

    def change_splash(self, event):
        """
        Open a file browser to load a new splash icon.
        """
        splash = QFileDialog.getOpenFileName(self, "Select splash image", filter="Images (*.png *.svg)")
        if not splash:
            return
        ext = os.path.splitext(splash)[1]
        shutil.copy(splash, os.path.join(self.project.folder, "splash" + ext))
        self.setsplash(self.project.splash)

    def updatetitle(self, text):
        """
        Called when the title text box changes and we need to update the config file
        :param text: The new text for the title.
        """
        self.project.settings['title'] = text

    def setsplash(self, splash):
        """
        Set the project image to the given image.
        :param splash: The path to the image to use as a the splash screen.
        """
        pixmap = QPixmap(splash)
        w = self.splashlabel.width()
        h = self.splashlabel.height()
        self.splashlabel.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

    def update_items(self):
        """
        Update the UI widgets form the current project.
        """
        self.titleText.setText(self.project.name)
        self.descriptionText.setPlainText(self.project.description)
        self.setsplash(self.project.splash)
        self.versionText.setText(str(self.project.version))
        self.saveVersionText.setText(str(self.project.save_version))

    def set_project(self, project, treenode):
        """
        Set the project for the current widget.
        :param project: The new active project
        :param treenode: The active tree node
        """
        super(ProjectInfoWidget, self).set_project(project, treenode)
        self.project.projectUpdated.connect(self.update_items)
        self.update_items()

    def write_config(self):
        """
        Wrtie the config for the widget back to the project config
        """
        title = self.titleText.text()
        description = self.descriptionText.toPlainText()

        settings = self.project.settings
        settings['title'] = title
        settings['description'] = description


class InfoNode(ui_infonode.Ui_Form, WidgetBase):
    """
    Info query node for a layer. Allows setting the SQL query if a layer is SQL Server or SQLite.
    """

    def __init__(self, parent=None):
        super(InfoNode, self).__init__(parent)
        self.setupUi(self)
        self.Editor.setLexer(QsciLexerSQL())
        self.Editor.setMarginWidth(0, 0)
        self.Editor.setWrapMode(QsciScintilla.WrapWord)
        self.connectionCombo.currentIndexChanged.connect(self.update_panel_status)
        self.fromlayer_radio.toggled.connect(self.update_panel_status)
        self.thislayer_radio.toggled.connect(self.update_panel_status)
        self.connectionCombo.blockSignals(True)
        self.testButton.pressed.connect(self.test_query)

    def update_panel_status(self, *args):
        """
        Update if the SQL panel is enabled or disable if the source is SQL Server or SQLite.
        """
        layer = self.layer

        if not layer:
            self.queryframe.setEnabled(False)
            return False

        source = layer.source()
        name = layer.dataProvider().name()

        if ".sqlite" in source or name == "mssql" and layer.isValid():
            keys = layer.pkAttributeList()
            fields = layer.fields()
            if keys:
                fieldnames = " + ".join(fields[key].name() for key in keys)
            elif fields.count() > 0:
                fieldnames = fields.at(0).name()
            else:
                fieldnames = ""

            self.keyColumnLabel.setText(fieldnames)
            self.queryframe.setEnabled(True)
            self.queryframe.show()
            return True
        else:
            self.keyColumnLabel.setText("")
            self.queryframe.setEnabled(False)
            self.queryframe.hide()
            return False

    @property
    def layer(self):
        if self.fromlayer_radio.isChecked():
            return self.connectionCombo.currentLayer()

        if self.thislayer_radio.isChecked():
            return self.treenode.layer

        return None

    def test_query(self):
        if not self.layer:
            return

        layer = self.layer
        db = Database.fromLayer(layer)
        try:
            if not self.mapKeyEdit.text():
                feature = next(layer.getFeatures())
                self.mapKeyEdit.setText(str(feature.id()))
            else:
                try:
                    mapkey = int(self.mapKeyEdit.text())
                    rq = QgsFeatureRequest().setFilterFid(mapkey)
                    feature = next(layer.getFeatures(rq))
                except ValueError:
                    self.attributesLabel.setText("")
                    self.previewGrid.setModel(None)
                    self.resultsLabel.setText("Error in mapkey. Map key is invalid. Should be a valid number")
                    return
        except StopIteration:
            self.attributesLabel.setText("")
            self.previewGrid.setModel(None)
            self.resultsLabel.setText("No features found. No results or map key not found in layer")
            return

        self.resultsLabel.setText("")

        dbkey = self.dbKeyEdit.text()

        attributes = utils.values_from_feature(feature, safe_names=True, ordered=True)
        attributes['mapkey'] = feature.id()
        attributes['dbkey'] = dbkey
        # Run the SQL text though the QGIS expression engine first.
        sql = self.Editor.text()
        sql = roam.api.utils.replace_expression_placeholders(sql, feature)
        results = db.querymodel(sql, **attributes)
        self.previewGrid.setModel(results)
        labelText = ""
        for key, value in attributes.items():
            labelText += "<br> {}: {}".format(key, value)
        print(labelText)
        self.attributesLabel.setText("Feature Attributes Used:<br>" + labelText)

    def set_project(self, project, node):
        """
        Set the project for the widget. Updates the selection query for the current widget..
        """
        self.connectionCombo.blockSignals(False)
        super(InfoNode, self).set_project(project, node)
        # uri = QgsDataSourceURI(self.layer.dataProvider().dataSourceUri())

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
        self.attributesLabel.setText("")
        self.previewGrid.setModel(None)
        self.resultsLabel.setText("")

        if not self.update_panel_status():
            pass

    def write_config(self):
        """
        Wrtie the config for the widget back to the project config
        """
        nodelayer = self.treenode.layer.name()
        self.project.settings.setdefault('selectlayerconfig', {}).setdefault(nodelayer, {})

        if self.fromlayer_radio.isChecked():
            layer = self.connectionCombo.currentLayer()

            connection = {"layer": layer.name()}
        else:
            connection = "from_layer"

        if self.Editor.text():
            config = {
                "caption": self.caption_edit.text(),
                "query": self.Editor.text(),
                "connection": connection,
                "type": "sql"
            }
            self.project.settings['selectlayerconfig'][nodelayer][self.treenode.key] = config
        else:
            try:
                del self.project.settings['selectlayerconfig'][nodelayer][self.treenode.key]
            except KeyError:
                pass


class LayerWidget(ui_layernode.Ui_Form, WidgetBase):
    """
    Select layer widget.
    """

    def __init__(self, parent=None):
        super(LayerWidget, self).__init__(parent)
        self.setupUi(self)

    def set_project(self, project, node):
        """
        Set the project for this widget. Updates the select layer config based on the project info
        for the layer.
        """
        roam.utils.debug("LayerWidget: Set Project")
        super(LayerWidget, self).set_project(project, node)
        self.layer = node.layer
        forms = self.project.forms
        self.inspection_form_combo.clear()
        self.inspection_form_combo.clear()
        for form in forms:
            self.inspection_form_combo.addItem(form.name)
        tools = self.project.layer_tools(self.layer)
        delete = 'delete' in tools
        capture = 'capture' in tools
        edit_attr = 'edit_attributes' in tools
        edit_geom = 'edit_geom' in tools
        inspection = 'inspection' in tools
        self.capture_check.setChecked(capture)
        self.delete_check.setChecked(delete)
        self.editattr_check.setChecked(edit_attr)
        self.editgeom_check.setChecked(edit_geom)
        self.inspection_check.setChecked(inspection)
        self.datasouce_label.setText(self.layer.publicSource())

        self.inspection_fieldmappings.clear()
        if inspection:
            config = tools['inspection']
            formindex = self.inspection_form_combo.findText(config['form'])
            self.inspection_form_combo.setCurrentIndex(formindex)
            for key, value in config['field_mapping'].items():
                self.inspection_fieldmappings.appendPlainText("{}, {}".format(key, value))
        else:
            self.inspection_form_combo.setCurrentIndex(0)
            self.inspection_fieldmappings.setPlainText("")

    def inspection_mappings(self):
        """
        Return the inspection config mapping.
        """
        if not self.inspection_fieldmappings.toPlainText():
            return {}
        text = self.inspection_fieldmappings.toPlainText().split('\n')
        mappings = {}
        for line in text:
            field1, field2 = line.split(',')
            mappings[field1] = field2.strip()
        return mappings

    def write_config(self):
        """
        Wrtie the config for the widget back to the project config
        """
        roam.utils.debug("Layer Widget: Write config")
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        capture = self.capture_check.isChecked()
        delete = self.delete_check.isChecked()
        editattr = self.editattr_check.isChecked()
        editgoem = self.editgeom_check.isChecked()
        inspection = self.inspection_check.isChecked()
        tools = []

        if capture:
            tools.append("capture")
        if delete:
            tools.append("delete")
        if editattr and not inspection:
            # Inspection tool will override the edit button so you can't have both
            tools.append("edit_attributes")
        if editgoem:
            tools.append("edit_geom")
        if inspection:
            inspectionitem = dict(inspection=dict(
                mode="Copy",
                form=self.inspection_form_combo.currentText(),
                field_mapping=self.inspection_mappings()
            ))
            tools.append(inspectionitem)

        infoconfig['tools'] = tools

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayersWidget(ui_layersnode.Ui_Form, WidgetBase):
    """
    Root widget for select layers config.
    """

    def __init__(self, parent=None):
        super(LayersWidget, self).__init__(parent)
        self.setupUi(self)

        self.selectlayermodel = CaptureLayersModel(watchregistry=True)
        self.selectlayerfilter = LayerTypeFilter(geomtypes=[])
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)
        self.selectlayermodel.dataChanged.connect(self.selectlayerschanged)

        self.selectLayers.setModel(self.selectlayerfilter)

    def selectlayerschanged(self):
        """
        Update the tree node if selection layers are added or removed.
        """
        self.treenode.refresh()

    def set_project(self, project, node):
        """
        Set the project for this widget. Updates the select layers config.
        """
        super(LayersWidget, self).set_project(project, node)
        self.selectlayermodel.config = project.settings
        self.selectlayermodel.refresh()


class LayerSearchWidget(ui_searchsnode.Ui_Form, WidgetBase):
    """
    Root widget for the search config UI. Nothing here at the moment.
    """

    def __init__(self, parent=None):
        super(LayerSearchWidget, self).__init__(parent)
        self.setupUi(self)

    def set_project(self, project, node):
        """
        Set the project for this widget.
        """
        super(LayerSearchWidget, self).set_project(project, node)


class LayerSearchConfigWidget(ui_searchnode.Ui_Form, WidgetBase):
    """
    Widget to handle setting which fields are enabled for searching on the selected layer.

    Auto adds the search plugin if not loaded as well as the columns for the current layer.
    """

    def __init__(self, parent=None):
        super(LayerSearchConfigWidget, self).__init__(parent)
        self.setupUi(self)

        self.fieldsmodel = SearchFieldsModel()
        self.fieldsview.setModel(self.fieldsmodel)

    def set_project(self, project, node):
        """
        Set the project for this widget.  Updates the config on the fields model.
        """
        super(LayerSearchConfigWidget, self).set_project(project, node)
        self.fieldsmodel.setLayer(node.layer)
        self.fieldsmodel.set_settings(project.settings)

    def write_config(self):
        """
        Wrtie the config for the widget back to the project config
        """
        layers = self.fieldsmodel.layerconfig
        if layers:
            plugins = self.project.settings.setdefault('plugins', [])
            if "search_plugin" not in plugins:
                plugins.append("search_plugin")
                self.project.settings['plugins'] = plugins
            config = self.project.settings.setdefault('search', {})
            config[self.treenode.layer.name()] = dict(columns=layers)


class MapWidget(ui_mapwidget.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(MapWidget, self).__init__(parent)
        self.setupUi(self)

        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.canvas.mapRenderer().setLabelingEngine(QgsPalLabeling())
        self.style = QgsStyle.defaultStyle()
        self.styledlg = None
        self.bridge = QgsLayerTreeMapCanvasBridge(QgsProject.instance().layerTreeRoot(), self.canvas)
        self.bridge.setAutoSetupOnFirstLayer(False)
        QgsProject.instance().writeProject.connect(self.bridge.writeProject)
        QgsProject.instance().readProject.connect(self.bridge.readProject)

        self.applyStyleButton.pressed.connect(self.apply_style)

    def apply_style(self):
        if self.styledlg:
            self.styledlg.apply()
            self.canvas.refresh()

    def set_project(self, project, treenode):
        red = QgsProject.instance().readNumEntry("Gui", "/CanvasColorRedPart", 255)[0]
        green = QgsProject.instance().readNumEntry("Gui", "/CanvasColorGreenPart", 255)[0]
        blue = QgsProject.instance().readNumEntry("Gui", "/CanvasColorBluePart", 255)[0]
        myColor = QColor(red, green, blue)
        self.canvas.setCanvasColor(myColor)
        if hasattr(treenode, "layer"):
            layer = treenode.layer
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QgsWkbTypes.NoGeometry:
                self.stackedWidget.setCurrentIndex(0)
            self.set_style_widget(treenode.layer)
            self.stackedWidget.setCurrentIndex(1)
        else:
            self.loadmap(project)
            self.stackedWidget.setCurrentIndex(0)

    def set_style_widget(self, layer):
        if self.styledlg:
            widget = self.styleWidget.layout().removeWidget(self.styledlg)

        if layer.type() == QgsMapLayer.VectorLayer:
            self.styledlg = QgsRendererPropertiesDialog(layer, self.style, True)
        else:
            # TODO Nothing else is supported yet.
            return

        # self.styledlg.setStyleSheet(roam_style.appstyle())
        self.styledlg.setParent(self)
        # TODO Only in 2.12
        # self.styledlg.setMapCanvas(self.canvas)
        self.styleWidget.layout().addWidget(self.styledlg)

    def loadmap(self, project):
        """
        Load the map into the canvas widget of config manager.
        """

        # Refresh will stop the canvas timer
        # Repaint will redraw the widget.
        self.canvas.refresh()
        self.canvas.repaint()

        missing = project.missing_layers
        layers = QgsProject.instance().mapLayers().values()
        proj = self.canvas.mapSettings().destinationCrs().authid()
        html = render_tample("projectinfo", projection=proj,
                             layers=layers,
                             missinglayers=missing,
                             file=project.projectfile)
        self.textMapReport.setHtml(html)
