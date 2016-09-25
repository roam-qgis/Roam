import os
from qgis.core import QgsExpression, QgsMapLayerRegistry, QgsFeatureRequest, QGis, QgsPoint, QgsRectangle

import roam.utils
from roam.api import RoamEvents

canvas = None

class DefaultError(Exception):
    pass


def default_value(defaultconfig, feature, layer):
    if isinstance(defaultconfig, dict):
        try:
            defaulttype = defaultconfig['type']
        except KeyError:
            raise DefaultError("No type key set for default config")

        try:
            defaultprovider = defaultproviders[defaulttype]
        except KeyError as ex:
            log(ex)
            raise DefaultError("No default provider found for {}".format(defaulttype))

        try:
            value = defaultprovider(feature, layer, defaultconfig)
        except DefaultError as ex:
            roam.utils.log(ex)
            value = None
    else:
        # Pass it though a series of filters to get the default value if it's just pain text
        defaultconfig = str(defaultconfig)
        value = os.path.expandvars(defaultconfig)
        if '[%' in defaultconfig and '%]' in defaultconfig:
            # TODO Use regex
            value = QgsExpression.replaceExpressionText(value, feature, layer)

    return value


def widget_default(widgetconfig, feature, layer):
    defaultconfig = widgetconfig.get("default", None)
    if defaultconfig is None:
        return None

    return default_value(defaultconfig, feature, layer)


def default_values(widgets, feature, layer):
    defaultvalues = {}
    for field, config in widgets:
        value = widget_default(config, feature, layer)
        defaultvalues[field] = value

    return defaultvalues

def layer_value(feature, layer, defaultconfig):
    if not canvas:
        roam.utils.warning("No canvas set for using layer_values default function")
        return None
    layers = []
    # layer name can also be a list of layers to search
    layername = defaultconfig['layer']
    if isinstance(layername, basestring):
        layers.append(layername)
    else:
        layers = layername

    expression = defaultconfig['expression']
    field = defaultconfig['field']

    for searchlayer in layers:
        try:
            searchlayer = QgsMapLayerRegistry.instance().mapLayersByName(searchlayer)[0]
        except IndexError:
            RoamEvents.raisemessage("Missing layer",
                                    "Unable to find layer used in widget expression {}".format(searchlayer),
                                    level=1)
            roam.utils.warning("Unable to find expression layer {}".format(searchlayer))
            return
        if feature.geometry():
            rect = feature.geometry().boundingBox()
            if layer.geometryType() == QGis.Point:
                point = feature.geometry().asPoint()
                rect = QgsRectangle(point.x(), point.y(), point.x() + 10, point.y() + 10)

            rect.scale(20)

            rect = canvas.mapRenderer().mapToLayerCoordinates(layer, rect)
            rq = QgsFeatureRequest().setFilterRect(rect)\
                                    .setFlags(QgsFeatureRequest.ExactIntersect)
            features = searchlayer.getFeatures(rq)
        else:
            features = searchlayer.getFeatures()

        exp = QgsExpression(expression)
        exp.prepare(searchlayer.pendingFields())
        if exp.hasParserError():
            error = exp.parserErrorString()
            roam.utils.warning(error)

        for f in features:
            value = exp.evaluate(f)
            if exp.hasEvalError():
                error = exp.evalErrorString()
                roam.utils.warning(error)
            if value:
                return f[field]

    raise DefaultError('No features found')

defaultproviders = {'spatial-query': layer_value,
                    'layer-value': layer_value}

