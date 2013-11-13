import os
from functools import partial

from PyQt4.QtCore import pyqtSignal, pyqtSlot, QPyNullVariant
from PyQt4.QtGui import QWidget, QGridLayout, QComboBox

from qgis.core import QgsMessageLog

from qmap.editorwidgets.core import WidgetFactory, WidgetsRegistry, EditorWidget

def nullcheck(value):
    if isinstance(value, QPyNullVariant):
        return None
    else:
        return value

class ListWidget(EditorWidget):
    def __init__(self, layer, field, widget, parent=None):
        super(ListWidget, self).__init__(layer, field, widget, parent)

    def createWidget(self, parent):
        return QComboBox(parent)

    def initWidget(self, widget):
        print "initWidget"
        if 'list' in self.config:
            listconfig = self.config['list']
            self.items = listconfig['items']
            for item in self.items:
                parts = item.split(';')
                data = parts[0]
                try:
                    desc = parts[1]
                except IndexError:
                    desc = data

                widget.addItem(desc, data)

    def setvalue(self, value):
        value = nullcheck(value)
        print "Set Value {}".format(value)
        index = self.widget.findData(value)
        if index == -1 and self.widget.isEditable():
            if value is None and not self.config['allownull']:
                return

            self.widget.addItem(value)
            index = self.widget.count() - 1
        print index
        self.widget.setCurrentIndex(index)

    def value(self):
        index = self.widget.currentIndex()
        value = self.widget.itemData(index)
        print value
        if value is None and self.widget.isEditable():
            return self.widget.currentText()

        return value

factory = WidgetFactory("List", ListWidget, None)
