from PyQt5.QtCore import QObject, pyqtSignal

import roam.utils


class EditorWidget(QObject):
    validationupdate = pyqtSignal(object, bool)
    valuechanged = pyqtSignal(object)

    # Signal to emit when you need to show a large widget in the UI.
    largewidgetrequest = pyqtSignal(object, object, object, dict)

    def __init__(self, widget=None, layer=None, label=None, field=None, parent=None, *args, **kwargs):
        super(EditorWidget, self).__init__(parent)
        self.logger = roam.utils
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
        if self.label:
            self.starttext = self.label.text()
        else:
            self.starttext = ""
        self.default_events = ['capture']
        self.valuechanged.connect(self.updatecontrolstate)
        self._parent_config = {}

    @property
    def main_config(self):
        return self._parent_config

    @main_config.setter
    def main_config(self, value):
        self._parent_config = value

    @property
    def id(self):
        return self.main_config.get("_id", "")

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

    def updatecontrolstate(self, value=None):
        if self.label is None:
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
        self._required = state
        self.updatecontrolstate()

    @property
    def buddywidget(self):
        if not self.label is None:
            return self.label
        else:
            return self.widget

    @property
    def unformatted_label(self):
        """
        The original label text with any UI formatting.
        :return:
        """
        return self.starttext

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