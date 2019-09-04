import os
import copy
import glob
import yaml
import importlib
import importlib.util

from collections import OrderedDict

from qgis.PyQt.QtCore import pyqtSignal, QObject
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsWkbTypes, QgsMapLayer, QgsFeature, QgsProject
from roam.maptools.pointtool import PointTool
from roam.maptools.polygontool import PolygonTool
from roam.maptools.polylinetool import PolylineTool

from roam.utils import log, debug
from roam.syncing import replication
from roam.api import FeatureForm
from roam.dataaccess.database import Database
from roam.structs import CaseInsensitiveDict

from yaml.scanner import ScannerError

import roam.qgisfunctions
import roam.utils
import roam
import roam.maptools
import roam.api.utils
import roam.defaults as defaults

# This of supported geometry types for the forms.
supportedgeometry = [QgsWkbTypes.PointGeometry,
                     QgsWkbTypes.PolygonGeometry,
                     QgsWkbTypes.LineGeometry]

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



class ProjectExpection(Exception):
    """
    Raised when there is a issue with a project.
    """
    pass


class NoMapToolConfigured(Exception):
    """ 
        Raised when no map tool has been configured
        for the layer
    """
    pass


class ErrorInMapTool(Exception):
    """
        Raised when there is an error in configuring the map tool  
    """
    pass


class ProjectLoadError(Exception):
    """
        Raised when a project fails to load.
    """
    pass


def increment_version(version):
    return int(version) + 1


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


def layersfromlist(layerlist):
    """
    Transform a list of layer names into layer objects from the layer registry.
    :param layerlist:
    :return:
    """
    qgislayers = roam.api.utils.layers()
    qgislayers = {layer.name(): layer for layer in qgislayers if layer.type() == QgsMapLayer.VectorLayer}
    if not layerlist:
        return qgislayers
    else:
        _qgislayers = OrderedDict()
        for layername in layerlist:
            try:
                _qgislayers[layername] = qgislayers[layername]
            except KeyError:
                continue
        return _qgislayers


def checkversion(roamversion, projectversion):
    def versiontuple(v):
        v = v.split('.')[:3]
        version = tuple(map(int, (v)))
        if len(version) == 2:
            version = (version[0], version[1], 0)
        return version

    if not projectversion:
        return True

    min = versiontuple(roamversion)
    project = versiontuple(projectversion)
    # Only match major for now because API is only broken between major versions.
    majormatch = min[0] == project[0]
    return majormatch


def initfound(folder):
    return os.path.exists(os.path.join(folder, "__init__.py"))


def createinifile(folder):
    with open(os.path.join(folder, "__init__.py"), 'w'):
        pass


def getProjects(paths):
    """
    Return projects inside the set path.
    Each folder will be considered a Roam project
    """
    for projectpath in paths:
        try:
            folders = (sorted([os.path.join(projectpath, item)
                               for item in next(os.walk(projectpath))[1]]))

            for folder in folders:
                if os.path.basename(folder).startswith("_"):
                    # Ignore hidden folders.
                    continue

                if not initfound(folder):
                    createinifile(folder)

                project = Project.from_folder(folder)

                yield project
        except IOError as ex:
            roam.utils.warning("Could not load projects from {}".format(projectpath))
            roam.utils.exception(ex)
            continue


def readfolderconfig(folder, configname):
    """
    Read the config file from the given folder. A file called settings.config is expected to be found in the folder.
    :param folder: The folder to read the config from.
    :return: Returns None if the settings file could not be read.
    """
    settingspath = os.path.join(folder, "{}.config".format(configname))
    if not os.path.exists(settingspath):
        settingspath = os.path.join(folder, "settings.config")

    try:
        with open(settingspath, 'r') as f:
            try:
                settings = yaml.load(f) or {}
            except ScannerError as ex:
                raise ProjectLoadError(str(ex))
        return settings
    except IOError as e:
        roam.utils.warning(e)
        roam.utils.warning("Returning empty settings for settings.config")
        return {}


def writefolderconfig(settings, folder, configname):
    """
    Write the given settings out to the folder to a file named settings.config.
    :param settings: The settings to write to disk.
    :param folder: The folder to create the settings.config file
    """
    settingspath = os.path.join(folder, "settings.config")
    if not os.path.exists(settingspath):
        settingspath = os.path.join(folder, "{}.config".format(configname))

    with open(settingspath, 'w') as f:
        yaml.safe_dump(data=settings, stream=f, default_flow_style=False)


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
        print(config)
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

        location = os.path.join(self.folder, "__init__.py")
        spec = importlib.util.spec_from_file_location(self.project.id + "." + self.name, location)
        module = importlib.util.module_from_spec(spec)
        print(module)
        spec.loader.exec_module(module)
        self._module = module

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
                roam.utils.log("Default key {0}".format(key))
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
        return geomtype in supportedgeometry

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


