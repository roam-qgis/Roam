import os
import collections

from PyQt4.QtGui import QTableWidgetItem
from PyQt4.QtCore import Qt, QUrl

from qgis.core import QgsExpression, QgsFeature

import utils

from uifiles import (infodock_widget, infodock_base)

htmlpath = os.path.join(os.path.dirname(__file__) , "info.html")

with open(htmlpath) as f:
    template = f.read()

class InfoDock(infodock_widget, infodock_base):
    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        self.results = collections.defaultdict(list)
        self.layerList.currentIndexChanged.connect(self.layerIndexChanged)
        self.featureList.currentIndexChanged.connect(self.featureIndexChanged)
        
    def featureIndexChanged(self, index):
        feature = self.featureList.itemData(index)
        layer = self.layerList.itemData(self.layerList.currentIndex())
        if not feature:
            return 
        
        self.update(layer, feature)
        
    def layerIndexChanged(self, index):
        self.featureList.clear()
        layer = self.layerList.itemData(index)
        if not layer:
            return
        
        features = self.results[layer]
        utils.log(features)
        index = layer.fieldNameIndex(layer.displayField())
        for feature in features:
            if index < 0:
                display = QgsExpression.replaceExpressionText( layer.displayField(), feature, layer )
            else:
                display = feature[index]
            self._addFeature(str(display), feature)
                     
    def _addFeature(self, display, feature):
        self.featureList.addItem(display, feature)
        
    def setResults(self, results):
        self.clearResults()
        for result in results:
            self._addResult(result)
        self.layerIndexChanged(0)
        self.featureIndexChanged(0)
            
    def _addResult(self, result):
        layer = result.mLayer
        self.addLayer(layer)
        utils.log(result.mFeature.id())
        self.results[layer].append(QgsFeature(result.mFeature))
        
    def update(self, layer, feature):
        fields = [field.name() for field in feature.fields()]
        data = dict(zip(fields, feature.attributes()))
        items = []
        for key, value in data.iteritems():
            item = "<tr><th>{}</th> <td>{}</td></tr>".format(key, value)
            items.append(item)
            
        rows = ''.join(items)
        html = template.format(TITLE=layer.name(), ROWS=rows)
        base = os.path.dirname(os.path.abspath(__file__))
        baseurl = QUrl.fromLocalFile(base + '\\')
        self.attributesView.setHtml(html, baseurl)
        
    def clearResults(self):
        self.results.clear()
        self.layerList.clear()
        self.featureList.clear()
        self.attributesView.setHtml('')
          
    def addLayer(self, layer):
        name = layer.name()
        if self.layerList.findData(layer) == -1:
            self.layerList.addItem(name, layer)