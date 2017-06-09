"""
Config file loading logic for Roam.
"""
import os
import yaml
from yaml.reader import ReaderError
from PyQt4.QtCore import QSize

settings = {}

loaded_path = ''



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


