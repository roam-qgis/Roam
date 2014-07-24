import os
import glob
import utils
import yaml
import functools
import imp
import importlib
import sys

from datetime import datetime
from collections import OrderedDict

from PyQt4.QtGui import QAction, QIcon

from qgis.core import QgsMapLayerRegistry, QGis, QgsTolerance, QgsVectorLayer, QgsMapLayer

from roam.utils import log, debug
from roam.syncing import replication
from roam.api import FeatureForm, plugins
from roam.structs import OrderedDictYAMLLoader

import roam.utils
import roam
import roam.maptools

supportedgeometry = [QGis.Point, QGis.Polygon, QGis.Line]

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


def layersfromlist(layerlist):
    """
    Transform a list of layer names into layer objects from the layer registry.
    :param layerlist:
    :return:
    """
    qgislayers = QgsMapLayerRegistry.instance().mapLayers().values()
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
        version = tuple(map(int, (v.split("."))))
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
            if not initfound(projectpath):
                createinifile(projectpath)

            folders = (sorted([os.path.join(projectpath, item)
                               for item in os.walk(projectpath).next()[1]]))

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
            settings = yaml.load(f) or {}
        return settings
    except IOError as e:
        utils.warning(e)
        utils.warning("Returning empty settings for settings.config")
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
        roam.yaml.safe_dump(data=settings, stream=f, default_flow_style=False)



class Form(object):
    def __init__(self, name, config, rootfolder):
        self._name = name
        self.settings = config
        self.folder = rootfolder
        self._module = None
        self.errors = []
        self._qgislayer = None
        self._formclass = None
        self._action = None

    @classmethod
    def from_config(cls, name, config, folder):
        form = cls(name, config, folder)
        form._loadmodule()
        form.init_form()
        return form

    @property
    def label(self):
        return self.settings.setdefault('label', self.name)

    @property
    def name(self):
        return self._name

    def createuiaction(self):
        action = QAction(QIcon(self.icon), self.icontext, None)
        if not self.valid[0]:
            action.setEnabled(False)
            action.setText(action.text() + " (invalid)")
        return action

    @property
    def icontext(self):
        return self.label

    @property
    def layername(self):
        return self.settings['layer']

    @property
    def icon(self):
        iconpath = os.path.join(self.folder, 'icon.png')
        return iconpath

    @property
    def QGISLayer(self):
        def getlayer(name):
            try:
                return QgsMapLayerRegistry.instance().mapLayersByName(name)[0]
            except IndexError as e:
                utils.log(e)
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
            return roam.maptools.tools[geomtype]
        except KeyError:
            raise NoMapToolConfigured

    @property
    def capabilities(self):
        """
            The configured capabilities for this layer.
        """
        default = ['capture', 'edit', 'move']
        capabilities = self.settings.get("capabilities", default)
        utils.log(capabilities)
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

    def create_featureform(self, feature, defaults, *args, **kwargs):
        """
        Creates and returns the feature form for this Roam form
        """
        return self.formclass.from_form(self, self.settings, feature, defaults, *args, **kwargs)

    def widgetswithdefaults(self):
        """
        Return any widget configs that have default values needed
        """
        for config in self.widgets:
            if 'default' in config:
                yield config['field'], config

    def widget_by_field(self, fieldname):
        return [widget for widget in self.widgets if widget['field'] == fieldname][0]

    def _loadmodule(self):
        rootfolder = os.path.abspath(os.path.join(self.folder, '..', '..'))
        projectfolder = os.path.abspath(os.path.join(self.folder, '..'))
        rootname = os.path.basename(rootfolder)
        projectname = os.path.basename(projectfolder)
        name = "{root}.{project}.{formfolder}".format(root=rootname,
                                                      project=projectname,
                                                      formfolder=self.name)
        try:
            self._module = importlib.import_module(name)
        except ImportError as err:
            createinifile(self.folder)
            self._loadmodule()

    @property
    def module(self):
        return self._module

    def save(self):
        Form.saveconfig(self.settings, self.folder)

    @classmethod
    def saveconfig(cls, config, folder):
        writefolderconfig(config, folder, configname='form')


