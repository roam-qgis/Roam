from PyQt4.QtGui import QTableWidgetItem
from PyQt4.QtCore import Qt

from uifiles import (infodock_widget, infodock_base)

class InfoDock(infodock_widget, infodock_base):
    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        
    def addResult(self, result):
        layer = result.mLayer
        self.addLayer(layer)
        
        feature = result.mFeature
        
        fields = [field.name() for field in feature.fields()]
        data = dict(zip(fields, feature.attributes()))
        
        self.attributeTable.setColumnCount(1)
        self.attributeTable.setHorizontalHeaderLabels(['Value'])
        
        self.attributeTable.setRowCount(len(data))
        for key, value in data.iteritems():
            row = self.attributeTable.rowCount() + 1
            self.attributeTable.insertRow(row)
            rowitem = QTableWidgetItem(str(key))
            valueitem = QTableWidgetItem(str(value))
            
            self.attributeTable.setHorizontalHeaderItem(row, rowitem)
            self.attributeTable.setItem(row, 1, valueitem)
            
    def clearResults(self):
        self.layerList.clear()
        self.attributeTable.clear()
          
    def addLayer(self, layer):
        self.layerList.addItem(layer.name())
        