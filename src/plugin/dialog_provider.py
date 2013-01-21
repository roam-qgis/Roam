import os.path
import os
from form_binder import FormBinder
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils import Timer, log, info, warning, error
import tempfile
from ui_errorlist import Ui_Dialog

class DialogProvider(QObject):
    """
    A class to handle opening user form and creating all the required bindings

    @note: There is a little too much work in this class. Needs a bit of a clean up.
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    
    def __init__(self, canvas, iface):
        QObject.__init__(self)
        self.canvas = canvas
        self.iface = iface

    def openDialog(self, formmodule, feature, layer, forupdate, mandatory_fields=True):
        """
        Opens a form for the given feature

        @refactor: This really needs to be cleaned up.
        """
        self.update = forupdate
        self.dialog = formmodule.formInstance(self.iface.mainWindow())
        self.layer = layer
        self.feature = feature

        self.settings = formmodule.settings()

        self.binder = FormBinder(layer, self.dialog, self.canvas,\
                                 self.settings, formmodule, formmodule.db())
        self.binder.beginSelectFeature.connect(self.selectingFromMap)
        self.binder.endSelectFeature.connect(self.featureSelected)
        self.binder.bindFeature(self.feature, mandatory_fields, \
                                self.update)
        self.binder.bindSelectButtons()

        buttonbox = self.dialog.findChild(QDialogButtonBox)
        try:
            buttonbox.accepted.disconnect()
            buttonbox.rejected.disconnect()
        except TypeError:
            # If there are no signals to disconnect then we get a type error.
            pass

        if mandatory_fields:
            buttonbox.accepted.connect(self.validateForm)
        else:
            buttonbox.accepted.connect(self.dialogAccept)
            buttonbox.accepted.connect(self.accepted)

        buttonbox.rejected.connect(self.rejected)
        buttonbox.rejected.connect(self.dialog.reject)
        buttonbox.rejected.connect(self.deleteDialog)

        self.dialog.setModal(True)
        
        if self.settings.get("fullscreen", False):
            self.dialog.showFullScreen()
        else:
            self.dialog.show()

    def selectingFromMap(self, message):
        """
        Put QMap in the select feature from map mode
        
        Hides the dialog and shows the user a message
        """
        self.dialog.hide()
        label = QLabel()
        label.setText(QString(message))
        label.setStyleSheet('font: 75 30pt "MS Shell Dlg 2";color: rgb(231, 175, 62);')
        self.item = self.canvas.scene().addWidget(label)
        self.disableToolbars()

    def featureSelected(self):
        """
        Called once a feature has been selected. Shows the dialog back to the user.
        """
        log('Feature selected')
        self.canvas.scene().removeItem(self.item)
        self.dialog.show()
        self.enableToolbars()

    def validateForm(self):
        """
        Validate the users form.  If there are any errors report them to the user.

        @refactor: Should really just return a bool and let the caller handle what happens next.
                   We should also consider using QValidator for validation.
        """
        controls = self.binder.mandatory_group.unchanged()
        haserrors = len(controls) > 0
        
        if haserrors:
            dlg = QDialog()
            dlg.setWindowFlags( Qt.Tool | Qt.WindowTitleHint )
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
        """
        Accept the current open dialog and save the new/updated feature 
        back to the layer.
        """
        info("Saving values back")
        feature = self.binder.unbindFeature(self.feature, self.update)
        info("New feature %s" % feature)
        for value in self.feature.attributeMap().values():
            info("New value %s" % value.toString())

        if self.update:
            self.layer.updateFeature( feature )
        else:
            self.layer.addFeature( feature )

        saved = self.layer.commitChanges()
        if not saved:
            for e in self.layer.commitErrors():
                error(e)

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
        """ 
        Disable the toolbars in the main interface.

        @refactor: Should be moved into qmap.py
        """
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setEnabled(False)

    def enableToolbars(self):
        """ 
        Enable the toolbars in the main interface.

        @refactor: Should be moved into qmap.py
        """
        toolbars = self.iface.mainWindow().findChildren(QToolBar)
        for toolbar in toolbars:
            toolbar.setEnabled(True)