class Project(object):
    def __init__(self, rootfolder, settings):
        self.folder = rootfolder
        self._project = None
        self._splash = None
        self.settings = settings
        self._forms = []
        self.error = ''
        self.basepath = os.path.join(rootfolder,"..")

    @classmethod
    def from_folder(cls, rootfolder):
        project = cls(rootfolder, {})
        project.settings = readfolderconfig(rootfolder, configname='project')
        return project

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self._settings = value

    @property
    def name(self):
        default = os.path.basename(self.folder)
        return self.settings.setdefault("title", default)
        
    @property
    def description(self):
        return self.settings.setdefault("description", '')
        
    @property
    def version(self):
        return str(self.settings.setdefault("version", roam.__version__))
    
    @property
    def projectfile(self):
        return glob.glob(os.path.join(self.folder, '*.qgs'))[0]

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

        if not checkversion(roam.__version__, self.version):
            error = "Version mismatch"
            yield error

    @property
    def valid(self):
        """
        Check if this project is valid or not.  Call validate for more detail on errors
        :return: True if this project is valid.
        """
        return not list(self.validate())

    @property
    def splash(self):
        if not self._splash:
            try:
                self._splash = glob.glob(os.path.join(self.folder, 'splash.png'))[0]
            except IndexError:
                self._splash = ''
            
        return self._splash
    
    def syncprovders(self):
        providers = self.settings.get("providers", {})
        for name, config in providers.iteritems():
            cmd = config['cmd']
            cmd = os.path.join(self.folder, cmd)
            if config['type'] == 'replication' or config['type'] == 'batch':
                yield replication.BatchFileSync(name, cmd)
    
    def getPanels(self):
        for module in glob.iglob(os.path.join(self.folder, "_panels", '*.py')):
            modulename = os.path.splitext(os.path.basename(module))[0]
            try:
                panelmod = imp.load_source(modulename, module)
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
            name = os.path.basename(self.folder)
            module = importlib.import_module("{}".format(name))
        except ImportError as err:
            log(err)
            print err
            return True, None
            
        try:
            return module.onProjectLoad()
        except AttributeError as err:
            log("Not onProjectLoad attribute found")
            print "No onProjectLoad attribute found"
            return True, None

    def formsforlayer(self, layername):
        for form in self.forms:
            if form.layername == layername:
                yield form

    @property
    def forms(self):
        def mapformconfig(forms):
            if hasattr(forms, 'iteritems'):
                for formname, config in forms.iteritems():
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
                form = Form.from_config(formname, config, folder)
                self._forms.append(form)

        return self._forms

    @property
    def selectlayers(self):
        return self.settings.get('selectlayers', [])


    def selectlayersmapping(self):
        """
        Return the mapping between the select layers listed in settings
        and the QGIS layer itself.

        If no select layers are found in the settings this function will return
        all layers in the project
        """
        return layersfromlist(self.selectlayers)

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

        if hasattr(forms, 'iteritems'):
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
        forms = self.settings.setdefault("forms", [])
        if hasattr(forms, 'iteritems'):
           del self.settings['forms'][name]
        else:
            index = forms.index(name)
            del self.settings['forms'][index]

    def save(self):
        """
        Save the project config to disk.
        """
        writefolderconfig(self.settings, self.folder, configname='project')
        formsstorage = self.settings.setdefault("forms", [])
        if not hasattr(formsstorage, 'iteritems'):
            for form in self.forms:
                debug("Saving {}".format(form.name))
                debug(form.settings)
                form.save()

    @property
    def oldformconfigstlye(self):
        formsstorage = self.settings.get("forms", [])
        return hasattr(formsstorage, 'iteritems')


    def hascapturelayers(self):
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        layers = (layer for layer in layers if layer.type() == QgsMapLayer.VectorLayer)
        layers = [layer.name() for layer in layers if layer.geometryType() in supportedgeometry]
        for layer in self.selectlayers:
            if layer in layers:
                return True
        return False

    def getPlugins(self):
        filteredplugins={}
        configuredplugins = self.settings.get("plugins", [])
        configuredplugins.append("Legend")
        for page, config in plugins.registeredpages.iteritems():
            if page in configuredplugins:
                filteredplugins[page] = config
        return filteredplugins

