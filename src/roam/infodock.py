import os
import collections

from string import Template
from collections import OrderedDict

from PyQt4.QtGui import (QImageReader, QWidget, QFrame, QDialog)

from PyQt4.QtCore import (Qt, QUrl, 
                          QDate,
                          QDateTime, QTime,
                          QPoint, QSize,
                          QEvent, pyqtSignal)
from PyQt4.QtWebKit import QWebPage

from qgis.core import (QgsExpression, QgsFeature, 
                       QgsMapLayer)

from roam import utils
from roam.flickwidget import FlickCharm
from roam.htmlviewer import updateTemplate, openimage
from roam.uifiles import (infodock_widget, infodock_base)

import pkgutil
htmlpath = os.path.join(os.path.dirname(__file__), "info.html")

with open(htmlpath) as f:
    template = Template(f.read())


class InfoDock(infodock_widget, QWidget):
    requestopenform = pyqtSignal(object, QgsFeature)
    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        self.forms = {}
        self.selection = (None, None)
        self.charm = FlickCharm()
        self.charm.activateOn(self.attributesView)
        self.results = collections.defaultdict(list)
        self.layerList.currentIndexChanged.connect(self.layerIndexChanged)
        self.featureList.currentIndexChanged.connect(self.featureIndexChanged)
        self.attributesView.linkClicked.connect(openimage)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.parent().installEventFilter(self)
        self.editButton.pressed.connect(self.openform)

    def openform(self):
        layer, feature = self.selection
        forms = self.forms[layer.name()]
        form = forms[0]
        self.requestopenform.emit(form, feature)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.resize(self.width(), self.parent().height())
            self.move(self.parent().width() - self.width() -1, 1)

        return self.parent().eventFilter(object, event)

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
        
    def setResults(self, results, forms):
        self.clearResults()
        self.forms = forms
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
        edittools = len(self.forms[layer.name()]) > 0
        self.editButton.setVisible(edittools)
        self.moveButton.setVisible(edittools)
        self.selection = layer, feature

    def clearResults(self):
        self.results.clear()
        self.layerList.clear()
        self.featureList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.moveButton.setVisible(False)
          
    def addLayer(self, layer):
        name = layer.name()
        if self.layerList.findData(layer) == -1:
            self.layerList.addItem(name, layer)
