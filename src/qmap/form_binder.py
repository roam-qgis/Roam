import tempfile
import uuid
import os.path
import os
import re
import qmaplayer

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from utils import log, info, warning, openImageViewer
from select_feature_tool import SelectFeatureTool
from functools import partial
from datatimerpickerwidget import DateTimePickerDialog
from helpviewdialog import HelpViewDialog
from qgis.core import QgsVectorLayer
from qgis.gui import QgsAttributeEditor
import resources_rc

class BindingError(Exception):
    def __init__(self, control, value, reason=''):
        Exception.__init__(self)
        self.control = control
        self.value = value
        self.message = "Couldn't bind {} to {}".format(control.objectName(), value)
        self.reason = reason


class ControlNotFound(Exception):
    def __init__(self, control_name):
        Exception.__init__(self)
        self.message = "Can't find control called {}".format(control_name)


class MandatoryGroup(QObject):
    passed = pyqtSignal()
    failed = pyqtSignal()
    #http://doc.qt.nokia.com/qq/qq11-mandatoryfields.html

    def __init__(self):
        QObject.__init__(self)
        self.widgets = {}
        # Mapping of widget type to condition to check.  Condition should return
        # false if value has been completed.
        self.mapping = {QComboBox: lambda w: comboboxvalidate(w),
                        QCheckBox: lambda w: w.checkState() == Qt.Unchecked,
                        QLineEdit: lambda w: not w.text(),
                        QTextEdit: lambda w: not w.toPlainText(),
                        QDateTimeEdit: lambda w: w.dateTime() == \
                                         QDateTime(2000, 1, 1, 00, 00, 00, 0),
                       }
        self.stylesheets = {
                                QGroupBox: "QGroupBox::title[mandatory=true]" \
                                            "{border-radius: 5px; background-color: rgba(255, 221, 48,150);}" \
                                            "QGroupBox::title[ok=true]" \
                                            "{ border-radius: 5px; background-color: rgba(200, 255, 197, 150); }",
                                QLabel: "QLabel[mandatory=true]" \
                                            "{border-radius: 5px; background-color: rgba(255, 221, 48,150);}" \
                                            "QLabel[ok=true]" \
                                            "{ border-radius: 5px; background-color: rgba(200, 255, 197, 150); }",
                                QCheckBox: "QCheckBox[mandatory=true]" \
                                            "{border-radius: 5px; background-color: rgba(255, 221, 48,150);}" \
                                            "QCheckBox[ok=true]" \
                                            "{border-radius: 5px; background-color: rgba(200, 255, 197, 150); }",

                           }

        def comboboxvalidate(w):
            return not w.currentText() or w.currentText() == "(no selection)"

        def comboxboxchanges(w, m):
            if w.isEditable():
                w.editTextChanged.connect(m)

            w.currentIndexChanged.connect(m)

        self.signals = {
                         QComboBox: lambda w, m: comboxboxchanges(w, m),
                         QCheckBox: lambda w, m: w.stateChanged.connect(m),
                         QLineEdit: lambda w, m: w.textChanged.connect(m),
                         QTextEdit: lambda w, m: w.textChanged.connect(m),
                         QDateTimeEdit: lambda w, m: w.dateTimeChanged.connect(m),
                        }

    def addWidget(self, widget, buddy):
        if widget in self.widgets.keys():
            return

        try:
            sig = self.signals[type(widget)]
            sig(widget, self.validateAll)
        except KeyError:
            pass

        try:
            style = self.stylesheets[type(buddy)]
            buddy.setStyleSheet(style)
        except KeyError:
            pass

        buddy.setProperty("mandatory", True)
        self.widgets[widget] = buddy

    def validateAll(self):
        anyfailed = False
        for widget, buddy in self.widgets.iteritems():
            failed = self.mapping[type(widget)](widget)
            if failed:
                buddy.setProperty("ok", False)
                anyfailed = True
            else:
                buddy.setProperty("ok", True)

            buddy.style().unpolish(buddy)
            buddy.style().polish(buddy)

        if not anyfailed:
            # If we get here then we are right to let the user continue.
            self.passed.emit()
        else:
            self.failed.emit()
            
def bindForm(dialog, layer, feature, canvas):
    def dialogaccept():
        log("Dialog Accept")
        binder.unbindFeature(feature)
        binder.saveValues(feature)
        
        log("ON ACCCPT")
        for attr in feature.attributes():
            log(attr)
        
    binder = FormBinder(layer, dialog, canvas)
    updatemode = feature.id() > 0
    binder.bindFeature(feature, mandatory_fields=True, editing=updatemode)
    
    for control in dialog.findChildren(QWidget):
        if hasattr(control, 'openRequest'):
            control.openRequest.connect(openImageViewer)
            
    buttonbox = dialog.findChild(QDialogButtonBox)
    buttonbox.accepted.connect(dialogaccept)
        
    buttonbox.setStandardButtons(QDialogButtonBox.Save | QDialogButtonBox.Cancel )
    savebutton = buttonbox.button(QDialogButtonBox.Save)
    
    if updatemode:
        savebutton.setText("Update")

    if not layer.isEditable():
        savebutton.hide()

    binder.mandatory_group.passed.connect(lambda x = True : savebutton.setEnabled(x))
    binder.mandatory_group.failed.connect(lambda x = False : savebutton.setEnabled(x))
    binder.mandatory_group.validateAll()

