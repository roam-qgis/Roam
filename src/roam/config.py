"""
Config file loading logic for Roam.
"""
import os

import yaml
from qgis.PyQt.QtCore import QSize
from yaml.reader import ReaderError
from yaml.scanner import ScannerError

import roam.utils

settings = {}

loaded_path = ''


class ConfigLoadError(Exception):
    pass


def read_qsize(key):
    """
    Read a size from the settings into the QSize.
    :param key: The key to search.
    :return:
    """
    size = settings.get(key, None)
    if not size:
        return QSize()

    try:
        w, h = size.split(',')
        w, h = int(w.strip()), int(h.strip())
        return QSize(w, h)
    except ValueError:
        return QSize()


def load(path):
    with open(path, 'r') as f:
        global settings
        try:
            settings = yaml.load(f)
        except ReaderError:
            settings = {}
        if settings is None:
            settings = {}
        global loaded_path
        loaded_path = path


def save(path=None):
    """
    Save the settings to disk. The last path is used if no path is given.
    :param path:
    :return:
    """
    if not path:
        path = loaded_path

    with open(path, 'w') as f:
        yaml.dump(data=settings, stream=f, default_flow_style=False)


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
                raise ConfigLoadError(str(ex))
        return settings
    except IOError as e:
        roam.utils.warning(e)
        roam.utils.warning("Returning empty settings for settings.config")
        return {}