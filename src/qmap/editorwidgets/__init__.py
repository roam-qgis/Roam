__author__ = 'nathan.woodrow'

from qmap.editorwidgets import listwidget, checkboxwidget, textwidget, datewidget
from qmap.editorwidgets.core import WidgetsRegistry

factories = [listwidget.factory,
             checkboxwidget.factory,
             textwidget.factory,
             datewidget.factory]

WidgetsRegistry.registerFactories(factories)

