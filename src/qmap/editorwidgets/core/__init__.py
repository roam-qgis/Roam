from PyQt4.QtCore import QObject, pyqtSignal


class WidgetsRegistry(object):
    widgets = {}

    @staticmethod
    def registerFactories(factories):
        for factory in factories:
            WidgetsRegistry.addWidget(factory)

    @staticmethod
    def addWidget(widgetfactory):
        WidgetsRegistry.widgets[widgetfactory.name] = widgetfactory

    @staticmethod
    def createwidget(widgettype, layer, field, widget, label, config, parent=None):
        if not widgettype in WidgetsRegistry.widgets:
            return None

        factory = WidgetsRegistry.widgets[widgettype]
        widgetwrapper = factory.createWidget(layer, field, widget, label, parent)
        widgetwrapper.config = config
        return widgetwrapper


class WidgetFactory(object):
    def __init__(self, name, editorwidget, configwidget):
        self.name = name
        self.description = ''
        self.icon = ''
        self.editorwidget = editorwidget
        self.configwidget = configwidget

    def createWidget(self, layer, field, widget, label, parent=None):
        return self.editorwidget.for_widget(layer, field, widget, label, parent)

    def readwidgetconfig(self, configwidget):
        widgetconfig = configwidget.getconfig()
        return {self.name: widgetconfig}

    def setwidgetconfig(self, configwidget, config):
        configwidget.config = config


class EditorWidget(QObject):
    validationupdate = pyqtSignal(str, bool)

    def __init__(self, layer=None, field=None, widget=None, label=None, parent=None):
        super(EditorWidget, self).__init__(parent)
        self._config = {}
        self.widget = widget
        self.layer = layer
        self.field = field
        self.label = label
        self.required = False
        self.validationstyle = """QLabel[required=true]
                                {border-radius: 5px; background-color: rgba(255, 221, 48,150);}
                                QLabel[ok=true]
                                { border-radius: 5px; background-color: rgba(200, 255, 197, 150); }"""
        self.buddywidget.setStyleSheet(self.validationstyle)
        self.validationupdate.connect(self.updatecontrolstate)

    @classmethod
    def for_widget(cls, layer, field, widget, label, parent=None):
        """
        Create a new editor wrapper for the given widget.
        If no widget is given then the wrapper will create the widget it needs.
        """
        if widget is None:
            widget = cls().createWidget(parent)

        editor = cls(layer, field, widget, label, parent)
        return editor

    def raisevalidationupdate(self, passed):
        self.validationupdate.emit(self.field, passed)

    def updatecontrolstate(self, field, passed):
        if self.required:
            self.buddywidget.setProperty('ok', passed)
            self.buddywidget.style().unpolish(self.buddywidget)
            self.buddywidget.style().polish(self.buddywidget)

    def setrequired(self):
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

