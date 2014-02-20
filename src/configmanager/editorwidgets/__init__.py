from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QWidget

from configmanager.editorwidgets.checkwidget import CheckboxWidgetConfig
from configmanager.editorwidgets.datewidget import DateWidgetConfig
from configmanager.editorwidgets.imagewidget import ImageWidgetConfig
from configmanager.editorwidgets.textwidget import TextBlockWidgetConfig, TextWidgetConfig
from configmanager.editorwidgets.listwidget import ListWidgetConfig


widgetconfigs = {"Checkbox" : CheckboxWidgetConfig,
                 "Date": DateWidgetConfig,
                 "Image": ImageWidgetConfig,
                 "List":  ListWidgetConfig,
                 "Text" : TextWidgetConfig,
                 "TextBlock": TextBlockWidgetConfig}