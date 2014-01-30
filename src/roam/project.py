import os
import glob
import utils
import yaml
import functools
import imp
import importlib
import sys

from PyQt4.QtGui import QAction, QIcon

from qgis.core import QgsMapLayerRegistry, QGis, QgsTolerance, QgsVectorLayer, QgsMapLayer

from roam.maptools import PointTool, InspectionTool, EditTool
from roam.utils import log
from roam.syncing import replication
from roam.featureform import FeatureForm
from roam.structs import OrderedDictYAMLLoader

import roam.utils
import roam


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
    majormatch = min[0] == project[0]
    return majormatch and (project > min or project == min)


def getProjects(projectpath):
    """
    Return QMapProjects inside the set path.  
    Each folder will be considered a QMap project
    """
    folders = (sorted([os.path.join(projectpath, item)
                       for item in os.walk(projectpath).next()[1]]))
    
    for folder in folders:
        project = Project.from_folder(folder)
        if not checkversion(roam.__version__, project.version):
            project.valid = False
            project.error = "Version mismatch"

        yield project


class Form(object):
    def __init__(self, name, config, rootfolder):
        self._name = name
        self.settings = config
        self.folder = rootfolder
        self._module = None
        self.errors = []
        self._qgislayer = None
        self._formclass = None

    @classmethod
    def from_config(cls, name, config, folder):
        def getlayer(name):
            try:
                return QgsMapLayerRegistry.instance().mapLayersByName(name)[0]
            except IndexError as e:
                utils.log(e)
                return None

        form = cls(name, config, folder)
        form.QGISLayer = getlayer(config['layer'])
        form._loadmodule()
        form.init_form()
        return form

    @property
    def label(self):
        return self.settings.get('label', self.name)

    @property
    def name(self):
        return self._name

    @property
    def icontext(self):
        return self.label

    @property
    def layername(self):
        return self.settings['layer']

    @property
    def icon(self):
        iconpath = os.path.join(self.folder, 'icon.png')
        utils.log(iconpath)
        return iconpath

    @property
    def QGISLayer(self):
        return self._qgislayer

    @QGISLayer.setter
    def QGISLayer(self, value):
        self._qgislayer = value

    def getMaptool(self, canvas):
        """
            Returns the map tool configured for this layer.
        """
        if self.QGISLayer.geometryType() == QGis.Point:
            return PointTool(canvas)
        
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
        return self.settings.get('widgets', [])

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

    def create_featureform(self, feature, defaults):
        """
        Creates and returns the feature form for this Roam form
        """
        return self.formclass.from_form(self, self.settings, feature, defaults)

    def widgetswithdefaults(self):
        """
        Return any widget configs that have default values needed
        """
        for config in self.widgets:
            if 'default' in config:
                yield config['field'], config

    def _loadmodule(self):
        projectfolder = os.path.abspath(os.path.join(self.folder, '..'))
        projectname = os.path.basename(projectfolder)
        name = "{project}.{formfolder}".format(project=projectname, formfolder=self.name)
        try:
            self._module = importlib.import_module(name)
        except ImportError as err:
            log(sys.path)
            log(err)
            self.errors.append(err.message)
            self._module = None

    @property
    def module(self):
        return self._module


class Project(object):
    def __init__(self, rootfolder, settings):
        self.folder = rootfolder
        self._project = None
        self._splash = None 
        self.valid = True
        self.settings = settings
        self._forms = []
        self.error = ''

    @classmethod
    def from_folder(cls, rootfolder):
        settings = os.path.join(rootfolder, "settings.config")
        project = cls(rootfolder, {})
        try:
            with open(settings, 'r') as f:
                settings = yaml.load(f)
                project.settings = settings
        except IOError as e:
            project.valid = False
            project.error = "No settings.config found in {} project folder".format(rootfolder)
            utils.warning(e)
        return project

    @property
    def name(self):
        default = os.path.basename(self.folder)
        return self.settings.get("title", default)
        
    @property
    def description(self):
        return self.settings.get("description", '')
        
    @property
    def version(self):
        return str(self.settings.get("version", roam.__version__))
    
    @property
    def projectfile(self):
        if not self._project:
            try:
                self._project = glob.glob(os.path.join(self.folder, '*.qgs'))[0]
            except IndexError:
                self.error = "No QGIS project found in the {} project folder".format(self.name)
                self.valid = False
        return self._project
    
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
    
    def getConfiguredLayers(self):
        """
        Return all the layers that have been configured for this project. Layers are represented as 
        folders.
        """
        for layerfolder in os.walk(self.folder).next()[1]:
            if layerfolder.startswith('_'):
                continue
            
            yield QMapLayer(os.path.join(self.folder, layerfolder), self)

    def layer(self, layername):
        for layer in self.getConfiguredLayers():
            if layer.name == layername:
                return layer

    def getPanels(self):
        log("getPanels")
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
        if not self._forms:
            for formname, config in self.settings.get("forms", {}).iteritems():
                folder = os.path.join(self.folder, formname)
                form = Form.from_config(formname, config, folder)
                self._forms.append(form)
        return self._forms

    @property
    def selectlayers(self):
        return self.settings.get('selectlayers', [])

    def historyenabled(self, layer):
        return layer.name() in self.settings.get('historylayers', [])