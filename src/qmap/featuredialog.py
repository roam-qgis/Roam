from PyQt4 import uic

class FeatureForm(object):
    def __init__(self, widget):
        self.widget = widget

    @classmethod
    def fromLayer(cls, layer):
        uifile = layer.editForm()
        widget = uic.loadUi(uifile)
        return cls(widget)

    def openForm(self, feature):
        fullscreen = self.widget.property('fullscreen')
        if fullscreen:
            self.widget.setWindowState(Qt.WindowFullScreen)

        self.bindFeature(feature)
        accepted = self.widget.exec_()
        return self.getFeature(), accepted

    def bindFeature(self, feature):
        pass

    def getFeature(self):
        pass
