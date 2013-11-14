__author__ = 'nathan.woodrow'

from qmap.editorwidgets import listwidget, checkboxwidget, textwidget
from qmap.editorwidgets.core import WidgetsRegistry

factories = [listwidget.factory,
             checkboxwidget.factory,
             textwidget.factory]

WidgetsRegistry.registerFactories(factories)

