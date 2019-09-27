import copy
import importlib
import importlib.util
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from qgis._core import QgsMapLayer, QgsFeature, QgsWkbTypes

import roam.api
import roam.qgisfunctions
import roam.utils
from roam import defaults as defaults
from roam.api import FeatureForm
from roam.maptools.pointtool import PointTool
from roam.maptools.polygontool import PolygonTool
from roam.maptools.polylinetool import PolylineTool
from roam.config import writefolderconfig, readfolderconfig
from roam.structs import CaseInsensitiveDict


def values_from_feature(feature, layer):
    attributes = feature.attributes()
    fields = [field.name().lower() for field in feature.fields()]
    if layer.dataProvider().name() == 'spatialite':
        pkindexes = layer.dataProvider().pkAttributeIndexes()
        for index in pkindexes:
            del fields[index]
            del attributes[index]
    values = CaseInsensitiveDict(zip(fields, attributes))
    return values


def tool_for_geometry_type(geomtype: QgsWkbTypes):
    """
    Get the geometry tool for the given geometry type
    :param geomtype:
    :return:
    """

    tools = {QgsWkbTypes.PointGeometry: PointTool,
             QgsWkbTypes.PolygonGeometry: PolygonTool,
             QgsWkbTypes.LineGeometry: PolylineTool}

    return tools[geomtype]


class NoMapToolConfigured(Exception):
    """
        Raised when no map tool has been configured
        for the layer
    """
    pass


