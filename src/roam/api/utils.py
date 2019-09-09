import collections
import os
import subprocess
import sys
from contextlib import contextmanager

from PyQt5.QtWidgets import QScroller
from qgis.core import QgsProject, QgsFeatureRequest, QgsGeometry, NULL, Qgis, QgsExpressionContext, \
    QgsExpressionContextScope, QgsExpression, QgsFeature

from roam.structs import CaseInsensitiveDict


def update_feature(layer, *features):
    """
    Change feature using the data provider skipping the edit buffer for speed.
    :param layer: The layer to get the provider from.
    :param features: A list of features to update.
    :return: True on success or rasies Expection on fail
    """
    featuremap = {}
    for feature in features:
        attrs = {index: value for index, value in enumerate(feature.attributes())}
        featuremap[feature.id()] = attrs
    passes = layer.dataProvider().changeAttributeValues(featuremap)
    if not passes:
        raise FeatureSaveException.not_saved(layer.dataProvider().error().message())


def open_keyboard():
    """
    Open the system keyboard
    """
    if sys.platform == 'win32':
        try:
            programfiles = os.environ['ProgramW6432']
        except KeyError:
            programfiles = os.environ['ProgramFiles']

        cmd = r'{path}\Common Files\Microsoft Shared\ink\TabTip.exe'.format(path=programfiles)
        try:
            os.startfile(cmd)
        except WindowsError:
            import roam.config
            roam.config.settings['keyboard'] = False
            roam.config.save()
    else:
        cmd = 'onboard'
        subprocess.Popen(cmd)


def layers(layertype=None):
    _layers = QgsProject.instance().mapLayers().values()
    if layertype is None:
        return _layers
    else:
        return [layer for layer in _layers if layer.type() == layertype]


def layer_by_name(name):
    """
    Return a layer from QGIS using its name.
    :param name: The name of the layer
    :return: A single layer with the given layer name
    """
    return layers_by_name(name)[0]


def layers_by_name(name):
    """
    Return any layers from QGIS using a name.
    :param name: The name of the layer
    :return: A list of layers with the given layer name
    """
    return QgsProject.instance().mapLayersByName(name)


def feature_by_key(layer, key):
    """
    Return the feature for the given key
    :param layer: The layer to search
    :param key: The mapkey to lookup.  This is the feature.id() in QGIS.
    :return: The feature found using the mapkey.  Will throw StopInteration if not found
    """
    rq = QgsFeatureRequest(key)
    return next(layer.getFeatures(rq))


class FeatureSaveException(Exception):
    def __init__(self, title, message, level, timeout=0, moreinfo=None):
        super(FeatureSaveException, self).__init__(self, message)
        self.title = title
        self.level = level
        self.timout = timeout
        self.moreinfo = moreinfo
        if self.moreinfo:
            self.message = message + ':' + str(moreinfo)
        else:
            self.message = message

    @classmethod
    def not_accepted(cls):
        return cls("Form was not accepted", "The form could not be accepted", Qgis.Warning)

    @classmethod
    def not_saved(cls, errors):
        return cls("Error in saving feature",
                   "There seems to be a error trying to save the feature",
                   Qgis.Critical,
                   moreinfo='\n'.join(errors))

    @property
    def error(self):
        """
        Returns a tuple of the error
        """
        return (self.title, self.message, self.level, self.timout, self.moreinfo)


class MissingValuesException(FeatureSaveException):
    @classmethod
    def missing_values(cls, fields):
        html = "<ul>"
        for field in fields:
            html += "<li>{}</li>".format(field)
        html += "</ul>"
        return cls("Missing fields", "Some fields are still required. <br> {}".format(html), Qgis.Warning, 2)


@contextmanager
def editing(layer):
    layer.startEditing()
    yield layer
    saved = layer.commitChanges()
    if not saved:
        layer.rollBack()
        errors = layer.commitErrors()
        raise FeatureSaveException.not_saved(errors)


def values_from_feature(feature, safe_names=False, ordered=False):
    def escape(value):
        if safe_names:
            value = value.replace(" ", "_")
            return value
        else:
            return value

    attributes = feature.attributes()
    fields = [escape(field.name().lower()) for field in feature.fields()]
    if ordered:
        return collections.OrderedDict(zip(fields, attributes))
    else:
        return CaseInsensitiveDict(zip(fields, attributes))


def copy_feature_values(from_feature, to_feature, include_geom=False):
    """
    Copy the values from one feature to another. Missing keys are ignored
    :param from_feature: Feature to copy from
    :param to_feature: Feature to copy to
    :param include_geom: default False, if True will copy the feature geometry
    :return: A reference to the to_feature
    """
    values = values_from_feature(from_feature)
    for field, value in values.items():
        try:
            to_feature[field] = value
        except KeyError:
            continue
    if include_geom:
        geom = QgsGeometry(from_feature.geometry())
        to_feature.setGeometry(geom)
    return to_feature


def nullcheck(value):
    """
    Checks if the value is a null type from QGIS ( NOTE: NULL != null for QgsFeature values).
    :param value: The value from the QgsFeature which might be a qgis.core.NULL value
    :return: None or the value if the value isn't qgis.core.NULL
    """
    if value == NULL:
        return None
    return value


def format_values(fieldnames, valuestore, with_char='\n'):
    """
    Format the given fields with with_char for each.
    :param fieldnames: A list of fields to format.
    :param valuestore: A dict like store of values
    """
    value = []
    for field in fieldnames:
        try:
            if nullcheck(valuestore[field]):
                value.append(valuestore[field])
        except KeyError:
            continue
    return with_char.join(value)


def install_touch_scroll(widget) -> None:
    """
    Install the touch events on a widget so it can scroll with touch events
    :param widget: The widget to install the touch events on.
    """
    QScroller.grabGesture(widget, QScroller.TouchGesture)


def replace_expression_placeholders(text:str, feature: QgsFeature):
    """
    Replace any QGIS expression placeholders in the given string.
    :param text: The text to replace the expression values in.
    :param feature: The feature to pull any expression values from.
    :return: A string with expression values replaced.
    """
    return QgsExpression.replaceExpressionText(text, expression_context_for_feature(feature))


def expression_context_for_feature(feature):
    """
    Create a new expression context for the given feature.
    :param feature:
    :return:
    """
    context = QgsExpressionContext()
    scope = QgsExpressionContextScope()
    context.appendScope(scope)
    if feature is not None:
        scope.setVariable("roamgeometry", feature.geometry())
        context.setFeature(feature)
    return context