class Project(QObject):
    projectUpdated = pyqtSignal(object)

    def __init__(self, rootfolder, settings):
        super(Project, self).__init__()
        self.folder = rootfolder
        self._project = None
        self._splash = None
        self.settings = settings
        self._forms = []
        self.basepath = os.path.join(rootfolder, "..")
        self.projectUpdated.connect(self.project_updated)
        self._missinglayers = []
        self.configError = None

    @classmethod
    def from_folder(cls, rootfolder):
        """
        Create a Project object wrapper from a given folder on the file system
        :param rootfolder:
        :return:
        """
        project = cls(rootfolder, {})
        try:
            project.settings = readfolderconfig(rootfolder, configname='project')
        except ProjectLoadError as error:
            roam.utils.error(error)
            project.configError = error.message
        return project

    def reload(self):
        self.settings = readfolderconfig(self.folder, configname='project')

    @property
    def image_folder(self):
        return os.path.join(self.folder, "_images")

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self._settings = value

    @property
    def basefolder(self):
        return os.path.basename(self.folder)

    @property
    def id(self):
        return self.basefolder

    @property
    def name(self):
        default = os.path.basename(self.folder)
        return self.settings.setdefault("title", default)

    @property
    def description(self):
        return self.settings.setdefault("description", '')

    @property
    def version(self):
        return int(self.settings.setdefault("project_version", 1))

    @property
    def save_version(self):
        return int(self.settings.setdefault("project_save_version", 0))

    def increament_version(self):
        self.settings['project_version'] = increment_version(self.version)

    def increament_save_version(self):
        self.settings['project_save_version'] = increment_version(self.save_version)

    def reset_save_version(self):
        """
        Reset the save point version of this project back to 1
        :return:
        """
        self.settings['project_save_version'] = 0

    @property
    def roamversion(self):
        """
        Returns the Roam version this roam project was built with.
        :return:
        """
        return str(self.settings.setdefault("version", roam.__version__))

    @property
    def projectfile(self):
        """
        Return the QGIS project file for the project.  Checks the following in order:
        - settings: projectfile
        - project.qgs
        - project.qgs

        :return: The path to the QGIS project file.
        """
        try:
            return os.path.abspath(self.settings['projectfile'])
        except KeyError:
            qgz = os.path.join(self.folder, "project.qgs.qgz")
            if os.path.exists(qgz):
                return qgz
            else:
                return os.path.join(self.folder, "project.qgs")

    def load_project(self):
        """
        Loads the current project into the QGIS session.
        :return:
        """
        was_read = QgsProject.instance().read(self.projectfile)
        if not was_read:
            raise ProjectExpection(QgsProject.instance().error())

    @property
    def error(self):
        """
        Return a list of errors if this project isn't valid.
        :return:
        """
        return "\n".join(list(self.validate()))

    def validate(self):
        """
        Yields messages for each error in the project.
        """
        try:
            projectfile = self.projectfile
        except IndexError:
            error = "No QGIS project found in the {} project folder".format(self.name)
            yield error

        if self.settings is None:
            error = "No settings set for project"
            yield error

        if not checkversion(roam.__version__, self.roamversion):
            error = "Version mismatch"
            yield error

        if self.configError:
            error = "Project has config error: {0}".format(self.configError)
            yield error

    @property
    def enabled_plugins(self):
        return self.settings.get('plugins', [])

    @property
    def valid(self):
        """
        Check if this project is valid or not.  Call validate for more detail on errors
        :return: True if this project is valid.
        """
        return not list(self.validate())

    def datafolder(self):
        return os.path.join(self.folder, "_data")

    def basedatadb(self):
        path = os.path.join(self.folder, "_data", "basedata.sqlite")
        return Database.connect(type="QSQLITE", database=path)

    @property
    def splash(self):
        self._splash = os.path.join(self.folder, 'splash.svg')
        if os.path.exists(self._splash):
            return self._splash

        self._splash = os.path.join(self.folder, 'splash.png')
        if os.path.exists(self._splash):
            return self._splash

        return ''

    def syncprovders(self):
        providers = self.settings.get("providers", {})
        variables = {}
        for name, config in providers.items():
            if name == "variables":
                variables.update(config)
                continue

            cmd = config['cmd']
            cmd = os.path.join(self.folder, cmd)
            if config['type'] == 'replication' or config['type'] == 'batch':
                config['cmd'] = cmd
                config.setdefault('variables', variables)
                config.update(variables)
                yield replication.BatchFileSync(name, self, **config)

    @property
    def module(self):
        name = os.path.basename(self.folder)
        location = os.path.join(self.folder, "__init__.py")
        spec = importlib.util.spec_from_file_location(name, location)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def getPanels(self):
        raise NotImplementedError("Panel support not migrated in Roam 3")

        for module in glob.iglob(os.path.join(self.folder, "_panels", '*.py')):
            modulename = os.path.splitext(os.path.basename(module))[0]
            try:
                panelmod = self.module.load_source(modulename, module)
                yield panelmod.createPanel()
            except ImportError as err:
                log("Panel import error {}".format(err))
            except AttributeError:
                log("No createPanel defined on module {}".format(module))

    def onProjectLoad(self):
        """
            Call the projects onProjectLoad method defined in projects __init__ module.
            Returns True if the user is able to load the project, else False
        """
        try:
            if hasattr(self.module, "onProjectLoad"):
                return self.module.onProjectLoad()
            else:
                return True, None
        except ImportError as err:
            log(err)
            return True, None

    def formsforlayer(self, layername):
        """
        Return all the forms that are assigned to that the given layer name.
        :param layername:
        :return:
        """
        for form in self.forms:
            if form.layername == layername:
                yield form

    def form_by_name(self, name):
        """
        Return the form with the given name.  There can only be one.
        :param name: The name of the form to return.
        :return:
        """
        for form in self.forms:
            if form.name == name:
                return form

    def layer_can_capture(self, layer):
        return 'capture' in self.layer_tools(layer)

    def layer_tools(self, layer):
        selectconfig = self.settings.setdefault('selectlayerconfig', {}).setdefault(layer.name(), {})
        tools = selectconfig.get('tools', ['delete', 'capture', 'edit_attributes', 'edit_geom'])
        _tools = {}
        for tool in tools:
            if isinstance(tool, str):
                _tools[tool] = {}
            elif isinstance(tool, dict):
                _tools[tool.keys()[0]] = tool.values()[0]

        print("TOOLS", _tools)
        return _tools

    @property
    def forms(self):
        def mapformconfig(forms):
            if hasattr(forms, 'items'):
                for formname, config in forms.items():
                    yield formname, config
            else:
                for formname in forms:
                    folder = os.path.join(self.folder, formname)
                    config = readfolderconfig(folder, configname='form')
                    yield formname, config

        if not self._forms:
            forms = self.settings.setdefault("forms", [])
            for formname, config in mapformconfig(forms):
                folder = os.path.join(self.folder, formname)
                form = Form.from_config(formname, config, folder, project=self)
                self._forms.append(form)

        return self._forms

    @property
    def selectlayers(self):
        return self.settings.get('selectlayers', [])

    def info_query(self, infoname, layername):
        try:
            layersconfig = self.settings['selectlayerconfig']
            layerconfig = layersconfig[layername]
            infoblock = layerconfig[infoname]
            return infoblock
        except KeyError:
            return {}

    def selectlayer_name(self, layername):
        try:
            layersconfig = self.settings['selectlayerconfig']
            layerconfig = layersconfig[layername]
            return layerconfig['label']
        except KeyError:
            return layername

    def selectlayersmapping(self):
        """
        Return the mapping between the select layers listed in settings
        and the QGIS layer itself.

        If no select layers are found in the settings this function will return
        all layers in the project
        """
        return layersfromlist(self.selectlayers)

    def gpslog_layer(self):
        """
        Return the GPS log layer set for this project
        """
        try:
            return roam.api.utils.layer_by_name("gps_log")
        except IndexError:
            return None

    @property
    def legendlayers(self):
        return self.settings.get('legendlayers', [])

    def legendlayersmapping(self):
        return layersfromlist(self.legendlayers)

    def historyenabled(self, layer):
        return layer.name() in self.settings.get('historylayers', [])

    def addformconfig(self, name, config):
        forms = self.settings.setdefault("forms", [])
        folder = os.path.join(self.folder, name)

        if hasattr(forms, 'items'):
            forms[name] = config
        else:
            forms.append(name)
            Form.saveconfig(config, folder)

        self.settings['forms'] = forms
        self._forms = []
        form = [form for form in self.forms if form.name == name][0]
        debug(config)
        return form

    def removeform(self, name):
        print("Removing {0}".format(name))
        forms = self.settings.setdefault("forms", [])
        if hasattr(forms, 'iteme'):
            del self.settings['forms'][name]
        else:
            index = forms.index(name)
            del self.settings['forms'][index]
        print(self.settings['forms'])

    def save(self, update_version=False, save_forms=True, reset_save_point=False):
        """
        Save the project config to disk.
        :param update_version Updates the version in the project file.
        """
        if update_version:
            self.increament_version()

        if reset_save_point:
            self.reset_save_version()
        else:
            self.increament_save_version()

        writefolderconfig(self.settings, self.folder, configname='project')
        if save_forms:
            # Clear the form cache
            formsstorage = self.settings.setdefault("forms", [])
            if not hasattr(formsstorage, 'items'):
                for form in self.forms:
                    debug("Saving {}".format(form.name))
                    debug(form.settings)
                    form.save()
        self.projectUpdated.emit(self)

    @property
    def oldformconfigstlye(self):
        formsstorage = self.settings.get("forms", [])
        return hasattr(formsstorage, 'items')

    def hascapturelayers(self):
        layers = roam.api.utils.layers()
        layers = (layer for layer in layers if layer.type() == QgsMapLayer.VectorLayer)
        layers = [layer.name() for layer in layers if layer.geometryType() in supportedgeometry]
        for layer in self.selectlayers:
            if layer in layers:
                return True
        return False

    def __eq__(self, other):
        if not other:
            return False
        return self.basefolder == other.basefolder

    def project_updated(self, project):
        self.reload()

    def dump_settings(self):
        import pprint

        pprint.pprint(self.settings)

    @property
    def missing_layers(self):
        return self._missinglayers

    @missing_layers.setter
    def missing_layers(self, layers):
        self._missinglayers = layers
