from qgis.core import QgsVectorLayer, QgsFeature, QgsProviderRegistry

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

