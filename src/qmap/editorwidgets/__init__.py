__author__ = 'nathan.woodrow'

from qmap.editorwidgets import listwidget
from qmap.editorwidgets.core import WidgetsRegistry

factories = [listwidget.factory]

WidgetsRegistry.registerFactories(factories)