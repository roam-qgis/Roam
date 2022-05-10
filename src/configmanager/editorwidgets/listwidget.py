from functools import partial
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsMapLayer
from qgis.gui import QgsExpressionBuilderDialog

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_listwidget_config import Ui_Form
from configmanager.models import QgsLayerModel, QgsFieldModel
from roam.api.utils import layer_by_name


class ListWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Select an item from a predefined list'

    def __init__(self, parent=None):
        super(ListWidgetConfig, self).__init__(parent)
        self.setupUi(self)

        self.allownull = False
        self.orderby = False

        self.orderbyCheck.hide()

        self.layerRadio.clicked.connect(partial(self.stackedWidget.setCurrentIndex, 0))
        self.listRadio.clicked.connect(partial(self.stackedWidget.setCurrentIndex, 1))

        self.layermodel = QgsLayerModel(watchregistry=False)
        self.layermodel.layerfilter = [QgsMapLayer.VectorLayer]

        self.fieldmodel = QgsFieldModel()

        self.blockSignals(True)
        self.layerCombo.setModel(self.layermodel)
        self.keyCombo.setModel(self.fieldmodel)
        self.valueCombo.setModel(self.fieldmodel)
        self.sortCombo.setModel(self.fieldmodel)
        self.filterButton.pressed.connect(self.define_filter)

        self.fieldmodel.setLayerFilter(self.layerCombo.view().selectionModel())
        self.reset()
        self.blockSignals(False)

    def define_filter(self):
        layer = self.layerCombo.currentText()
        if not layer:
            return
        layer = layer_by_name(layer)
        dlg = QgsExpressionBuilderDialog(layer, "List filter", self)
        text = self.filterText.toPlainText()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.filterText.setPlainText(dlg.expressionText())

    def reset(self):
        self.listtype = 'layer'
        self.listText.setPlainText('')
        self.orderby = False
        self.allownull = False
        self.filterText.setPlainText('')
        self.layerCombo.setCurrentIndex(-1)
        self.keyCombo.setCurrentIndex(-1)
        self.valueCombo.setCurrentIndex(-1)
        self.sortCombo.setCurrentIndex(-1)

    def widgetchanged(self):
        self.widgetdirty.emit(self.getconfig())

    @property
    def allownull(self):
        return self.allownullCheck.isChecked()

    @allownull.setter
    def allownull(self, value):
        self.allownullCheck.setChecked(value)

    @property
    def orderby(self):
        return self.orderbyCheck.isChecked()

    @orderby.setter
    def orderby(self, value):
        self.orderbyCheck.setChecked(value)

    @property
    def list(self):
        return [item for item in self.listText.toPlainText().split('\n')]

    @property
    def filter(self):
        return self.filterText.toPlainText()

    @property
    def sortAsNumber(self):
        return self.sortByAsNumberCheck.isChecked()

    @property
    def sort_by(self):
        if self.sortByValue.isChecked():
            index_key = self.fieldmodel.index(self.sortCombo.currentIndex(), 0)
            fieldname_key = self.fieldmodel.data(index_key, QgsFieldModel.FieldNameRole)
            return fieldname_key
        return "default"

    @property
    def layer(self):
        return self.layerCombo.currentText()

    @property
    def key(self):
        index_key = self.fieldmodel.index(self.keyCombo.currentIndex(), 0)
        fieldname_key = self.fieldmodel.data(index_key, QgsFieldModel.FieldNameRole)
        return fieldname_key

    @property
    def value(self):
        index_value = self.fieldmodel.index(self.valueCombo.currentIndex(), 0)
        return self.fieldmodel.data(index_value, QgsFieldModel.FieldNameRole)

    def getconfig(self):
        config = {}
        config['allownull'] = self.allownull
        config['orderbyvalue'] = self.orderby
        if self.layerRadio.isChecked():
            subconfig = {}
            # TODO Grab the data here and not just the text
            subconfig['layer'] = self.layer
            subconfig['key'] = self.key
            subconfig['value'] = self.value
            subconfig['filter'] = self.filter
            subconfig['sort_by'] = self.sort_by
            subconfig['sort_by_as_number'] = self.sortAsNumber
            config['layer'] = subconfig
        else:
            config['list'] = {}
            config['list']['items'] = self.list
        return config

    def blockSignals(self, bool):
        for child in self.findChildren(QWidget):
            child.blockSignals(bool)

        super(ListWidgetConfig, self).blockSignals(bool)

    def setconfig(self, config):
        self.blockSignals(True)
        self.allownull = config.get('allownull', True)
        self.orderby = config.get('orderbyvalue', False)

        # Clear the widgets
        self.listText.setPlainText('')
        self.keyCombo.clear()
        self.valueCombo.clear()
        self.sortCombo.clear()
        self.filterText.clear()
        self.layermodel.refresh()

        # Rebind all the values
        if 'list' in config:
            subconfig = config.get('list', {})
            self.listRadio.setChecked(True)
            self.stackedWidget.setCurrentIndex(1)
            listitems = subconfig.get('items', [])
            itemtext = '\n'.join(listitems)
            self.listText.setPlainText(itemtext)
        else:
            self.layerRadio.setChecked(True)
            self.stackedWidget.setCurrentIndex(0)
            subconfig = config.get('layer', {})
            layer = subconfig.get('layer', '') or ''
            key = subconfig.get('key', '') or ''
            sortBy = subconfig.get('sort_by', 'default') or 'default'
            sortByAsNumber = subconfig.get('sort_by_as_number', False) or False
            value = subconfig.get('value', '') or ''
            filter = subconfig.get('filter', None)
            index = self.layerCombo.findData(layer, Qt.DisplayRole)
            if index > -1:
                self.layerCombo.setCurrentIndex(index)

            index = self.layermodel.index(index, 0)
            self.fieldmodel.updateLayer(index, None)

            keyindex = self.keyCombo.findData(key.lower(), QgsFieldModel.FieldNameRole)
            if keyindex > -1:
                self.keyCombo.setCurrentIndex(keyindex)

            valueindex = self.valueCombo.findData(value.lower(), QgsFieldModel.FieldNameRole)
            if valueindex > -1:
                self.valueCombo.setCurrentIndex(valueindex)

            self.sortByAsNumberCheck.setChecked(sortByAsNumber)

            if sortBy == "default":
                self.sortDefault.setChecked(True)
            else:
                self.sortByValue.setChecked(True)
                sortIndex = self.sortCombo.findData(sortBy.lower(), QgsFieldModel.FieldNameRole)
                if sortIndex > -1:
                    self.sortCombo.setCurrentIndex(sortIndex)

            self.filterText.setPlainText(filter)

        self.allownullCheck.setChecked(self.allownull)
        self.orderbyCheck.setChecked(self.orderby)
        self.blockSignals(False)
