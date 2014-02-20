__author__ = 'nathan.woodrow'

import sys
import os

# We have to add this to PATH because the ui builder
# can't seem to find them :S

uipath = os.path.join(os.path.dirname(__file__), 'uifiles')
sys.path.append(uipath)

from roam.editorwidgets.listwidget import ListWidget
from roam.editorwidgets.checkboxwidget import CheckboxWidget
from roam.editorwidgets.datewidget import DateWidget
from roam.editorwidgets.textwidget import TextBlockWidget, TextWidget
from roam.editorwidgets.imagewidget import ImageWidget

from roam.editorwidgets.core import WidgetsRegistry

supportedwidgets = [ListWidget, CheckboxWidget, DateWidget, TextBlockWidget,
                   TextWidget, ImageWidget]

WidgetsRegistry.registerwidgets(supportedwidgets)


