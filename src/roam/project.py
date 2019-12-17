import glob
import os
from collections import OrderedDict

from qgis.PyQt.QtCore import pyqtSignal, QObject
from qgis.core import QgsWkbTypes, QgsMapLayer, QgsProject

import roam
import roam.api.utils
import roam.maptools
import roam.qgisfunctions
import roam.utils
from roam.api import FeatureForm
from roam.config import writefolderconfig, readfolderconfig, ConfigLoadError
from roam.dataaccess.database import Database
from roam.roam_form import Form
from roam.syncing import replication
from roam.utils import log

# This of supported geometry types for the forms.
supportedgeometry = [QgsWkbTypes.PointGeometry,
                     QgsWkbTypes.PolygonGeometry,
                     QgsWkbTypes.LineGeometry]


class ProjectExpection(Exception):
    """
    Raised when there is a issue with a project.
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


def versiontuple(v):
    v = v.split('.')[:3]
    version = tuple(map(int, (v)))
    if len(version) == 2:
        version = (version[0], version[1], 0)
    return version


def checkversion(roamversion, projectversion):
    if not projectversion:
        return True

    min = versiontuple(roamversion)
    project = versiontuple(projectversion)
    # Only match major for now because API is only broken between major versions.
    majormatch = min[0] == project[0]
    return majormatch


def version_major_part(version):
    """
    Return the major part of the version string
    :param version: The input version in the format of x.y.z
    :return: The major X part of the version string.
    """
    return versiontuple(version)[0]


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


class Project(QObject):
    projectUpdated = pyqtSignal(object)

    def __init__(self, rootfolder, settings):
        super(Project, self).__init__()
        print("init")
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
        except ConfigLoadError as error:
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

    def upgrade_roam_version(self):
        """
        Update the roam version this project was saved as
        """
        self.settings['version'] = roam.__version__

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
            error = "Roam project version incompatible. \n" \
                    "Please contact Roam administrator. \n" \
                    "Project Roam version {} but needed version at least {} or above".format(version_major_part(self.roamversion),
                                                                                    version_major_part(roam.__version__))
            yield error

        if self.configError:
            error = "Project has config error: {0}".format(self.configError)
            yield error

    @property
    def requires_upgrade(self):
        """
        Return if this project requires a upgrade before it can be loaded
        """
        same_version = checkversion(roam.__version__, self.roamversion)
        if not same_version:
            if version_major_part(roam.__version__) > version_major_part(self.roamversion):
                return True

        return False

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
            synctype = config.get('type', "replication")
            if synctype in ['replication', 'batch']:
                config['cmd'] = cmd
                config.setdefault('variables', variables)
                config.update(variables)
                yield replication.BatchFileSync(name, self, **config)

    @property
    def module(self):
        import imp
        rootfolder = os.path.abspath(os.path.join(self.folder, '..'))
        name = os.path.basename(self.folder)
        module = imp.find_module(name, [rootfolder])
        module = imp.load_module(name, *module)
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
        self.upgrade_roam_version()

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
