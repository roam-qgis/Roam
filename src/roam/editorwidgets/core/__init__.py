from collections import OrderedDict

from roam.editorwidgets.core.editorwidgetbase import EditorWidget
from roam.editorwidgets.core.largeeditorwidgetbase import LargeEditorWidget
from roam.editorwidgets.core.exceptions import EditorWidgetException, RejectedException

widgets = OrderedDict()


def registerwidgets(*widgetclasses):
    for widgetclass in widgetclasses:
        widgets[widgetclass.widgettype] = widgetclass


def registerallwidgets():
    from roam.editorwidgets.imagewidget import ImageWidget, MultiImageWidget
    from roam.editorwidgets.listwidget import ListWidget, MultiList
    from roam.editorwidgets.checkboxwidget import CheckboxWidget
    from roam.editorwidgets.datewidget import DateWidget
    from roam.editorwidgets.numberwidget import NumberWidget, DoubleNumberWidget
    from roam.editorwidgets.textwidget import TextWidget, TextBlockWidget
    from roam.editorwidgets.optionwidget import OptionWidget
    from roam.editorwidgets.attachmentwidget import AttachmentWidget

    registerwidgets(ImageWidget, ListWidget, MultiList, CheckboxWidget, DateWidget,
                    NumberWidget, DoubleNumberWidget, TextWidget, TextBlockWidget, OptionWidget, AttachmentWidget,
                    MultiImageWidget)


def supportedwidgets():
    return widgets.keys()


def widgetwrapper(widgettype, widget, config, layer, label, field, context=None, parent=None, main_config=None):
    if not context:
        context = {}
    try:
        editorwidget = widgets[widgettype]
    except KeyError:
        raise EditorWidgetException("No widget wrapper for type {} was found".format(widgettype))

    widgetwrapper = editorwidget.for_widget(widget, layer, label, field, parent)
    widgetwrapper.context = context
    config['context'] = context
    widgetwrapper.main_config = main_config
    widgetwrapper.initWidget(widget, config)
    widgetwrapper.config = config
    return widgetwrapper


def createwidget(widgettype, parent=None):
    try:
        wrapper = widgets[widgettype]
    except KeyError:
        raise EditorWidgetException("No widget wrapper for type {} was found".format(widgettype))

    return wrapper.createwidget(parent=parent)


