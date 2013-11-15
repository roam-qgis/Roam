from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QWidget, QDialogButtonBox, QStatusBar, QLabel, QGridLayout

from qmap.editorwidgets.core import WidgetsRegistry
from qmap import nullcheck

class FeatureForm(object):
    requiredfieldsupdated = pyqtSignal(bool)
    def __init__(self, widget, layer, layerconfig):
        self.widget = widget
        self.layerconfig = layerconfig
        self.layer = layer
        self.boundwidgets = []
        self.requiredfields = {}

    @classmethod
    def fromLayer(cls, layer, layerconfig):
        uifile = layer.editForm()
        widget = uic.loadUi(uifile)
        return cls(widget, layer, layerconfig)

    def openForm(self):
        fullscreen = self.widget.property('fullscreen')
        if fullscreen:
            self.widget.setWindowState(Qt.WindowFullScreen)

        self.statusbar = QStatusBar()
        self.statusbar.setSizeGripEnabled(False)
        layout = self.widget.layout()
        if isinstance(layout, QGridLayout):
            rows = layout.rowCount()
            columns = layout.columnCount()
            layout.addWidget(self.statusbar, rows, 0, 1, columns)
        else:
            layout.addWidget(self.statusbar)

        try:
            buttonbox = self.widget.findChildren(QDialogButtonBox)[0]
            buttonbox.accepted.connect(self.widget.accept)
            buttonbox.rejected.connect(self.widget.reject)
        except IndexError:
            # If we can't find a button box we should assume the user has
            # sorted it out on the form some how
            pass

        return self.widget.exec_()

    def updaterequired(self, field, state):
        self.requiredfields[field] = state
        passed = all(valid == True for valid in m.values())
        if not passed:
            self.statusbar.showMessage('Required fields missing')
        self.requiredfieldsupdated.emit(passed)

    def bindFeature(self, feature):
        fieldsconfig = self.layerconfig['fields']
        for field, config in fieldsconfig.iteritems():
            widget = self.widget.findChild(QWidget, field)
            label = self.widget.findChild(QLabel, "{}_label".format(field))
            widgetconfig = config['widget']
            widgettype = widgetconfig['widgettype']
            required = config.get('required', False)
            widgetwrapper = WidgetsRegistry.createwidget(widgettype, self.layer, field, widget, label, widgetconfig)

            if widgetwrapper is None:
                print("No widget found for {}".format(widgettype))
                continue

            if required:
                # All widgets state off as false unless told otherwise
                self.requiredfields[field] = False
                widgetwrapper.statechanged.connect(self.updaterequired)

            value = nullcheck(feature[field])
            widgetwrapper.setvalue(value)
            self.boundwidgets.append(widgetwrapper)

    def updateFeature(self, feature):
        for wrapper in self.boundwidgets:
            value = wrapper.value()
            field = wrapper.field
            feature[field] = value
        return feature
