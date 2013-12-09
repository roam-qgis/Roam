import os
import collections

from string import Template
from collections import OrderedDict

from PyQt4.QtGui import (QImageReader, QWidget, QFrame, QDialog, QIcon, QSortFilterProxyModel)

from PyQt4.QtCore import (Qt, QUrl, 
                          QDate,
                          QDateTime, QTime,
                          QPoint, QSize,
                          QEvent, pyqtSignal,
                          )

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
    featureupdated = pyqtSignal(object, object, list)
    resultscleared = pyqtSignal()

    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        self.forms = {}
        self.charm = FlickCharm()
        self.charm.activateOn(self.attributesView)
        self.results = collections.defaultdict(list)
        self.layerList.currentIndexChanged.connect(self.layerIndexChanged)
        self.featureList.currentIndexChanged.connect(self.featureIndexChanged)
        self.attributesView.linkClicked.connect(openimage)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.grabGesture(Qt.SwipeGesture)
        self.setAttribute(Qt.WA_AcceptTouchEvents)
        self.editButton.pressed.connect(self.openform)

    def close(self):
        self.clearResults()
        super(InfoDock, self).close()

    def event(self, event):
        if event.type() == QEvent.Gesture:
            gesture = event.gesture(Qt.SwipeGesture)
            if gesture:
                self.pagenext()
        return QWidget.event(self, event)

    @property
    def selection(self):
        layer = self.layerList.itemData(self.layerList.currentIndex())
        feature = self.featureList.itemData(self.featureList.currentIndex())
        return layer, feature

    def openform(self):
        layer, feature = self.selection
        forms = self.forms[layer.name()]
        form = forms[0]
        self.requestopenform.emit(form, feature)

    def pagenext(self):
        index = self.featureList.currentIndex() + 1
        if index > self.featureList.count():
            index = 0
        self.featureList.setCurrentIndex(index)

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
        self.results = results
        for layer, features in results.iteritems():
            if features:
                self._addResult(layer, features)

        self.layerList.setCurrentIndex(0)

    def _addResult(self, layer, features):
        self.addLayer(layer)
        self.results[layer] = features
        
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
        #self.moveButton.setVisible(edittools)
        self.featureupdated.emit(layer, feature, self.results[layer])

    def clearResults(self):
        self.results.clear()
        self.layerList.clear()
        self.featureList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.moveButton.setVisible(False)
        self.resultscleared.emit()
          
    def addLayer(self, layer):
        name = layer.name()
        if self.layerList.findData(layer) == -1:
            forms = self.forms.get(name, None)
            icon = QIcon()
            if forms:
                icon = QIcon(forms[0].icon)
            self.layerList.addItem(icon, name, layer)
