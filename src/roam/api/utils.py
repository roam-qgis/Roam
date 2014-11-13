import sys
import os
import subprocess
from contextlib import contextmanager
from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest, QgsGeometry
from qgis.gui import QgsMessageBar
from PyQt4.QtCore import QPyNullVariant
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
            roam.config.settings['keyboard'] = False
            roam.config.save()
    else:
        cmd = 'onboard'
        subprocess.Popen(cmd)

def layers():
    return QgsMapLayerRegistry.instance().mapLayers().values()

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
    return QgsMapLayerRegistry.instance().mapLayersByName(name)

def feature_by_key(layer, key):
    """
    Return the feature for the given key
    :param layer: The layer to search
    :param key: The mapkey to lookup.  This is the feature.id() in QGIS.
    :return: The feature found using the mapkey.  Will throw StopInteration if not found
    """
    rq = QgsFeatureRequest(key)
    return layer.getFeatures(rq).next()


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
        return cls("Form was not accepted", "The form could not be accepted", QgsMessageBar.WARNING)

    @classmethod
    def not_saved(cls, errors):
        return cls("Error in saving feature",
                   "There seems to be a error trying to save the feature",
                   QgsMessageBar.CRITICAL,
                   moreinfo='\n'.join(errors))

    @property
    def error(self):
        """
        Returns a tuple of the error
        """
        return (self.title, self.message, self.level, self.timout, self.moreinfo)

class MissingValuesException(FeatureSaveException):
    @classmethod
    def missing_values(cls):
        return cls("Missing fields", "Some fields are still required.", QgsMessageBar.WARNING, 2)


@contextmanager
def editing(layer):
    layer.startEditing()
    yield layer
    saved = layer.commitChanges()
    if not saved:
        layer.rollBack()
        errors = layer.commitErrors()
        raise FeatureSaveException.not_saved(errors)

def values_from_feature(feature):
    attributes = feature.attributes()
    fields = [field.name().lower() for field in feature.fields()]
    values = CaseInsensitiveDict(zip(fields, attributes))
    return values

def copy_feature_values(from_feature, to_feature, include_geom=False):
    """
    Copy the values from one feature to another. Missing keys are ignored
    :param from_feature: Feature to copy from
    :param to_feature: Feature to copy to
    :param include_geom: default False, if True will copy the feature geometry
    :return: A reference to the to_feature
    """
    values = values_from_feature(from_feature)
    for field, value in values.iteritems():
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
    SIP 2.0 has this gross QPyNullVariant type that we have to convert to None for better handling in our
    calling code.  Most QGIS None values return as QPyNullVariant.
    :param value:
    :return:
    """
    if isinstance(value, QPyNullVariant):
        return None
    else:
        return value

def format_values(fieldnames, valuestore, with_char='\n'):
    """
    Format the given fields with with_char for each.
    :param fieldnames: A list of fields to format.
    :param valuestore: A dict like store of values
    """
    value = []
    for field in fieldnames:
        if nullcheck(valuestore[field]):
            value.append(valuestore[field])
    return with_char.join(value)