class Form(object):
    def __init__(self, name, config, rootfolder, project=None):
        self._name = name
        self.settings = config
        self.folder = rootfolder
        self._module = None
        self.errors = []
        self._qgislayer = None
        self._formclass = None
        self._action = None
        self.project = project
        self.template_values = {}
        self.suppressform = False

    @classmethod
    def from_config(cls, name, config, folder, project=None):
        form = cls(name, config, folder, project)
        form._loadmodule()
        form.init_form()
        return form

    def copy(self):
        import copy
        settings = copy.copy(self.settings)
        return Form(self.name, settings, self.folder, self.project)

    @classmethod
    def from_folder(cls, name, folder):
        config = readfolderconfig(folder, "form")
        return Form.from_config(name, config, folder)

    @property
    def savekey(self):
        return self.settings.get('savekey', str(self.QGISLayer.id()))

    @property
    def label(self):
        return self.settings.setdefault('label', self.name)

    @property
    def name(self):
        return self._name

    def createuiaction(self, parent=None):
        action = QAction(QIcon(self.icon), self.icontext, parent)
        if not self.valid[0]:
            action.setEnabled(False)
            action.setText(action.text() + " (invalid)")
        return action

    @property
    def icontext(self):
        return self.label

    @property
    def layername(self):
        return self.settings.get('layer', '')

    @property
    def events(self):
        return self.settings.get('events', [])

    @property
    def icon(self):
        icon = os.path.join(self.folder, 'icon.svg')
        if os.path.exists(icon):
            return icon

        icon = os.path.join(self.folder, 'icon.png')
        if os.path.exists(icon):
            return icon

        return ''

    @property
    def QGISLayer(self):
        def getlayer(name):
            try:
                return roam.api.utils.layer_by_name(name)
            except IndexError as e:
                roam.utils.log(e)
                return None

        if self._qgislayer is None:
            layer = self.settings.get('layer', None)
            self._qgislayer = getlayer(layer)
        return self._qgislayer

    def getMaptool(self):
        """
            Returns the map tool configured for this layer.
        """
        geomtype = self.QGISLayer.geometryType()
        try:
            return tool_for_geometry_type(geomtype)
        except KeyError:
            raise NoMapToolConfigured

    @property
    def capabilities(self):
        """
            The configured capabilities for this layer.
        """
        default = ['capture', 'edit', 'move']
        capabilities = self.settings.get("capabilities", default)
        roam.utils.log(capabilities)
        return capabilities

    @property
    def valid(self):
        """
        Check if this layer is a valid project layer
        """
        if not os.path.exists(self.folder):
            self.errors.append("Form folder not found")

        if self.QGISLayer is None:
            self.errors.append("Layer {} not found in project".format(self.layername))

        elif not self.QGISLayer.type() == QgsMapLayer.VectorLayer:
            self.errors.append("We can only support vector layers for data entry")

        if self.errors:
            return False, self.errors
        else:
            return True, []

    @property
    def widgets(self):
        return self.settings.setdefault('widgets', [])

    def init_form(self):
        try:
            self.module.init_form(self)
        except AttributeError:
            pass

    def registerform(self, formclass):
        self._formclass = formclass

    @property
    def formclass(self):
        return self._formclass or FeatureForm

    def create_featureform(self, feature, defaults=None, *args, **kwargs):
        """
        Creates and returns the feature form for this Roam form
        """
        if defaults is None:
            defaults = {}
        print(dir(self.formclass))
        return self.formclass.from_form(self, self.settings, feature, defaults, *args, **kwargs)

    def widgetswithdefaults(self):
        """
        Return any widget configs that have default values needed
        """
        for config in self.valid_widgets():
            if 'default' in config:
                yield config['field'], config

    def valid_widgets(self):
        def is_valid(widget):
            try:
                return widget['field'] is not None
            except KeyError:
                return True

        return [widget for widget in self.widgets if is_valid(widget)]

    def widget_by_field(self, fieldname):
        widgets = [widget for widget in self.widgets if not widget['widget'].lower() == 'section']
        return [widget for widget in widgets if widget['field'] == fieldname][0]

    def _loadmodule(self):
        """
        Load the forms python module
        :return:
        """

        # imp is meant to not be used but I couldn't work out a Pyton 3 version that works
        import imp
        projectfolder = os.path.abspath(os.path.join(self.folder, '..'))
        module = imp.find_module(self.name, [projectfolder, self.folder])
        import sys
        sys.path.append(self.folder)
        self._module = imp.load_module(self.name, *module)
        sys.path.remove(self.folder)

    @property
    def module(self):
        return self._module

    def save(self):
        Form.saveconfig(self.settings, self.folder)

    @classmethod
    def saveconfig(cls, config, folder):
        writefolderconfig(config, folder, configname='form')

    def new_feature(self, set_defaults=True, geometry=None, data=None):
        """
        Returns a new feature that is created for the layer this form is bound too
        :return: A new QgsFeature
        """

        layer = self.QGISLayer
        fields = layer.fields()
        feature = QgsFeature(fields)
        if data:
            for key, value in data.items():
                feature[key] = value
        else:
            data = {}

        if geometry:
            feature.setGeometry(geometry)

        if set_defaults:
            for index in range(fields.count()):
                pkindexes = layer.dataProvider().pkAttributeIndexes()
                if index in pkindexes and layer.dataProvider().name() == 'spatialite':
                    continue

                # Don't override fields we have already set.
                if fields.field(index).name() in data:
                    continue

                value = layer.dataProvider().defaultValue(index)
                feature[index] = value
            # Update the feature with the defaults from the widget config
            defaults = self.default_values(feature)
            roam.utils.log(defaults)
            for key, value in defaults.items():
                # Don't override fields we have already set.
                if key is None:
                    continue
                datakeys = [key.lower() for key in data.keys()]
                if key.lower() in datakeys:
                    roam.utils.log("Skippping {0}".format(key))
                    continue
                try:
                    feature[key] = value
                except KeyError:
                    roam.utils.info("Couldn't find key {} on feature".format(key))

        return feature

    def values_from_feature(self, feature):
        return values_from_feature(feature, self.QGISLayer)

    def default_values(self, feature):
        """
        Return the default values for the form using the given feature.
        :param feature: The feature that can be used for default values
        :return: A dict of default values for the form
        """
        # One capture geometry, even for sub forms?
        # HACK Remove me and do something smarter
        roam.qgisfunctions.capturegeometry = feature.geometry()
        defaultwidgets = self.widgetswithdefaults()
        defaultvalues = defaults.default_values(defaultwidgets, feature, self.QGISLayer)
        return defaultvalues

    @property
    def has_geometry(self):
        if not self.QGISLayer:
            return False

        geomtype = self.QGISLayer.geometryType()
        return geomtype not in [QgsWkbTypes.UnknownGeometry,
                                QgsWkbTypes.NullGeometry]

    def get_query(self, name, values):
        if values is None:
            values = {}
        query = self.settings['query'][name]['sql']
        try:
            # Why am I doing this here?  We don't even need it
            mappings = self.settings['query'][name]['mappings']
            newvalues = copy.deepcopy(mappings)
            for key_name, key_column in mappings.items():
                newvalues[key_name] = values[key_column]
        except KeyError:
            newvalues = copy.deepcopy(values)
        return query, newvalues

