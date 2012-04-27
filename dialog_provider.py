import os
from form_binder import FormBinder
from PyQt4.QtCore import pyqtSignal, QObject, QSettings
from PyQt4.QtGui import QLabel
from utils import Timer, log, info, warning

class DialogProvider(QObject):
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    
    def __init__(self, canvas):
        QObject.__init__(self)
        self.canvas = canvas

    def openDialog(self, formmodule, feature, layer, forupdate):
        self.update = forupdate
        self.dialog = formmodule.dialogInstance()
        self.layer = layer
        self.feature = feature

        curdir = os.path.dirname(formmodule.__file__)
        settingspath = os.path.join(curdir,'settings.ini')
        self.settings = QSettings(settingspath, QSettings.IniFormat)

        self.binder = FormBinder(layer, self.dialog, self.canvas, self.settings)
        self.binder.beginSelectFeature.connect(self.selectingFromMap)
        self.binder.endSelectFeature.connect(self.featureSelected)
        self.binder.bindFeature(self.feature)
        self.binder.bindSelectButtons()

        self.dialog.accepted.connect(self.dialogAccept)
        self.dialog.accepted.connect(self.accepted)
        self.dialog.rejected.connect(self.rejected)
        self.dialog.rejected.connect(self.deleteDialog)
        self.dialog.setModal(True)
        if self.settings.value("fullscreen", False).toBool():
            self.dialog.showFullScreen()
        self.dialog.show()

    def selectingFromMap(self, message):
        self.dialog.hide()
        label = QLabel(message)
        label.setStyleSheet('font: 75 30pt "MS Shell Dlg 2";color: rgb(231, 175, 62);')
        self.item = self.canvas.scene().addWidget(label)

    def featureSelected(self):
        self.canvas.scene().removeItem(self.item)
        self.dialog.show()

    def dialogAccept(self):
        info("Saving values back")
        feature = self.binder.unbindFeature(self.feature)
        info("New feature %s" % feature)
        for value in self.feature.attributeMap().values():
            info("New value %s" % value.toString())

        if self.update:
            self.layer.updateFeature( feature )
        else:
            self.layer.addFeature( self.feature )

        self.canvas.refresh()
        self.layer.commitChanges()

    def deleteDialog(self):
        del self.dialog