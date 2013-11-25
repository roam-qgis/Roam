import os
import collections

from string import Template
from collections import OrderedDict

from PyQt4.QtGui import (QImageReader, QWidget, QFrame, QDialog)

from PyQt4.QtCore import (Qt, QUrl, 
                          QDate,
                          QDateTime, QTime, QPoint, QSize)
from PyQt4.QtWebKit import QWebPage

from qgis.core import (QgsExpression, QgsFeature, 
                       QgsMapLayer)

from qmap import utils
from qmap.htmlviewer import updateTemplate, openimage
from qmap.uifiles import (infodock_widget, infodock_base)

import pkgutil
htmlpath = os.path.join(os.path.dirname(__file__), "info.html")

with open(htmlpath) as f:
    template = Template(f.read())


class InfoDock(infodock_widget, QWidget):
    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        self.results = collections.defaultdict(list)
        self.layerList.currentIndexChanged.connect(self.layerIndexChanged)
        self.featureList.currentIndexChanged.connect(self.featureIndexChanged)
        self.attributesView.linkClicked.connect(openimage)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

    def showEvent(self, event):
        self.resize(QSize(self.geometry().width(), self.parent().geometry().size().height()))
        topright = self.parent().geometry().topRight()
        self.move(topright - QPoint(self.geometry().width(), 0))

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
        if layer.type() == QgsMapLayer.RasterLayer:
            return
        self.addLayer(layer)
        utils.log(result.mFeature.id())
        self.results[layer].append(QgsFeature(result.mFeature))
        
    def update(self, layer, feature):
        global image
        images = {}
        fields = [field.name() for field in feature.fields()]
        data = OrderedDict()

        items = []
        for field, value in zip(fields, feature.attributes()):
            data[field] = value
            item = "<tr><th>{0}</th> <td>${{{0}}}</td></tr>".format(field)
            items.append(item)
        rowtemple = Template(''.join(items))
        rowshtml = updateTemplate(data, rowtemple)
        info = {}
        info['TITLE'] = layer.name()
        info['ROWS'] = rowshtml
        html = updateTemplate(info, template)
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
