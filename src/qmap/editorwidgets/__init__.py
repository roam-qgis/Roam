__author__ = 'nathan.woodrow'

from qmap.editorwidgets import (listwidget,
                                checkboxwidget,
                                textwidget,
                                datewidget,
                                imagewidget)

from qmap.editorwidgets.core import WidgetsRegistry

factories = [listwidget.factory,
             checkboxwidget.factory,
             textwidget.factory,
             datewidget.factory,
             imagewidget.factory]

WidgetsRegistry.registerFactories(factories)

