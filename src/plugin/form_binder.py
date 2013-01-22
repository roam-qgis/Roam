import tempfile
import uuid
import os.path
import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtSql import QSqlQuery
from utils import log, info, warning
from select_feature_tool import SelectFeatureTool
from functools import partial
from datatimerpickerwidget import DateTimePickerDialog
from drawingpad import DrawingPad
from helpviewdialog import HelpViewDialog
from utils import log, warning, appdata
import re
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
    enable = pyqtSignal()
    #http://doc.qt.nokia.com/qq/qq11-mandatoryfields.html

    def __init__(self):
        QObject.__init__(self)
        self.widgets = []
        # Mapping of widget type to condition to check.  Condition should return
        # false if value has been completed.
        self.mapping = {QComboBox: lambda w: w.currentText().isEmpty(),
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
        if widget in self.widgets:
            return

        try:
            sig = self.signals[type(widget)]
            sig(widget, self.changed)
        except KeyError:
            log("CAN'T FIND WIDGET")

        try:
            style = self.stylesheets[type(buddy)]
            buddy.setStyleSheet(style)
        except KeyError:
            pass

        buddy.setProperty("mandatory", True)
        self.widgets.append((widget, buddy))

    def changed(self):
        anyfailed = False
        for widget, buddy in self.widgets:
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
            self.enable.emit()

    def unchanged(self):
        unchanged = []
        for widget, buddy in self.widgets:
            failed = self.mapping[type(widget)](widget)
            if failed:
                unchanged.append(widget)

        return unchanged

    def remove(self, widget):
        pass


class FormBinder(QObject):
    beginSelectFeature = pyqtSignal(str)
    endSelectFeature = pyqtSignal()
    """
    Handles binding of values to and out of the form.
    """
    def __init__(self, layer, formInstance, canvas, settings, form, db):
        QObject.__init__(self)
        self.layer = layer
        self.canvas = canvas
        self.forminstance = formInstance
        self.fields = self.layer.pendingFields()
        self.fieldtocontrol = {}
        self.actionlist = []
        self.settings = settings
        self.images = {}
        self.mandatory_group = MandatoryGroup()
        self.form = form
        self.db = db

    def bindFeature(self, qgsfeature, mandatory_fields=True, editing=False):
        """
        Binds a features values to the form. If the control has the mandatory
        property set then it will be added to the mandatory group.

        qgsfeature - A QgsFeature to bind the values from
        mandatory_fields - True if mandatory fields should be respected (default)
        """
        self.feature = qgsfeature
        defaults = self.form.getSavedValues()

        for index, value in qgsfeature.attributeMap().items():
            name = str(self.fields[index].name())

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

            info("Binding %s to %s" % (control.objectName(), value.toString()))

            self.bindSaveValueButton(control, defaults, editingmode=editing)
            if not editing:
                try:
                    value = defaults[name]
                except KeyError:
                    pass 

            try:
                self.bindValueToControl(control, value, index)
            except BindingError as er:
                warning(er.reason)

            self.createHelpLink(control)

            self.fieldtocontrol[index] = control

    def createHelpLink(self, control):
        name = control.objectName()
        helpfile = self.form.getHelpFile(name)
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
        if not control:
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
            button = self.getControl(control.objectName() + "_pick", QPushButton )
            if not button:
                return

            button.setIcon(QIcon(":/icons/calender"))
            button.setText("Pick")
            button.setIconSize(QSize(24,24))
            button.pressed.connect(partial(self.pickDateTime, control, "DateTime" ))

        elif isinstance(control, QPushButton):
            if control.text() == "Drawing":
                control.setIcon(QIcon(":/icons/draw"))
                control.setIconSize(QSize(24,24))
                control.pressed.connect(partial(self.loadDrawingTool, control))
        else:
            if self.layer.editType(index) == QgsVectorLayer.UniqueValues:
                editable = control.isEditable()

            widget = QgsAttributeEditor.createAttributeEditor(self.forminstance, control, self.layer, index, value)
            wasset = QgsAttributeEditor.setValue(control, self.layer, index, value)
            log(widget)
            
            if self.layer.editType(index) == QgsVectorLayer.UniqueValues:
                # Set the control back to the editable state the form says it should be.
                # This is to work around http://hub.qgis.org/issues/7012
                control.setEditable(editable)

    def unbindFeature(self, qgsfeature, editingmode=False):
        """
        Unbinds the feature from the form saving the values back to the QgsFeature.

        qgsfeature -- A QgsFeature that will store the new values.
        """
        savefields = []
        for index, control in self.fieldtocontrol.items():
                value = QVariant()
                if isinstance(control, QDateTimeEdit):
                    value = control.dateTime().toString(Qt.ISODate)
                elif isinstance(control, QListWidget):
                    item = control.currentItem()
                    if item:
                        value = item.text()
                    else:
                        return QString("")
                else:
                    if (self.layer.editType(index) == QgsVectorLayer.UniqueValues and
                       control.isEditable()):
                        # Due to http://hub.qgis.org/issues/7012 we can't have editable
                        # comboxs using QgsAttributeEditor. If the value isn't in the
                        # dataset already it will return null.  Until that bug is fixed
                        # we are just going to handle ourself.
                        value = control.currentText()
                    else:
                        modified = QgsAttributeEditor.retrieveValue(control, self.layer, index, value)

                info("Setting value to %s from %s" % (value, control.objectName()))
                qgsfeature.changeAttribute(index, value)

                # Save the value to the database as a default if it is needed.
                if self.shouldSaveValue(control):
                    savefields.append(index)

        if not editingmode:
            m = qgsfeature.attributeMap()
            fields_map = self.layer.pendingFields()
            attr = { str(fields_map[k].name()): str(v.toString()) for k, v in m.items() if k in savefields }
            self.form.setSavedValues(attr)

        return qgsfeature


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
        drawingpad.ui.actionMapSnapshot.triggered.connect(partial(self.drawingPadMapSnapshot,drawingpad))
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