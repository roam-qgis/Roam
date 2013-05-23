import tempfile
import uuid
import os.path
import os
import re
import qmaplayer

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from utils import log, info, warning
from select_feature_tool import SelectFeatureTool
from functools import partial
from datatimerpickerwidget import DateTimePickerDialog
from drawingpad import DrawingPad
from helpviewdialog import HelpViewDialog
from utils import log, warning, appdata
from qtcontrols.imagewidget import QMapImageWidget
from qgis.gui import QgsAttributeEditor
from qgis.core import QgsVectorLayer



class BindingError(Exception):
    def __init__(self, control, value, reason=''):
        Exception.__init__(self)
        self.control = control
        self.value = value
        self.message = "Couldn't bind %s to %s" % (control.objectName(), value)
        self.reason = reason


class ControlNotFound(Exception):
    def __init__(self, control_name):
        Exception.__init__(self)
        self.message = "Can't find control called %s" % (control_name)


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
                        QLineEdit: lambda w: w.text().isEmpty(),
                        QTextEdit: lambda w: w.toPlainText().isEmpty(),
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
            return w.currentText().isEmpty() or w.currentText() == "(no selection)"

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


class FormBinder(QObject):
    beginSelectFeature = pyqtSignal(str)
    endSelectFeature = pyqtSignal()
    """
    Handles binding of values to and out of the form.
    """
    def __init__(self, layer, formInstance, canvas):
        QObject.__init__(self)
        self.layer = layer
        self.canvas = canvas
        self.forminstance = formInstance
        self.images = {}
        self.mandatory_group = MandatoryGroup()
        self.boundControls = []

    def bindFeature(self, qgsfeature, mandatory_fields=True, editing=False):
        """
        Binds a features values to the form. If the control has the mandatory
        property set then it will be added to the mandatory group.

        qgsfeature - A QgsFeature to bind the values from
        mandatory_fields - True if mandatory fields should be respected (default)
        """
        self.feature = qgsfeature
        defaults = qmaplayer.getSavedValues(self.layer)
        
        for index in xrange(qgsfeature.fields().count()):
            value = qgsfeature[index]
            name = str(qgsfeature.fields()[index].name())
            
            try:
                control = self.getControl(name)
            except ControlNotFound as ex:
                warning(ex.message)
                continue

            if mandatory_fields:
                mandatory = control.property("mandatory").toBool()
                if mandatory:
                    buddy = self.getBuddy(control)
                    self.mandatory_group.addWidget(control, buddy)

            self.bindSaveValueButton(control, defaults, editingmode=editing)
            if not editing:
                try:
                    value = defaults[name]
                except KeyError:
                    pass

            try:
                self.bindValueToControl(control, QVariant(value), index)
            except BindingError as er:
                warning(er.reason)

            self.createHelpLink(control)
            self.mandatory_group.validateAll()

    def createHelpLink(self, control):
        name = control.objectName()
        helpfile = qmaplayer.getHelpFile(self.layer, name)
        if helpfile:
            label = self.getBuddy(control)
            if label is control: return
            if label is None: return
            text = '<a href="%s">%s<a>' % (helpfile, label.text())
            label.setText(text)
            label.linkActivated.connect(self.showHelp)
    
    def showHelp(self, url):
        dlg = HelpViewDialog()
        dlg.loadFile(url)
        dlg.exec_()

    def getBuddy(self, control):
        try:
            label = self.getControl(control.objectName() + "_label", control_type=QLabel)
            return label
        except ControlNotFound:
            return control

    def getControl(self, name, control_type=QWidget):
        control = self.forminstance.findChild(control_type, name)
        if control is None:
            raise ControlNotFound(name)

        return control

    def bindByName(self, controlname, value):
        """
        Binds a value to a control based on the control name.

        controlname - Name of the control to bind
        value - QVariant holding the value.
        """
        control = self.getControl(controlname)

        try:
            self.bindValueToControl(control, value)
        except BindingError as er:
            warning(er.reason)

    def bindValueToControl(self, control, value, index=0):
        """
        Binds a control to the supplied value.

        control - QWidget based control that takes the new value
        value - A QVariant holding the value
        """
        if isinstance(control, QDateTimeEdit):
            # Can be removed after http://hub.qgis.org/issues/7013 is fixed.
            control.setDateTime(QDateTime.fromString(value.toString(), Qt.ISODate))
            try:
                button = self.getControl(control.objectName() + "_pick", QPushButton)
                button.setIcon(QIcon(":/icons/calender"))
                button.setText("Pick")
                button.setIconSize(QSize(24, 24))
                button.pressed.connect(partial(self.pickDateTime, control, "DateTime"))
            except ControlNotFound:
                pass
            
            self.boundControls.append(control)

        elif isinstance(control, QPushButton):
            if control.text() == "Drawing":
                control.setIcon(QIcon(":/icons/draw"))
                control.setIconSize(QSize(24, 24))
                control.pressed.connect(partial(self.loadDrawingTool, control))
                self.boundControls.append(control)
                
        elif hasattr(control, 'loadImage'):
            image = value.toByteArray()
            log("IMAGE FROM FIELD")
            log(image)
            control.loadImage(image)
            self.boundControls.append(control)
            
        else:
            if (isinstance(control, QComboBox) and
                self.layer.editType(index) == QgsVectorLayer.UniqueValuesEditable):
                
                for v in self.layer.dataProvider().uniqueValues(index):
                    control.addItem(v.toString(), v.toString())
                
                editable = control.isEditable()
                
                control.setEditText(value.toString())
                self.boundControls.append(control)
                
            try:
                # Remove the validator because there seems to be a bug with the 
                # MS SQL layers and validators.
                control.setValidator(None)
            except AttributeError:
                pass

    def unbindFeature(self, feature):
        """
        Unbinds the feature from the form saving the values back to the QgsFeature.

        feature -- A QgsFeature that will store the new values.
        """
        for control in self.boundControls:
            name = str(control.objectName())
            log(name)
            if isinstance(control, QDateTimeEdit):
                value = control.dateTime().toString(Qt.ISODate)
                log(value)
                try:
                    feature[name] = value
                except KeyError as e:
                    log(e)
                    continue
                
            elif hasattr(control, 'getImage'):
                image = control.getImage()
                value = QVariant(image)
                try:
                    feature[name] = value
                except KeyError:
                    log("No field named " + name)
                    pass  
                   
        return feature
    
    def saveValues(self, feature):
        tosave = {}
        for field, shouldsave in self._getSaveButtons():
            if shouldsave:
                index = feature.fieldNameIndex(field)
                tosave[field] = str(feature[field].toString())
                    
        qmaplayer.setSavedValues(self.layer, tosave)
        
    def _getSaveButtons(self):
        buttons = self.forminstance.findChildren(QToolButton)
        for button in buttons:
            name = str(button.objectName())
            if name.endswith('_save'):
                yield name[:-5], button.isChecked()


    def loadDrawingTool(self, control):
        """
        Load the drawing tool.

        control - The control (QWidget) who owns this drawing.  Its name is used
                  in the naming of the final image.
        """
        controlname = str(control.objectName())
        self.forminstance.hide()
        curdir = os.path.dirname(__file__)
        id = self.feature.attributeMap()[self.layer.fieldNameIndex("UniqueID")].toString()
        savedname = str(id) + "_" + controlname + ".jpg"
        imagename = os.path.join(curdir, "data", str(self.layer.name()), "images", \
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

    def pickDateTime(self, control, mode):
        """
        Open the date time picker dialog

        control - The control that will recive the user set date time.
        """
        dlg = DateTimePickerDialog(mode)
        dlg.setWindowTitle("Select a date")
        if control.dateTime() == QDateTime(2000, 1, 1, 00, 00, 00, 0):
            dlg.setAsNow()
        else:
            dlg.setDateTime(control.dateTime())

        if dlg.exec_():
            if hasattr(control, 'setDate'):
                control.setDate(dlg.getSelectedDate())

            if hasattr(control, 'setTime'):
                control.setTime(dlg.getSelectedTime())

    def shouldSaveValue(self, control):
        try:
            button = self.getControl(control.objectName() + "_save", QToolButton)
        except ControlNotFound:
            return

        return button.isChecked()

    def bindSaveValueButton(self, control, defaults, editingmode=False):
        name = str(control.objectName())
        try:
            button = self.getControl(name + "_save", QToolButton)
        except ControlNotFound:
            return

        button.setCheckable(not editingmode)
        button.setIcon(QIcon(":/icons/save_default"))
        button.setIconSize(QSize(24, 24))
        button.setChecked(name in defaults)
        button.setVisible(not editingmode)

    def bindSelectButtons(self):
        """
        Binds all the buttons on the form that need a select from map action.
        """
        tools = self.forminstance.findChildren(QToolButton, QRegExp('.*_mapselect'))
        log(tools)
        layers = {QString(l.name()): l for l in self.canvas.layers()}
        log(layers)
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

            layer_name = tool.property('from_layer').toString()
            column_name = tool.property('using_column').toString()

            layer = None
            try:
                layer = layers[QString(layer_name)]
            except KeyError:
                warning('layer not found in list')
                tool.setEnabled(False)
                continue

            message = tool.property('message').toString()
            if message.isEmpty():
                message = "Please select a feature in the map"

            radius, valid = tool.property('radius').toInt()
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
