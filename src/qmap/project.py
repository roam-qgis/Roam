import os
import glob
import utils
import json

def getProjects(projectpath):
    folders = (sorted( [os.path.join(projectpath, item) 
                       for item in os.walk(projectpath).next()[1]]))
    
    for folder in folders:
        # The folder name is the display name
        # Grab the first project file
        # Look for splash.png
        # Path to project folder.       
        yield QMapProject(folder)
        
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
        self._qgslayer = layer

    @property
    def mapTool(self):
        """
            Returns the map tool configured for this layer.
        """
        raise NotImplementedError
        

class QMapProject(object):
    """
        A QMap project represented as a folder on the disk.  Each project folder
        can contain a single QGIS project, a splash icon, name, and a list of layer folders.
    """
    def __init__(self, rootfolder):
        self.folder = rootfolder
        self._project = None
        self._splash = None 
        self._isVaild = True
        
    @property
    def name(self):
        return os.path.basename(self.folder)
    
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
    
    def getConfiguredLayers(self):
        """
        Return all the layers that have been configured for this project. Layers are represented as 
        folders.
        """
        for layerfolder in os.walk(self.folder).next()[1]:
            if layerfolder.startswith('_'):
                continue
            
            yield QMapLayer(os.path.join(self.folder, layerfolder), self)
    
    @property
    def settings(self):
        settings = os.path.join(self.folder, "settings.config")
        try:
            with open(settings,'r') as f:
                return json.load(f)
        except IOError as e:
            utils.warning(e)
            return None
        
    @property
    def layersettings(self):
        return self.settings["layers"]
        
    
    
    
    
    
    
    
    
    
    
    
    
        