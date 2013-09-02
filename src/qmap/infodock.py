import os

from PyQt4.QtGui import QTableWidgetItem
from PyQt4.QtCore import Qt, QUrl

from uifiles import (infodock_widget, infodock_base)

htmlpath = os.path.join(os.path.dirname(__file__) , "info.html")

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
        with open(htmlpath) as f:
            html = f.read()
        items = []
        for key, value in data.iteritems():
            item = "<tr><th>{}</th> <td>{}</td></tr>".format(key, value)
            items.append(item)
            
        rows = ''.join(items)
        html = html.format(TITLE=layer.name(), ROWS=rows)
        import tempfile
        with tempfile.TemporaryFile(mode='at', delete=False) as f:
            f.write(html)
            name = f.name +  ".html"
            
        import utils
        utils.log(name) 
        base = os.path.dirname(os.path.abspath(__file__))
        baseurl = QUrl.fromLocalFile(name)
        self.attributesView.load(baseurl)
        
    def clearResults(self):
        self.layerList.clear()
        self.attributesView.setHtml('')
          
    def addLayer(self, layer):
        self.layerList.addItem(layer.name())
        