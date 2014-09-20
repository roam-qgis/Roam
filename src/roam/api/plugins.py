import pkgutil
import sys
import importlib

registeredpages = {}
loaded_plugins = {}

def register_page(name, title, icon, projectpage, widget):
    """
    Register this page for creation in Roam
    :param name:
    :param pageconfig:
    :return:
    """
    pageconfig = dict(title=title,
                      icon=icon,
                      projectpage=projectpage,
                      widget=widget)
    registeredpages[name] = pageconfig

def page(name, title=None, icon=None, projectpage=True):
    """
    Register this page widget with the Roam.

    A registered page will be created by Roam when it's ready.

    :param name: The name of the page.
    :param title: The title shown in the UI. Name is take if this is None
    :param icon: Icon for the page
    :param projectpage: If True this page is only visible when the project is open.
    :return: The page class instance.
    """
    if not title:
        title = name
    def registered_page(PageClass):
        pageconfig = dict(name=name,
                          title=title,
                          icon=icon,
                          projectpage=projectpage,
                          widget=PageClass)
        register_page(**pageconfig)
        return PageClass
    return registered_page

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


if __name__ == "__main__":
    print registeredpages
    print load_plugins_from([r'F:\dev\roam\src\plugins'])
    print loaded_plugins
