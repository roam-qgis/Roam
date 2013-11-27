import os.path
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsDistanceArea
from qgis.gui import QgsMessageBar

from qmap.utils import log, info, warning, error
from qmap import featuredialog

form = None

class DialogProvider(QObject):
    """
    A class to handle opening user form and creating all the required bindings

    @note: There is a little too much work in this class. Needs a bit of a clean up.
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    featuresaved = pyqtSignal()
    failedsave = pyqtSignal()
    
    def __init__(self, canvas):
        QObject.__init__(self)
        self.canvas = canvas

    def openDialog(self, feature, layer, settings, qmaplayer, parent=None):
        """
        Opens a form for the given feature
        """
        def accept():
            if not form.accept():
                return

            feature, savedvalues = form.getupdatedfeature()
            print feature.id()
            if feature.id() > 0:
                layer.updateFeature(feature)
            else:
                layer.addFeature(feature)
                featuredialog.savevalues(layer, savedvalues)

            saved = layer.commitChanges()

            if not saved:
                self.failedsave.emit()
                map(error, layer.commitErrors())
            else:
                self.featuresaved.emit()

            self.canvas.refresh()
            parent.showmap()
            self.accepted.emit()

        def reject():
            if not form.reject():
                return

            layer.rollBack()
            clearcurrentwidget()
            parent.showmap()
            parent.hidedataentry()
            self.rejected.emit()

        def formvalidation(passed):
            msg = None
            if not passed:
                msg = "Looks like some fields are missing. Check any fields marked in"
            parent.missingfieldsLabel.setText(msg)
            parent.savedataButton.setEnabled(passed)
            parent.yellowLabel.setVisible(not passed)

        def clearcurrentwidget():
            item = parent.scrollAreaWidgetContents.layout().itemAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        # None of this saving logic belongs here.
        parent.savedataButton.pressed.connect(accept)
        parent.cancelButton.pressed.connect(reject)

        layerconfig = settings[layer.name()]

        defaults = featuredialog.loadsavedvalues(layer)

        form = featuredialog.FeatureForm.from_layer(layer, layerconfig, qmaplayer, parent)
        form.formvalidation.connect(formvalidation)

        form.bindfeature(feature, defaults)

        widget = form.widget
        clearcurrentwidget()

        parent.scrollAreaWidgetContents.layout().insertWidget(0, widget)
        parent.showdataentry()
        layer.startEditing()

    def selectingFromMap(self, message):
        """
        Put QMap in the select feature from map mode
        
        Hides the dialog and shows the user a message
        """
        self.dialog.hide()
        label = QLabel()
        label.setText(message)
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
        raise NotImplementedError
    
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
