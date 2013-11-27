__author__ = 'nathan.woodrow'

import sys
import os

# We have to add this to PATH because the ui builder
# can't seem to find them :S

uipath = os.path.join(os.path.dirname(__file__), 'uifiles')
sys.path.append(uipath)


from roam.editorwidgets import (listwidget,
                                checkboxwidget,
                                textwidget,
                                datewidget,
                                imagewidget)

from roam.editorwidgets.core import WidgetsRegistry

factories = [listwidget.factory,
             checkboxwidget.factory,
             textwidget.factory,
             datewidget.factory,
             imagewidget.factory]

WidgetsRegistry.registerFactories(factories)

