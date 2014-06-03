import os

from functools import partial

from PyQt4.QtGui import QWidget
from PyQt4.QtCore import Qt
from qgis.core import QgsMapLayer

from configmanager.models import QgsLayerModel, QgsFieldModel
from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_listwidget_config import Ui_Form


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

        self.fieldmodel.setLayerFilter(self.layerCombo.view().selectionModel())
        self.reset()
        self.blockSignals(False)

    def reset(self):
        self.listtype = 'layer'
        self.list = []
        self.layer = None
        self.key = None
        self.value = None
        self.filter = None

    def widgetchanged(self):
        self.reset()
        self.allownull = self.allownullCheck.isChecked()
        self.orderby = self.orderbyCheck.isChecked()
        if self.listRadio.isChecked():
            self.listtype = 'list'
            self.list = [item for item in self.listText.toPlainText().split('\n')]
        else:
            self.layer = self.layerCombo.currentText()
            index_key = self.fieldmodel.index(self.keyCombo.currentIndex(), 0)
            index_value = self.fieldmodel.index(self.valueCombo.currentIndex(), 0)
            fieldname_key = self.fieldmodel.data(index_key, QgsFieldModel.FieldNameRole)
            fieldname_value = self.fieldmodel.data(index_value, QgsFieldModel.FieldNameRole)
            self.key = fieldname_key
            self.value = fieldname_value
            self.filter = self.filterText.toPlainText()

        self.widgetdirty.emit(self.getconfig())

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

        #Clear the widgets
        self.listText.setPlainText('')
        self.keyCombo.clear()
        self.valueCombo.clear()
        self.filterText.clear()
        self.layermodel.refresh()

        # Rebind all the values
        if 'list' in config:
            subconfig = config.get('list', {})
            self.listRadio.setChecked(True)
            self.stackedWidget.setCurrentIndex(1)
            self.list = subconfig.get('items', [])
            itemtext = '\n'.join(self.list)
            self.listText.setPlainText(itemtext)
        else:
            self.layerRadio.setChecked(True)
            self.stackedWidget.setCurrentIndex(0)
            subconfig = config.get('layer', {})
            layer = subconfig.get('layer', '') or ''
            key = subconfig.get('key', '') or ''
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

            self.filterText.setPlainText(filter)

        self.allownullCheck.setChecked(self.allownull)
        self.orderbyCheck.setChecked(self.orderby)
        self.blockSignals(False)

