from PyQt4.QtCore import QObject, pyqtSignal


class EditorWidgetException(Exception):
    pass

# HACK I really don't like all this static state here. Fix me!
class WidgetsRegistry(object):
    widgets = {}

    @staticmethod
    def registerwidgets(widgets):
        for widget in widgets:
            WidgetsRegistry.addWidget(widget.widgettype, widget)

    @staticmethod
    def addWidget(widgettype, widget):
        WidgetsRegistry.widgets[widgettype] = widget

    @staticmethod
    def widgetwrapper(widgettype, widget, config, layer, label, field, parent=None):
        try:
            editorwidget = WidgetsRegistry.widgets[widgettype]
        except KeyError:
            raise EditorWidgetException("No widget wrapper for type {} was found".format(widgettype))

        widgetwrapper = editorwidget.for_widget(widget, layer, label, field, parent)
        widgetwrapper.config = config
        return widgetwrapper

    @staticmethod
    def createwidget(widgettype, parent=None):
        try:
            wrapper = WidgetsRegistry.widgets[widgettype]
        except KeyError:
            raise EditorWidgetException("No widget wrapper for type {} was found".format(widgettype))

        return wrapper.createwidget(parent=parent)


class EditorWidget(QObject):
    validationupdate = pyqtSignal(str, bool)

    def __init__(self, widget=None, layer=None, label=None, field=None, parent=None):
        super(EditorWidget, self).__init__(parent)
        self._config = {}
        self.widget = widget
        self.layer = layer
        self.field = field
        self.label = label
        self.required = False
        self._readonly = True
        self.validationstyle = """QLabel[required=true]
                                {border-radius: 5px; background-color: rgba(255, 221, 48,150);}
                                QLabel[ok=true]
                                { border-radius: 5px; background-color: rgba(200, 255, 197, 150); }"""
        self.validationupdate.connect(self.updatecontrolstate)

    @classmethod
    def for_widget(cls, widget, layer, label, field, parent):
        """
        Create a new editor wrapper for the given widget.
        """
        editor = cls(widget, layer, label, field, parent)
        return editor

    @classmethod
    def createwidget(cls, parent):
        """
        Creates the widget that wrapper supports.
        """
        return cls().createWidget(parent)

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

    def raisevalidationupdate(self, passed):
        if self.required:
            self.validationupdate.emit(self.field, passed)

    def updatecontrolstate(self, field, passed):
        if self.required:
            self.buddywidget.setProperty('ok', passed)
            self.buddywidget.style().unpolish(self.buddywidget)
            self.buddywidget.style().polish(self.buddywidget)

    def setrequired(self):
        self.buddywidget.setStyleSheet(self.validationstyle)
        self.buddywidget.setProperty('required', True)
        self.required = True

    @property
    def buddywidget(self):
        if not self.label is None:
            return self.label
        else:
            return self.widget

    def setvalue(self, value):
        pass

    def value(self):
        pass

    def validate(self, *args):
        pass

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value
        self.initWidget(self.widget)

    def createWidget(self, parent):
        pass

    def initWidget(self, widget):
        pass

    def setEnabled(self, enabled):
        if not self.widget is None:
            self.widget.setEnabled(enabled)

