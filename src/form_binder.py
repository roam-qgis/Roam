from distutils.errors import CCompilerError
import tempfile
import uuid
import os.path
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from utils import log, info, warning
from qgis.gui import QgsAttributeEditor
from select_feature_tool import SelectFeatureTool
import os
from functools import partial
from datatimerpickerwidget import DateTimePickerDialog
from drawingpad import DrawingPad
from utils import log, warning


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
    def __init__(self, layer, formInstance, canvas, settings):
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

    def bindFeature(self, qgsfeature, mandatory_fields=True):
        """
        Binds a features values to the form. If the control has the mandatory
        property set then it will be added to the mandatory group.

        qgsfeature - A QgsFeature to bind the values from
        mandatory_fields - True if mandatory fields should be respected (default)
        """
        self.feature = qgsfeature
        for index, value in qgsfeature.attributeMap().items():
            field = self.fields[index]

            try:
                control = self.getControl(field.name())
            except ControlNotFound as ex:
                warning(ex.message)
                continue

            if mandatory_fields:
                mandatory = control.property("mandatory").toBool()
                if mandatory:
                    buddy = self.getBuddy(control)
                    self.mandatory_group.addWidget(control, buddy)

            info("Binding %s to %s" % (control.objectName(), value.toString()))

            try:
                self.bindValueToControl(control, value)
            except BindingError as er:
                warning(er.reason)

            self.fieldtocontrol[index] = control

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

    def saveComboValues(self, combobox, text):
        """
        Save the value of the combo box into the form settings values.
        Only saves new values.
        """
        comboitems = [combobox.itemText(i) for i in range(combobox.count())]
        name = combobox.objectName()
        self.settings.beginGroup('ComboBoxItems')
        items = self.settings.value('%s' % name).toString().split(',')
        settingslist = [str(s) for s in items]

        if not text in comboitems and not text in settingslist:
            settingslist.append(str(text))
            newlist = ",".join(settingslist)
            self.settings.setValue('%s' % name, newlist)

        self.settings.endGroup()
        self.settings.sync()

    def bindValueToControl(self, control, value):
        """
        Binds a control to the supplied value.
        Raises BindingError() if control is not supported.

        control - QWidget based control that takes the new value
        value - A QVariant holding the value
        """
        if isinstance(control, QCalendarWidget):
            control.setSelectedDate(QDate.fromString(value.toString(), Qt.ISODate))

        elif isinstance(control, QListWidget):
            items = control.findItems(value.toString(), Qt.MatchExactly)
            try:
                control.setCurrentItem(items[0])
            except IndexError:
                pass

        elif isinstance(control, QLineEdit) or isinstance(control, QTextEdit):
            control.setText(value.toString())

        elif isinstance(control, QCheckBox) or isinstance(control, QGroupBox):
            control.setChecked(value.toBool())

        elif isinstance(control, QComboBox):
            self.settings.beginGroup('ComboBoxItems')
            items = self.settings.value('%s' % control.objectName()).toString() \
                                                                    .split(',')
            for item in items:
                control.addItem(item)
            self.settings.endGroup()
            itemindex = control.findText(value.toString())
            control.setCurrentIndex(itemindex)

        elif isinstance(control, QDoubleSpinBox):
            double, passed = value.toDouble()
            control.setValue(double)

        elif isinstance(control, QSpinBox):
            integer, passed = value.toInt()
            control.setValue(integer)

        elif isinstance(control, QDateTimeEdit):
            control.setDateTime(QDateTime.fromString(value.toString(), Qt.ISODate))
            # Wire up the date picker button
            parent = control.parentWidget()
            if parent:
                button = parent.findChild(QPushButton, control.objectName() + "_pick" )
                if button:
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
            raise BindingError(control, value.toString(), "Unsupported widget %s" % control)

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
        name = str(id) + "_" + controlname + ".jpg"
        imagename = os.path.join(curdir, "data", str(self.layer.name()), "images", \
                                name)

        name = "drawingFor_{0}".format(controlname)
        tempimage = os.path.join(tempfile.gettempdir(), name)

        log("Looking for {0} or {1}".format(imagename, tempimage))
        imagetoload = self.images.get(controlname, imagename)

        drawingpad = DrawingPad(imagetoload)
        drawingpad.setWindowState(Qt.WindowFullScreen | Qt.WindowActive)
        drawingpad.ui.actionMapSnapshot.triggered.connect(partial(self.drawingPadMapSnapshot,drawingpad))
        if drawingpad.exec_():
            #Save the image to a temporay location until commit.
            self.images[controlname] = tempimage + ".jpg"
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

    def unbindFeature(self, qgsfeature):
        """
        Unbinds the feature from the form saving the values back to the QgsFeature.

        qgsfeature -- A QgsFeature that will store the new values.
        TODO: If the parent of the control is a QGroupBox and is disabled, the control is ignored for changing.
        """
        for index, control in self.fieldtocontrol.items():
                value = None
                if isinstance(control, QLineEdit):
                    value = control.text()

                elif isinstance(control, QTextEdit):
                    value = control.toPlainText()

                elif isinstance(control, QCalendarWidget):
                    value = control.selectedDate().toString(Qt.ISODate)

                elif isinstance(control, QCheckBox) or isinstance(control, QGroupBox):
                    value = 0
                    if control.isChecked():
                        value = 1
                elif isinstance(control, QComboBox):
                    value = control.currentText()
                    if control.isEditable():
                        self.saveComboValues(control, value)

                elif isinstance(control, QDoubleSpinBox) or isinstance(control, QSpinBox):
                    value = control.value()

                elif isinstance(control, QDateTimeEdit):
                    value = control.dateTime().toString(Qt.ISODate)

                info("Setting value to %s from %s" % (value, control.objectName()))

                qgsfeature.changeAttribute(index, value)
        return qgsfeature

    def pickDateTime(self, control, mode):
        """
        Open the date time picker dialog

        control - The control that will recive the user set date time.
        """
        dlg = DateTimePickerDialog(mode)
        dlg.setDateTime(control.dateTime())
        if dlg.exec_():
            if hasattr(control, 'setDate'):
                control.setDate(dlg.getSelectedDate())

            if hasattr(control, 'setTime'):
                control.setTime(dlg.getSelectedTime())

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