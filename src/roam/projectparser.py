from PyQt4.QtXml import QDomDocument

from qgis.gui import QgsMapCanvasLayer
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsMapLayerRegistry


def iternodes(nodes):
    for index in xrange(nodes.length()):
        yield nodes.at(index).toElement()


class ProjectParser(object):
    def __init__(self, xmldoc):
        self.doc = xmldoc

    @classmethod
    def fromFile(cls, filename):
        xml = open(filename).read()
        doc = QDomDocument()
        doc.setContent(xml)
        return cls(doc)

    def _createLayer(self, node):
        type = node.attribute('type')
        if type == "vector":
            layer = QgsVectorLayer()
        elif type == "raster":
            layer = QgsRasterLayer()
        else:
            return None
        layer.readLayerXML(node)
        return layer.id(), layer

    def canvaslayers(self):
        """
        Get all configured canvas layers in the project
        """
        layers = QgsMapLayerRegistry.instance().mapLayers()

        def makelayer(layerid, visible):
            try:
                layer = layers[layerid]
            except KeyError:
                return None
            return QgsMapCanvasLayer(layer, visible)

        layerset = [makelayer(layerid, visible) for layerid, visible in self.layers()]
        layerset = filter(None, layerset)
        return layerset

    @property
    def canvasnode(self):
        nodes = self.doc.elementsByTagName("mapcanvas")
        return nodes.at(0)

    def _getLayers(self, node):
        filelist = node.elementsByTagName("legendlayerfile")
        layerfile = filelist.at(0).toElement()
        layerid = layerfile.attribute('layerid')
        visible = int(layerfile.attribute('visible'))
        return layerid, bool(visible)
    
    def maplayers(self):
        layernodes = self.doc.elementsByTagName("maplayer")
        return (self._createLayer(elm) for elm in iternodes(layernodes))
        
    def layers(self):
        legendnodes = self.doc.elementsByTagName("legendlayer")
        return (self._getLayers(elm) for elm in iternodes(legendnodes))


