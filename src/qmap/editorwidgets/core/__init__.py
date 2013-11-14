from PyQt4.QtCore import QObject


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
    def createwidget(widgettype, layer, field, widget, config, parent=None):
        if not widgettype in WidgetsRegistry.widgets:
            return None

        factory = WidgetsRegistry.widgets[widgettype]
        widgetwrapper = factory.createWidget(layer, field, widget, parent)
        widgetwrapper.config = config
        return widgetwrapper

class WidgetFactory(object):
    def __init__(self, name, editorwidget, configwidget):
        self.name = name
        self.description = ''
        self.icon = ''
        self.editorwidget = editorwidget
        self.configwidget = configwidget

    def createWidget(self, *args):
        return self.editorwidget(*args)

    def readwidgetconfig(self, configwidget):
        widgetconfig = configwidget.getconfig()
        return {self.name : widgetconfig}

    def setwidgetconfig(self, configwidget, config):
        configwidget.config = config


class EditorWidget(QObject):
    def __init__(self, layer, field, widget, parent=None):
        super(EditorWidget, self).__init__(parent)
        self._config = {}
        self.widget = widget
        self.layer = None
        self.field = field

    def setvalue(self, value):
        pass

    def value(self):
        pass

    @property
    def widget(self):
        if not self._widget:
            self._widget = self.createWidget(self.parent())
            self.initWidget(self._widget)
        return self._widget

    @widget.setter
    def widget(self, widget):
        self._widget = widget

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        print "Setting config"
        self._config = value
        if not self._widget is None:
            self.initWidget(self._widget)

    def createWidget(self, parent):
        pass

    def initWidget(self, widget):
        pass

    def setEnabled(self, enabled):
        if self._widget:
            self._widget.setEnabled(enabled)


