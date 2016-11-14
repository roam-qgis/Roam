from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QWidget

from configmanager.editorwidgets.checkwidget import CheckboxWidgetConfig
from configmanager.editorwidgets.datewidget import DateWidgetConfig
from configmanager.editorwidgets.imagewidget import ImageWidgetConfig
from configmanager.editorwidgets.textwidget import TextBlockWidgetConfig, TextWidgetConfig
from configmanager.editorwidgets.listwidget import ListWidgetConfig
from configmanager.editorwidgets.numberwidget import NumberWidgetConfig, DoubleNumberWidgetConfig
from configmanager.editorwidgets.optionwidget import OptionWidgetConfig
from configmanager.editorwidgets.attachmentwidget import AttachmentWidgetConfig


widgetconfigs = {"Checkbox" : CheckboxWidgetConfig,
                 "Date": DateWidgetConfig,
                 "Image": ImageWidgetConfig,
                 "MultiImage": ImageWidgetConfig,
                 "List":  ListWidgetConfig,
                 "MultiList" : ListWidgetConfig,
                 "Text" : TextWidgetConfig,
                 "TextBlock": TextBlockWidgetConfig,
                 "Number": NumberWidgetConfig,
                 "Number(Double)": DoubleNumberWidgetConfig,
                 "Attachment": AttachmentWidgetConfig,
                 "Option Row": OptionWidgetConfig}
