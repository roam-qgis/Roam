import os.path
import os
from form_binder import FormBinder
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils import Timer, log, info, warning, error
import tempfile
from ui_errorlist import Ui_Dialog
from qgis.gui import QgsMessageBar
from qgis.core import QgsVectorLayer
import qmap

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

    def openDialog(self, feature, layer, forupdate, mandatory_fields=True):
        """
        Opens a form for the given feature

        @refactor: This really needs to be cleaned up.
        """
        
        # If the layer has a ui file then we need to rewrite to be relative
        # to the current projects->layer folder
        
        if layer.editorLayout() == QgsVectorLayer.UiFileLayout:
            form = os.path.basename(str(layer.editForm()))
            folder = qmap.currentproject.folder
            newpath = os.path.join(folder,str(layer.name()),form)
            layer.setEditForm(newpath)
            log(str(layer.editForm()))
              
        self.dialog = self.iface.getFeatureForm(layer, feature)
        self.layer = layer
        self.binder = FormBinder(layer, self.dialog, self.canvas)
        self.binder.beginSelectFeature.connect(self.selectingFromMap)
        self.binder.endSelectFeature.connect(self.featureSelected)
        self.binder.bindFeature(feature, mandatory_fields, forupdate)
        self.binder.bindSelectButtons()

        buttonbox = self.dialog.findChild(QDialogButtonBox)
        
        buttonbox.setStandardButtons(QDialogButtonBox.Save | QDialogButtonBox.Cancel )
        savebutton = buttonbox.button(QDialogButtonBox.Save)
        
        if forupdate:
            savebutton.setText("Update")
        
        noerrors = len(self.binder.mandatory_group.unchanged()) == 0
        savebutton.setEnabled(noerrors)
        self.binder.mandatory_group.passed.connect(lambda x = True : savebutton.setEnabled(x))
        self.binder.mandatory_group.failed.connect(lambda x = False : savebutton.setEnabled(x))

        buttonbox.rejected.connect(self.rejected)
        buttonbox.rejected.connect(self.dialog.reject)

        self.dialog.setModal(True)
        
        fullscreen = self.dialog.property('fullscreen').toBool()
        
        if fullscreen:
            self.dialog.setWindowState(Qt.WindowFullScreen)
        
        if self.dialog.exec_():
            self.binder.unbindFeature(feature)
            
            for value in feature.attributes():
                info("New value %s" % value.toString())
    
            if forupdate :
                self.layer.updateFeature(feature)
            else:
                 self.layer.addFeature(feature)
                 self.binder.saveValues(feature)
            
            saved = self.layer.commitChanges()
            if not saved:
                self.iface.messageBar().pushMessage("Error",
                                                    "Error in saving changes. Contact administrator ", 
                                                    QgsMessageBar.CRITICAL)
                for e in self.layer.commitErrors(): error(e)
            else:
                self.iface.messageBar().pushMessage("Saved","Changes saved", QgsMessageBar.INFO, 2)

        self.canvas.refresh()

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
        self.canvas.scene().removeItem(self.item)
        self.dialog.show()
        self.enableToolbars()
        
    def moveImages(self):
        """ Not currently working """
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