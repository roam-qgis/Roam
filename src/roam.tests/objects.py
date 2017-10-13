from qgis.core import QgsVectorLayer, QgsFeature, QgsProviderRegistry, QgsField

def newmemorylayer():
    uri = "point?crs=epsg:4326&field=id:integer"
    layer = QgsVectorLayer(uri, 'testlayer', "memory")
    return layer

def addfeaturestolayer(layer, featurecount):
    for count in xrange(featurecount):
        feature = QgsFeature()
        feature.setFeatureId(count)
        layer.dataProvider().addFeatures([feature])
    return layer



def makefield(name, type, length):
    field = QgsField(name, type)
    field.setLength(length)
    return field
