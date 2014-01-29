import os

from functools import partial

from PyQt4.QtGui import QComboBox

from qgis.core import QgsMapLayer

from admin_plugin.models import QgsLayerModel,QgsFieldModel
from admin_plugin.editorwidgets.core import WidgetFactory, ConfigWidget
from admin_plugin import create_ui

widget, base = create_ui(os.path.join("editorwidgets","uifiles",'listwidget_config.ui'))

class ListWidgetConfig(widget, ConfigWidget):
    def __init__(self, layer, field, parent=None):
        super(ListWidgetConfig, self).__init__(layer, field, parent)
        self.setupUi(self)

        self.layerRadio.clicked.connect(partial(self.stackedWidget.setCurrentIndex, 0))
        self.listRadio.clicked.connect(partial(self.stackedWidget.setCurrentIndex, 1))

        self.layermodel = QgsLayerModel()
        self.layermodel.layerfilter = [QgsMapLayer.VectorLayer]
        self.layermodel.updateLayerList()

        self.fieldmodel = QgsFieldModel()

        self.layerCombo.setModel(self.layermodel)
        self.keyCombo.setModel(self.fieldmodel)
        self.valueCombo.setModel(self.fieldmodel)

        self.fieldmodel.setLayerFilter(self.layerCombo.view().selectionModel())
        self.fieldmodel.setLayerFilter(self.layerCombo.view().selectionModel())

    def widgetchanged(self):
        self.allownull = self.allownullCheck.isChecked()
        self.orderby = self.orderbyCheck.isChecked()
        self.listtype = 'layer'
        self.list = []
        self.layer = None
        self.key = None
        self.value = None
        self.filter = None
        if self.listRadio.isChecked():
            self.listtype = 'list'
            self.list = [item for item in self.listText.toPlainText().split('\n')]
        else:
            self.layer = self.layerCombo.currentText()
            index_key = self.keyCombo.view().currentIndex()
            index_value = self.valueCombo.view().currentIndex()
            fieldname_key = self.fieldmodel.data(index_key, QgsFieldModel.FieldNameRole)
            fieldname_value = self.fieldmodel.data(index_value, QgsFieldModel.FieldNameRole)
            self.key = fieldname_key
            self.value = fieldname_value
            self.filter = self.filterText.toPlainText()
        self.widgetdirty.emit()

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

    def setconfig(self, config):
        self.blockSignals(True)
        self.allownull = config['allownull']
        self.orderby = config['orderbyvalue']
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
            layer = subconfig.get('layer', None)
            key = subconfig.get('key', None)
            value = subconfig.get('value', None)
            filter = subconfig.get('filter', None)
            index = self.layermodel.findlayer(layer)
            if index:
                self.layerCombo.view().setCurrentIndex(index)
                self.layerCombo.setCurrentIndex(index.row())

            keyindex = self.fieldmodel.findfield(key)
            if keyindex:
                self.keyCombo.view().setCurrentIndex(keyindex)
                self.keyCombo.setCurrentIndex(keyindex.row())

            valueindex = self.fieldmodel.findfield(value)
            if valueindex:
                self.valueCombo.view().setCurrentIndex(valueindex)
                self.valueCombo.setCurrentIndex(valueindex.row())

            self.filterText.setPlainText(filter)

        self.allownullCheck.setChecked(config['allownull'])
        self.orderbyCheck.setChecked(config['orderbyvalue'])
        self.blockSignals(False)

factory = WidgetFactory("List", None, ListWidgetConfig)
factory.description = "Select an item from a predefined list"
factory.icon = ':/icons/list'
