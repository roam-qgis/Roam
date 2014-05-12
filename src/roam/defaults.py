import os
from qgis.core import QgsExpression, QgsMapLayerRegistry, QgsFeatureRequest

import roam.utils

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
            log(ex)
            value = None
    else:
        # Pass it though a series of filters to get the default value if it's just pain text
        value = os.path.expandvars(defaultconfig)
        if '[%' in defaultconfig and '%]' in defaultconfig:
            # TODO Use regex
            value = QgsExpression.replaceExpressionText(value, feature, layer)

    roam.utils.debug("Default value: {}".format(value))
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
    layername = defaultconfig['layer']
    expression = defaultconfig['expression']
    field = defaultconfig['field']

    searchlayer = QgsMapLayerRegistry.instance().mapLayersByName(layername)[0]
    rect = feature.geometry().boundingBox()
    rect.scale(10)
    rect = canvas.mapRenderer().mapToLayerCoordinates(layer, rect)
    rq = QgsFeatureRequest().setFilterRect(rect)
    features = searchlayer.getFeatures(rq)

    exp = QgsExpression(expression)
    exp.prepare(searchlayer.pendingFields())

    for f in features:
        if exp.evaluate(f):
            return f[field]

    raise DefaultError('No features found')

defaultproviders = {'spatial-query': layer_value,
                    'layer-value': layer_value}