class FormBinder(QObject):
    beginSelectFeature = pyqtSignal(str)
    endSelectFeature = pyqtSignal()
    """
    Handles binding of values to and out of the form.
    
    TODO: This whole class is really messy and needs a good clean up.
    """
    def __init__(self, layer, formInstance, canvas):
        QObject.__init__(self)
        self.layer = layer
        self.canvas = canvas
        self.forminstance = formInstance
        self.images = {}
        self.mandatory_group = MandatoryGroup()
        self.boundControls = []


    def loadDrawingTool(self, control):
        """
        Load the drawing tool.

        control - The control (QWidget) who owns this drawing.  Its name is used
                  in the naming of the final image.
        """
        raise NotImplementedError
    
        controlname = control.objectName()
        self.forminstance.hide()
        curdir = os.path.dirname(__file__)
        id = self.feature.attributeMap()[self.layer.fieldNameIndex("UniqueID")]
        savedname = str(id) + "_" + controlname + ".jpg"
        imagename = os.path.join(curdir, "data", self.layer.name(), "images", \
                                savedname)

        tempname = "drawingFor_{0}".format(controlname)
        tempimage = os.path.join(tempfile.gettempdir(), tempname)

        log("Looking for {0} or {1}".format(imagename, tempimage))
        imagetoload = self.images.get(controlname, imagename)

        drawingpad = DrawingPad(imagetoload)
        drawingpad.setWindowState(Qt.WindowFullScreen | Qt.WindowActive)
        drawingpad.ui.actionMapSnapshot.triggered.connect(partial(self.drawingPadMapSnapshot, drawingpad))
        if drawingpad.exec_():
            #Save the image to a temporay location until commit.
            self.images[controlname] = tempimage + ".png"
            drawingpad.saveImage(tempimage)
            self.forminstance.show()
        else:
            self.forminstance.show()

    def drawingPadMapSnapshot(self, pad):
        """
        Saves the current view of the map canvas to a image and it into the
        drawing pad.

        pad - The drawing pad that will take the final image.
        """
        #TODO Refactor me!!
        image = QPixmap.fromImage(pad.scribbleArea.image)
        tempimage = os.path.join(tempfile.gettempdir(), "mapcanvascapture.png")
        self.canvas.saveAsImage(tempimage, image)
        pad.openImage(tempimage)

    def bindSelectButtons(self):
        """
        Binds all the buttons on the form that need a select from map action.
        """
        tools = self.forminstance.findChildren(QToolButton, QRegExp('.*_mapselect'))
        layers = {l.name(): l for l in self.canvas.layers()}
        for tool in tools:
            try:
                control = self.getControl(tool.objectName()[:-10])
            except ControlNotFound as ex:
                warning(ex.message)
                tool.setEnabled(False)
                continue

            settings = tool.dynamicPropertyNames()
            if not 'from_layer' in settings or not 'using_column' in settings:
                warning('from_layer or using_column not found')
                tool.setEnabled(False)
                continue

            layer_name = tool.property('from_layer')
            column_name = tool.property('using_column')

            layer = None
            try:
                layer = layers[layer_name]
            except KeyError:
                warning('layer not found in list')
                tool.setEnabled(False)
                continue

            message = tool.property('message')
            if message.isEmpty():
                message = "Please select a feature in the map"

            radius, valid = tool.property('radius')
            if not valid:
                radius = 5

            tool.pressed.connect(partial(self.selectFeatureClicked,
                                                      layer,
                                                      column_name,
                                                      message,
                                                      radius,
                                                      control.objectName()))
            tool.setIcon(QIcon(":/icons/select"))
            tool.setIconSize(QSize(24, 24))

    def selectFeatureClicked(self, layer, column, message, searchsize, bindto):
        """
        Loads the select from map action tool. Switchs to the map to allow the
        user to select a feature.

        controlname - The control name when looking up in the settings for the
                      button config.
        """
        self.tool = SelectFeatureTool(self.canvas, layer, column, bindto, searchsize)
        self.tool.foundFeature.connect(self.bindHighlightedFeature)
        self.tool.setActive()
        self.beginSelectFeature.emit(message)

    def bindHighlightedFeature(self, feature, value, bindto):
        """
        Binds the selected features value to a control.
        """
        self.bindByName(bindto, value)
        self.endSelectFeature.emit()
