from PyQt4.QtGui import QWidget
from PyQt4.QtCore import QObject, pyqtSignal
from collections import OrderedDict


widgets = OrderedDict()

class EditorWidgetException(Exception):
    pass


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
    from roam.editorwidgets.tablewidget import TableWidget
    from roam.editorwidgets.optionwidget import OptionWidget
    from roam.editorwidgets.attachmentwidget import AttachmentWidget

    registerwidgets(ImageWidget, ListWidget, MultiList, CheckboxWidget, DateWidget,
                    NumberWidget, DoubleNumberWidget, TextWidget, TextBlockWidget, OptionWidget, AttachmentWidget)


def supportedwidgets():
    return widgets.keys()


def widgetwrapper(widgettype, widget, config, layer, label, field, context=None, parent=None):
    if not context:
        context = {}
    try:
        editorwidget = widgets[widgettype]
    except KeyError:
        raise EditorWidgetException("No widget wrapper for type {} was found".format(widgettype))

    widgetwrapper = editorwidget.for_widget(widget, layer, label, field, parent)
    widgetwrapper.context = context
    config['context'] = context
    widgetwrapper.initWidget(widget, config)
    widgetwrapper.config = config
    return widgetwrapper


def createwidget(widgettype, parent=None):
    try:
        wrapper = widgets[widgettype]
    except KeyError:
        raise EditorWidgetException("No widget wrapper for type {} was found".format(widgettype))

    return wrapper.createwidget(parent=parent)


class EditorWidget(QObject):
    validationupdate = pyqtSignal(object, bool)
    valuechanged = pyqtSignal(object)

    # Signal to emit when you need to show a large widget in the UI.
    largewidgetrequest = pyqtSignal(object, object, object, dict)

    def __init__(self, widget=None, layer=None, label=None, field=None, parent=None, *args, **kwargs):
        QObject.__init__(self, parent)
        self._config = {}
        self.modified = False
        self.widget = widget
        self.layer = layer
        self.field = field
        self.label = label
        self.context = {}
        self.formwidget = None
        self._required = False
        self._readonly = True
        self.initconfig = kwargs.get('initconfig', {})
        self.newstyleform = False
        self.starttext = ''
        self.id = ''
        self.default_events = ['capture']
        self.valuechanged.connect(self.updatecontrolstate)

    @classmethod
    def for_widget(cls, widget, layer, label, field, parent, *args, **kwargs):
        """
        Create a new editor wrapper for the given widget.
        """
        editor = cls(widget, layer, label, field, parent, *args, **kwargs)
        return editor

    @classmethod
    def createwidget(cls, parent=None, config=None):
        """
        Creates the widget that wrapper supports.
        """
        if not config:
            config = {}

        return cls(initconfig=config).createWidget(parent)

    def open_large_widget(self, widget, startvalue, callback, config=None):
        """
        Request to open a large widget.
        :param widget: The widget of type LargeEditorWidget to open
        :param startvalue: The value to preload the widget with.
        :param callback: Callback used when the value is set in the widget.
        :param config: The config passed to the widget.
        :return: None
        """
        if not config:
            config = {}
        self.largewidgetrequest.emit(widget, startvalue, callback, config)

    @property
    def passing(self):
        """
        Returns True of the widget is in a passing validation state.

        Widgets that are hidden can still pass validation
        :return:
        """
        if not self.required:
            return True

        if self.required and not self.hidden:
            return self.validate()
        else:
            return True

    @property
    def readonly(self):
        return self._readonly

    @readonly.setter
    def readonly(self, value):
        self._readonly = value
        self.setEnabled(not value)

    @property
    def hidden(self):
        return self._hidden

    @hidden.setter
    def hidden(self, value):
        self._hidden = value
        self.widget.setVisible(not value)
        self.buddywidget.setVisible(not value)

    def updatecontrolstate(self, value):
        if self.label is None or not self.required:
            return

        if self.passing:
            self.label.setText("{}".format(self.starttext))
        else:
            requiredtext = "required" if self.newstyleform else "*"
            self.label.setText("{} <b style='color:red'>({})</b>".format(self.starttext, requiredtext))

    def setrequired(self):
        self.required = True

    @property
    def required(self):
        return self._required

    @required.setter
    def required(self, state):
        if not self.starttext and state:
            self.starttext = self.labeltext

        if state and self.label:
            requiredtext = "required" if self.newstyleform else "*"
            self.label.setText("{} <b style='color:red'>({})</b>".format(self.starttext, requiredtext))

        self._required = state

    @property
    def buddywidget(self):
        if not self.label is None:
            return self.label
        else:
            return self.widget

    @property
    def labeltext(self):
        if self.label is None:
            return self.widget.objectName()
        else:
            return self.label.text()

    def setvalue(self, value):
        pass

    def value(self):
        pass

    def validate(self, *args):
        return True

    def setconfig(self, config):
        """
        Alias function for self.config so we can connect it to a signal.
        """
        self.config = config

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value
        self.updatefromconfig()

    def updatefromconfig(self):
        """
        Called when the config of the widget changes.

        When overloading you should call this base class function
        in order to save the current value before updating from the config.

        Your overloaded method should call endupdatefromconfig in order
        to restore the last value.
        """
        self._lastvalue = self.value()

    @property
    def get_default_value_on_save(self):
        return 'save' in self.default_events

    def endupdatefromconfig(self):
        self.setvalue(self._lastvalue)

    def createWidget(self, parent):
        pass

    def initWidget(self, widget, config):
        pass

    def setEnabled(self, enabled):
        if not self.widget is None:
            self.widget.setEnabled(enabled)

    def emitvaluechanged(self, *args):
        """
        Emit the value changed signal.
        :param args: Ignored.  Just a sink so we can connect it to any signal.
        :return:
        """
        self.valuechanged.emit(self.value())

    def extraData(self):
        """
        Returns extra field mappings and data this widget can write.
        Some widgets add extra information to fields that are not bound.
        Example: Image widget can write the GPS position to a {field}_GPS fields
        to include GPS information.
        """
        return {}

class RejectedException(Exception):
    WARNING = 1
    ERROR = 2

    def __init__(self, message, level=WARNING):
        super(RejectedException, self).__init__(message)
        self.level = level

class LargeEditorWidget(EditorWidget):
    """
    A large editor widget will take up all the UI before the action is finished.
    These can be used to show things like camera capture, drawing pads, etc

    The only thing this class has extra is a finished signal and emits that once input is complete.
    """
    finished = pyqtSignal(object)
    cancel = pyqtSignal(object, int)

    def __init__(self, *args, **kwargs):
        EditorWidget.__init__(self, *args, **kwargs)

    def emit_finished(self):
        self.finished.emit(self.value())

    def emit_cancel(self, reason=None, level=1):
        self.cancel.emit(reason, level)

    def before_load(self):
        """
        Called before the widget is loaded into the UI
        """
        pass

    def after_load(self):
        """
        Called after the widget has been loaded into the UI
        """
        pass
