import os
import collections

from string import Template
from collections import OrderedDict

from PyQt4.QtGui import (QPixmap,
                         QImageReader)

from PyQt4.QtCore import (Qt, QUrl, 
                          QByteArray, QDate,
                          QDateTime, QTime)
from PyQt4.QtWebKit import QWebPage

from qgis.core import (QgsExpression, QgsFeature, 
                       QgsMapLayer)

import utils

from uifiles import (infodock_widget, infodock_base)

htmlpath = os.path.join(os.path.dirname(__file__) , "info.html")

images = {}
formats = [f.data() for f in QImageReader.supportedImageFormats()]

with open(htmlpath) as f:
    template = Template(f.read())
    
def image_handler(key, value, **kwargs):
    imageblock = '''
                    <a href="{}" class="thumbnail">
                      <img width="200" height="200" src="{}"\>
                    </a>'''
    
    imagetype = kwargs.get('imagetype', 'base64' )
    global images
    images[key] = (value, imagetype)
    if imagetype == 'base64':
        src = 'data:image/png;base64,${}'.format(value.toBase64())
    else:
        src = value
    return imageblock.format(key, src)

def default_handler(key, value):
    return value

def string_handler(key, value):
    _, extension = os.path.splitext(value)
    if extension[1:] in formats:
        return image_handler(key, value, imagetype='file')
    
    return value

def date_handler(key, value):
    return value.toString()

blocks = {QByteArray: image_handler,
          QDate: date_handler,
          QDateTime: date_handler,
          QTime: date_handler,
          str: string_handler,
          unicode: string_handler }

class InfoDock(infodock_widget, infodock_base):
    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        self.results = collections.defaultdict(list)
        self.layerList.currentIndexChanged.connect(self.layerIndexChanged)
        self.featureList.currentIndexChanged.connect(self.featureIndexChanged)
        self.attributesView.linkClicked.connect(self.openimage)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        
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
        for field, value in zip(fields, feature.attributes()):
            data[field] = value
            
        items = []
        for key, value in data.iteritems():
            handler = blocks.get(type(value), default_handler)
            block = handler(key, value)
            try:
                item = "<tr><th>{}</th> <td>{}</td></tr>".format(key, block)
            except UnicodeEncodeError:
                item = "<tr><th>{}</th> <td>{}</td></tr>".format(key, '{IMAGE}')
                
            items.append(item)
            
        rows = ''.join(items)
        html = template.safe_substitute(TITLE=layer.name(), ROWS=rows)
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
    
    def openimage(self, url):
        key = url.toString().lstrip('file://')
        try:
            data, imagetype = images[os.path.basename(key)]
        except KeyError:
            return
        pix = QPixmap()
        if imagetype == 'base64':
            pix.loadFromData(data)
        else:
            pix.load(data)
        utils.openImageViewer(pix)