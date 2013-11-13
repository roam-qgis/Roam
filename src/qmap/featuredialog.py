from PyQt4 import uic
from PyQt4.QtGui import QWidget, QDialogButtonBox

from qmap.editorwidgets.core import WidgetsRegistry

class FeatureForm(object):
    def __init__(self, widget, layer, layerconfig):
        self.widget = widget
        self.layerconfig = layerconfig
        self.layer = layer
        self.boundwidgets = []

    @classmethod
    def fromLayer(cls, layer, layerconfig):
        uifile = layer.editForm()
        widget = uic.loadUi(uifile)
        return cls(widget, layer, layerconfig)

    def openForm(self):
        fullscreen = self.widget.property('fullscreen')
        if fullscreen:
            self.widget.setWindowState(Qt.WindowFullScreen)

        try:
            buttonbox = self.widget.findChildren(QDialogButtonBox)[0]
            buttonbox.accepted.connect(self.widget.accept)
            buttonbox.rejected.connect(self.widget.reject)
        except IndexError:
            # If we can't find a button box we should assume the user has
            # sorted it out on the form some how
            pass

        return self.widget.exec_()

    def bindFeature(self, feature):
        fieldsconfig = self.layerconfig['fields']
        for field, config in fieldsconfig.iteritems():
            widget = self.widget.findChild(QWidget, field)
            widgettype = config.keys()[0]
            widgetconfig = config[widgettype]
            widgetwrapper = WidgetsRegistry.createwidget(widgettype, self.layer, field, widget, widgetconfig)
            widgetwrapper.setvalue(feature[field])
            self.boundwidgets.append(widgetwrapper)

    def updateFeature(self, feature):
        for wrapper in self.boundwidgets:
            value = wrapper.value()
            field = wrapper.field
            feature[field] = value
        return feature
