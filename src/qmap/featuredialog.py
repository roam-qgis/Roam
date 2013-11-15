from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, QObject
from PyQt4.QtGui import QWidget, QDialogButtonBox, QStatusBar, QLabel, QGridLayout

from qmap.editorwidgets.core import WidgetsRegistry
from qmap import nullcheck

class FeatureForm(QObject):
    requiredfieldsupdated = pyqtSignal(bool)
    def __init__(self, widget, layer, layerconfig):
        super(FeatureForm, self).__init__()
        self.widget = widget
        self.layerconfig = layerconfig
        self.layer = layer
        self.boundwidgets = []
        self.requiredfields = {}
        self.statusbar = self.widget.findChild(QStatusBar)

    @classmethod
    def from_layer(cls, layer, layerconfig):
        uifile = layer.editForm()
        widget = uic.loadUi(uifile)

        statusbar = QStatusBar()
        statusbar.setSizeGripEnabled(False)
        layout = widget.layout()
        if isinstance(layout, QGridLayout):
            rows = layout.rowCount()
            columns = layout.columnCount()
            layout.addWidget(statusbar, rows, 0, 1, columns)
        else:
            layout.addWidget(statusbar)

        buttonbox = widget.findChildren(QDialogButtonBox)[0]
        buttonbox.accepted.connect(widget.accept)
        buttonbox.rejected.connect(widget.reject)

        return cls(widget, layer, layerconfig)

    def openForm(self):
        fullscreen = self.widget.property('fullscreen')
        if fullscreen:
            self.widget.setWindowState(Qt.WindowFullScreen)

        return self.widget.exec_()

    def acceptbutton(self):
        try:
            buttonbox = self.widget.findChildren(QDialogButtonBox)[0]
            savebutton = buttonbox.button(QDialogButtonBox.Save)
            return savebutton
        except IndexError:
            return None

    def updaterequired(self, field, passed):
        self.requiredfields[field] = passed
        passed = all(valid for valid in self.requiredfields.values())
        if not passed:
            self.statusbar.showMessage('Required fields missing')
        else:
            self.statusbar.clearMessage()

        if self.acceptbutton():
            self.acceptbutton().setEnabled(passed)

    def bindFeature(self, feature):
        fieldsconfig = self.layerconfig['fields']
        for field, config in fieldsconfig.iteritems():
            widget = self.widget.findChild(QWidget, field)
            label = self.widget.findChild(QLabel, "{}_label".format(field))
            widgetconfig = config['widget']
            widgettype = widgetconfig['widgettype']
            widgetwrapper = WidgetsRegistry.createwidget(widgettype, self.layer, field, widget, label, widgetconfig)

            if widgetwrapper is None:
                print("No widget found for {}".format(widgettype))
                continue

            if config.get('required', False):
                # All widgets state off as false unless told otherwise
                self.requiredfields[field] = False
                widgetwrapper.setrequired()
                widgetwrapper.validationupdate.connect(self.updaterequired)

            value = nullcheck(feature[field])
            widgetwrapper.setvalue(value)
            self.boundwidgets.append(widgetwrapper)

    def updateFeature(self, feature):
        for wrapper in self.boundwidgets:
            value = wrapper.value()
            field = wrapper.field
            feature[field] = value
        return feature
