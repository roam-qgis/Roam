import os
import glob
import utils
import yaml
import functools
from maptools import PointTool, InspectionTool, EditTool
from qgis.core import QgsMapLayerRegistry, QGis, QgsTolerance, QgsVectorLayer
from utils import log
from syncing import replication
import imp
import importlib

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

def getProjects(projectpath, iface=None):
    """
    Return QMapProjects inside the set path.  
    Each folder will be considered a QMap project
    """
    folders = (sorted( [os.path.join(projectpath, item) 
                       for item in os.walk(projectpath).next()[1]]))
    
    for folder in folders:      
        yield QMapProject(folder, iface)
        
class QMapLayer(object):
    """
    A QMap layer represented as a folder on the disk.
    """
    def __init__(self, rootfolder, project):
        self.folder = rootfolder
        self.project = project
        
    @property
    def name(self):
        return os.path.basename(self.folder)
    
    @property
    def icontext(self):
        try:
            return self.project.layersettings[self.name]["label"]
        except KeyError:
            return self.name
         
    @property
    def icon(self):
        utils.log(os.path.join(self.folder, 'icon.png'))
        return os.path.join(self.folder, 'icon.png')
    
    @property
    def QGISLayer(self):
        return self._qgslayer
    
    @QGISLayer.setter
    def QGISLayer(self, layer):
        # If the layer has a ui file then we need to rewrite to be relative
        # to the current projects->layer folder as QGIS doesn't support that yet.
        if layer.editorLayout() == QgsVectorLayer.UiFileLayout:
            form = os.path.basename(layer.editForm())
            newpath = os.path.join(self.folder, form)
            layer.setEditForm(newpath)
            self.project.iface.preloadForm(newpath)

        self._qgslayer = layer
        
    def _getLayer(self, name):
        try:
            return QgsMapLayerRegistry.instance().mapLayersByName(name)[0]
        except IndexError as e:
            utils.log(e)
            return None
        
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
            try:
                sourcelayername = toolsettings["sourcelayer"]
                sourcelayer = self._getLayer(sourcelayername)
                destlayername = toolsettings["destlayer"]
                destlayer = self._getLayer(destlayername)
                fieldmapping = toolsettings["mapping"]
                if destlayer is None or sourcelayer is None:
                    raise ErrorInMapTool("{} or {} not found in project".format(sourcelayername, destlayername))
                
                return InspectionTool(canvas=canvas, layerfrom=sourcelayer, 
                                      layerto=destlayer, mapping=fieldmapping  )
            except KeyError as e:
                utils.log(e)
                raise ErrorInMapTool(e)
            
        tools = {
                 "inspection" : _getInsectionTool,
                 "edit" : _getEditTool
                 }
                
        try:
            toolsettings = self.project.layersettings[self.name]["maptool"]
            tooltype = toolsettings["type"]
            return tools[tooltype]()
        except KeyError:
            pass
        
        if self.QGISLayer.geometryType() == QGis.Point:
            return PointTool(canvas)
        
        raise NoMapToolConfigured
    
    @property
    def capabilities(self):
        """
            The configured capabilities for this layer.
        """
        try:
            rights = self.project.layersettings[self.name]["capabilities"]
            return rights
        except KeyError:
            return ['capture', 'edit', 'move']
        

class QMapProject(object):
    """
        A QMap project represented as a folder on the disk.  Each project folder
        can contain a single QGIS project, a splash icon, name, 
        and a list of layer represented as folders.
    """
    def __init__(self, rootfolder, iface):
        self.folder = rootfolder
        self._project = None
        self._splash = None 
        self._isVaild = True
        self.iface = iface
        
    @property
    def name(self):
        try:
            return self.settings["title"]
        except KeyError:
            return os.path.basename(self.folder)
        
    @property
    def description(self):
        try:
            return self.settings["description"]
        except KeyError:
            return ''
    
    @property
    def projectfile(self):
        if not self._project:
            try:
                self._project = glob.glob(os.path.join(self.folder, '*.qgs'))[0]
            except IndexError:
                self._isVaild = False
        return self._project
    
    @property
    def vaild(self):
        return self._isVaild
    
    @property
    def splash(self):
        if not self._splash:
            try:
                self._splash = glob.glob(os.path.join(self.folder, 'splash.png'))[0]
            except IndexError:
                self._splash = ''
            
        return self._splash
    
    def getSyncProviders(self):
        for name, config in self.settings["providers"].iteritems():
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

    def getPanels(self):
        log("getPanels")
        for module in glob.iglob(os.path.join(self.folder, "_panels", '*.py')):
            modulename = os.path.splitext(os.path.basename(module))[0]
            log(module)
            try:
                panelmod = imp.load_source(modulename, module)
                yield panelmod.createPanel(self.iface)
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
            module = importlib.import_module("projects.{}".format(self.name))
        except ImportError as err:
            log(err)
            return True, None
            
        try:
            return module.onProjectLoad()
        except AttributeError:
            log("Not onProjectLoad attribute found")
            return True, None
        
    @property
    def settings(self):
        settings = os.path.join(self.folder, "settings.config")
        try:
            with open(settings,'r') as f:
                return yaml.load(f)
        except IOError as e:
            utils.warning(e)
            return None
        
    @property
    def layersettings(self):
        return self.settings["layers"]
        
    
