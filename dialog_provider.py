import os.path
import os
from form_binder import FormBinder
from PyQt4.QtCore import pyqtSignal, QObject, QSettings
from PyQt4.QtGui import QLabel, QToolBar
from utils import Timer, log, info, warning
import tempfile

class MandatoryGroup(QObject):
    enable = pyqtSignal()
    #http://doc.qt.nokia.com/qq/qq11-mandatoryfields.html
    def __init__(self):
        self.widgets = []
        self.mapping = { QComboBox : lambda w: w.currentText().isEmpty(),
                         QLineEdit : lambda w: w.text().isEmpty()
                         QCheckBox : lambda w: w.state() == QButton.NoChange,
                       }

    def addWidget(self, widget):
        if widget in self.widget:
            return

        self.widgets.append(widget)
        if isinstance(widget, QLineEdit) or isinstance(widget, QTextEdit):
            widget.textChanged.connect(functools.partial(self.changed, widget))

    def changed(self):
        for widget in self.widgets:
            canenable = mapping[type(widget)](widget)

            if not canenable:
                return

        # If we get here then we are right to let the user continue.
        enable.emit()
        
    def remove(self, widget):
        pass

class DialogProvider(QObject):
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    
    def __init__(self, canvas, iface):
        QObject.__init__(self)
        self.canvas = canvas
        self.iface = iface

    def openDialog(self, formmodule, feature, layer, forupdate):
        self.update = forupdate
        self.dialog = formmodule.formInstance()
        self.layer = layer
        self.feature = feature

        self.settings = formmodule.settings()

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
        self.disableToolbars()

    def featureSelected(self):
        self.canvas.scene().removeItem(self.item)
        self.dialog.show()
        self.enableToolbars()

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

        
        self.layer.commitChanges()
        self.canvas.refresh()
        
        if not self.binder.images:
            return

        # After we commit we have to move the drawing into the correct path.
        # TODO Use a custom field for the id name
        # Images are saved under data/{layername}/images/{id}_{fieldname}
        for image in self.binder.images.itervalues():
            curdir = os.path.dirname(__file__)
            id = self.feature.attributeMap()[self.layer.fieldNameIndex("UniqueID")].toString().toUpper()
            log(id)
            name = image.replace("drawingFor_", id + "_" )
            imagename = os.path.join(curdir, "data", str(self.layer.name()), "images", \
                                     os.path.basename(name))

            
            path = os.path.dirname(imagename)
            
            if not os.path.exists(path):
                os.makedirs(path)
            
            log(image)
            log(imagename)
            try:
                os.rename(image, imagename)
            except WindowsError, err:
                os.remove(imagename)
                os.rename(image, imagename)
            
    def deleteDialog(self):
        del self.dialog

    def disableToolbars(self):
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setEnabled(False)

    def enableToolbars(self):
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setEnabled(True)