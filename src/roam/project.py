import os
import glob
import utils
import yaml
import functools
import imp
import importlib

from PyQt4.QtGui import QAction, QIcon

from qgis.core import QgsMapLayerRegistry, QGis, QgsTolerance, QgsVectorLayer, QgsMapLayer

from roam.maptools import PointTool, InspectionTool, EditTool
from roam.utils import log
from roam.syncing import replication
from roam.featuredialog import FeatureForm
from roam.orderedyaml import OrderedDictYAMLLoader

import roam.utils


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


def getProjects(projectpath):
    """
    Return QMapProjects inside the set path.  
    Each folder will be considered a QMap project
    """
    folders = (sorted( [os.path.join(projectpath, item)
                       for item in os.walk(projectpath).next()[1]]))
    
    for folder in folders:
        project = Project.from_folder(folder)
        if project.valid:
            yield project
        else:
            roam.utils.warning("Invaild project")
            roam.utils.warning(project.error)


class Form(object):
    def __init__(self, name, config, rootfolder, project):
        self._name = name
        self.settings = config
        self.folder = rootfolder
        self.project = project
        self._module = None
        self.errors = []

    @classmethod
    def from_config(cls, name, config, project):
        folder = os.path.join(self.folder, name)
        form = cls(name, config, folder, project)
        form._loadmodule()
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
        def getlayer(name):
            try:
                return QgsMapLayerRegistry.instance().mapLayersByName(name)[0]
            except IndexError as e:
                utils.log(e)
                return None

        layer = getlayer(self.layername)
        return layer

    def getMaptool(self, canvas):
        """
            Returns the map tool configured for this layer.
        """
        def _getEditTool():
            radius = 10
            tool = EditTool(canvas = canvas, layers = [self.QGISLayer])
            tool.searchRadius = radius
            return tool
        
        def _getInsectionTool():
            """
            """
            try:
                sourcelayername = toolsettings["sourcelayer"]
                sourcelayer = self._getLayer(sourcelayername)
                destlayername = toolsettings["destlayer"]
                destlayer = self._getLayer(destlayername)
                fieldmapping = toolsettings["mapping"]
                validation = toolsettings.get("validation", None)
                if destlayer is None or sourcelayer is None:
                    raise ErrorInMapTool("{} or {} not found in project".format(sourcelayername, destlayername))

                modulename, method = os.path.splitext(validation)
                method = method[1:]

                try:
                    projectfolder = os.path.basename(self.project.folder)
                    name = "projects.{project}.{layer}.{module}".format(project=projectfolder,
                                                                        module=modulename,
                                                                        layer=self.name)
                    validationmod = importlib.import_module(name)
                    log(dir(validationmod))
                    validation_method = getattr(validationmod, method)
                except ImportError as err:
                    error = "Validation import error {}".format(err)
                    log(error)
                    raise ErrorInMapTool(error)
                except AttributeError:
                    error = "No method in {} called {} found".format(modulename, method)
                    log(error)
                    raise ErrorInMapTool(error)

                return InspectionTool(canvas=canvas, layerfrom=sourcelayer, 
                                      layerto=destlayer, mapping=fieldmapping, 
                                      validation_method=validation_method)
            except KeyError as e:
                utils.log(e)
                raise ErrorInMapTool(e)
            
        tools = {
                 "inspection" : _getInsectionTool,
                 "edit" : _getEditTool
                 }
                
        try:
            toolsettings = self.settings["maptool"]
            tooltype = toolsettings["type"]
            return tools[tooltype]()
        except KeyError:
            pass
        
        if self.QGISLayer.geometryType() == QGis.Point:
            return PointTool(canvas)
        
        raise NoMapToolConfigured

    @property
    def action(self):
        """
        The GUI action that can be used for this layer
        """
        action = QAction(QIcon(self.icon), "Capture", None)
        action.setData(self)
        action.setCheckable(True)
        return action

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

    @property
    def featureform(self):
        return FeatureForm.from_form(self, self.settings)
        
    def widgetswithdefaults(self):
        """
        Return any widget configs that have default values needed
        """
        for config in self.widgets:
            if 'default' in config:
                yield config['field'], config

    def _loadmodule(self):
        projectfolder = os.path.basename(self.project.folder)
        name = "projects.{project}.{formfolder}".format(project=projectfolder, formfolder=self.name)
        try:
            self._module = importlib.import_module(name)
        except ImportError as err:
            log(err)
            self.errors.append(err.message)
            self._module = None

    @property
    def module(self):
        return self._module

    def accept(self):
        #TODO Call form module accept method
        return True

    def reject(self):
        #TODO Call form module reject method
        return True

    def onformloading(self, form, feature, layers, editing):
        """
        Called before the form is loaded. This method can be used to do pre checks and halt the loading of the form
        if needed.

        When implemented, this method should always return a tuple with a pass state and a message.

        Returning (True, None) will let the form continue to be opened.
        Returning (False, "Message") will stop the opening of the form and show the message to the user.

        You may alter the QgsFeature given. You can access form settings using:

            >>> form.settings

        You can get the QGIS layer for the form using:

            >>> form.QGISLayer
        """
        try:
            return self.module.formloading(form, feature, layers, editing)
        except AttributeError as err:
            log("No formloading attribute found. Assuming pass")
            return True, None


class Project(object):

    def __init__(self, rootfolder, settings):
        self.folder = rootfolder
        self._project = None
        self._splash = None 
        self.valid = True
        self.settings = {}
        self.error = ''

    @classmethod
    def from_folder(cls, rootfolder):
        settings = os.path.join(rootfolder, "settings.config")
        project = cls(rootfolder, {})
        try:
            with open(settings,'r') as f:
                settings = yaml.load(f, Loader=OrderedDictYAMLLoader)
                project.settings = settings
        except IOError as e:
            project.valid = False
            project.error = "No settings.config found in {} project folder".format(folder)
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
        return self.settings.get("version", 1.00)
    
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
            if config['type'] == 'replication':
                yield replication.ReplicationSync(name, cmd)
    
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
            module = importlib.import_module("projects.{}".format(name))
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
        for formname, config in self.settings.get("forms", {}).iteritems():
            yield Form.from_config(formname, config, self)

    @property
    def selectlayers(self):
        return self.settings.get('selectlayers', [])

    def historyenabled(self, layer):
        return layer.name() in self.settings.get('historylayers', [])