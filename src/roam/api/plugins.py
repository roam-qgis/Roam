import pkgutil
import sys
import importlib

loaded_plugins = {}

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

