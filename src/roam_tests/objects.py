from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsFields, QgsGeometry

def newmemorylayer():
    uri = "point?crs=epsg:4326&field=id:integer"
    layer = QgsVectorLayer(uri, 'testlayer', "memory")
    return layer

def addfeaturestolayer(layer, featurecount):
    for count in range(featurecount):
        feature = QgsFeature()
        feature.setId(count)
        layer.dataProvider().addFeatures([feature])
    return layer


def makefield(name, type, length):
    field = QgsField(name, type)
    field.setLength(length)
    return field


def make_fields(fields):
    newfields = QgsFields()
    for field in fields:
        newfields.append(makefield(field["name"], field["type"], field["length"]))
    return newfields


def make_feature(fields, wkt=None, with_values=True):
    feature = QgsFeature()
    feature.setFields(make_fields(fields))
    if wkt is not None:
        geom = QgsGeometry.fromWkt(wkt)
        feature.setGeometry(geom)
    if with_values:
        for field in fields:
            feature[field["name"]] = field["value"]

    return feature


