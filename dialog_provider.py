import os.path
import os
from form_binder import FormBinder
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils import Timer, log, info, warning
import tempfile
from ui_errorlist import Ui_Dialog

class DialogProvider(QObject):
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    
    def __init__(self, canvas, iface):
        QObject.__init__(self)
        self.canvas = canvas
        self.iface = iface

    def openDialog(self, formmodule, feature, layer, forupdate,mandatory_fields=True):
        self.update = forupdate
        self.dialog = formmodule.formInstance(self.iface.mainWindow())
        self.layer = layer
        self.feature = feature

        self.settings = formmodule.settings()

        self.binder = FormBinder(layer, self.dialog, self.canvas, self.settings)
        self.binder.beginSelectFeature.connect(self.selectingFromMap)
        self.binder.endSelectFeature.connect(self.featureSelected)
        self.binder.bindFeature(self.feature, mandatory_fields)
        self.binder.bindSelectButtons()

        buttonbox = self.dialog.findChild(QDialogButtonBox)

        if mandatory_fields:
            buttonbox.accepted.connect(self.validateForm)
        else:
            buttonbox.accepted.connect(self.dialogAccept)
            buttonbox.accepted.connect(self.accepted)
            
        buttonbox.rejected.connect(self.rejected)
        buttonbox.rejected.connect(self.dialog.reject)
        buttonbox.rejected.connect(self.deleteDialog)

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

    def validateForm(self):
        controls = self.binder.mandatory_group.unchanged()
        haserrors = len(controls) > 0
        
        if haserrors:
            dlg = QDialog()
            dlg.setWindowFlags( Qt.Dialog | Qt.WindowTitleHint )
            ui = Ui_Dialog()
            ui.setupUi(dlg)
            for control in controls:
                label = self.dialog.findChild(QLabel, control.objectName() + "_label")
                if not label is None:
                    name = label.text()
                elif isinstance(control, QCheckBox):
                    name = control.text()
                elif isinstance(control, QGroupBox):
                    name = control.title()

                name += " is mandatory"
                item = QListWidgetItem(name)
                item.setBackground(QBrush(QColor.fromRgb(255,221,48,150)))
                ui.errorList.addItem(item)
            dlg.exec_()
        else:
            self.dialogAccept()
            
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

        self.dialog.accept()
        self.accepted.emit()
            
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