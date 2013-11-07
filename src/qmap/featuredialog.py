from PyQt4 import uic

class FeatureForm(object):
    def __init__(self, widget):
        self.widget = widget

    @classmethod
    def fromLayer(cls, layer):
        uifile = layer.editForm()
        widget = uic.loadUi(uifile)
        return cls(widget)

    def exec_(self):
        fullscreen = self.widget.property('fullscreen')
        if fullscreen:
            self.widget.setWindowState(Qt.WindowFullScreen)

        return self.widget.exec_()
