import pkgutil
import sys
import importlib
from PyQt5.QtCore import QSize, pyqtSignal, Qt
from PyQt5.QtWidgets import QToolBar

from roam.api import RoamEvents, GPS

loaded_plugins = {}
api = None


# from roam.gui import HideableToolbar

class HideableToolbar(QToolBar):
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(HideableToolbar, self).__init__(parent)
        self.startstyle = None

    def mouseDoubleClickEvent(self, *args, **kwargs):
        currentstyle = self.toolButtonStyle()
        if currentstyle == Qt.ToolButtonIconOnly:
            self.setSmallMode(False)
        else:
            self.setSmallMode(True)

    def setSmallMode(self, smallmode):
        currentstyle = self.toolButtonStyle()

        if self.startstyle is None:
            self.startstyle = currentstyle

        if not smallmode:
            self.setToolButtonStyle(self.startstyle)
        else:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.stateChanged.emit(smallmode)

    def setToolButtonStyle(self, style):
        super(HideableToolbar, self).setToolButtonStyle(style)


def safe_connect(method, to):
    try:
        method.connect(to)
    except AttributeError:
        pass


class Page(object):
    title = ""
    icon = ""
    projectpage = True

    def selection_changed(self, selection):
        """
        Auto connected selection changed event.
        :param selection:
        :return:
        """
        pass

    def project_loaded(self, project):
        """
        Auto connected projet loaded event
        """
        pass


class ToolBar(HideableToolbar):
    def __init__(self, parent=None):
        super(ToolBar, self).__init__()

        self.setIconSize(QSize(32, 32))
        self.setMovable(False)

        RoamEvents.selectionchanged.connect(self.selection_changed)
        RoamEvents.activeselectionchanged.connect(self.active_selection_changed)
        RoamEvents.projectloaded.connect(self.project_loaded)

    def active_selection_changed(self, layer, feature, features):
        pass

    def selection_changed(self, selection):
        """
        Auto connected selection changed event.
        :param selection:
        :return:
        """
        pass

    def project_loaded(self, project):
        """
        Auto connected projet loaded event
        """
        pass

    def unload(self):
        """
        Called when the toolbar is unloaded from the interface
        """
        pass


def find_plugins(pluginfolders=None):
    """
    Return all the plugins found in the given folders.
    :param pluginfolders: A None or a list of folders to look for plugins.
    :return: The name of each plugin.
    """
    for loader, name, ispkg in pkgutil.iter_modules(pluginfolders):
        if name.endswith("_plugin"):
            sys.path.append(loader.path)
            yield name


def load_plugin(pluginname):
    mod = importlib.import_module(pluginname)
    loaded_plugins[pluginname] = mod
    return pluginname, mod


def load_plugins_from(pluginfolders=None):
    """
    Load all the plugins found in the given folder
    :param pluginfolders: None or list of folders to look for plugins.
    :return: A dict of pluginname: module for each loaded plugin.
    """
    loadedplugins = {}
    for plugin in find_plugins(pluginfolders):
        loadedplugins[plugin] = load_plugin(plugin)
    return loadedplugins
