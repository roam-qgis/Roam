__author__ = 'nathan.woodrow'

import os

from PyQt4 import uic


def create_ui(filename):
    basepath = os.path.dirname(__file__)
    uipath = os.path.join(basepath, filename)
    return uic.loadUiType(uipath)