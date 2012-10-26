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
from utils import log, warning
import re


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
    def __init__(self, layer, formInstance, canvas, settings, formmodule, db):
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
        self.forsaving = set()
        self.formmodule = formmodule
        self.db = db

    def bindFeature(self, qgsfeature, mandatory_fields=True, editing=False):
        """
        Binds a features values to the form. If the control has the mandatory
        property set then it will be added to the mandatory group.

        qgsfeature - A QgsFeature to bind the values from
        mandatory_fields - True if mandatory fields should be respected (default)
        """
        self.feature = qgsfeature
        self.connectControlsToSQLCommands()
        defaults = self.getDefaults()
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

            isdefaultset = False
            if not editing:
                try:
                    # Get the default value from the database and use that instead.
                    value = defaults[control]
                    isdefaultset = control in defaults
                except KeyError:
                    pass

            try:
                self.bindValueToControl(control, value)
            except BindingError as er:
                warning(er.reason)

            self.bindSaveValueButton(control, indefaults=isdefaultset)
            self.createHelpLink(control)

            self.fieldtocontrol[index] = control

    def createHelpLink(self, control):
        name = control.objectName()
        helpfile = self.formmodule.getHelpFile(name)
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
    
    def getDefaults(self):
        query = QSqlQuery("SELECT control, value FROM DefaultValues")
        query.exec_()
        defaults = {}
        while query.next():
            try:
                name = query.value(0).toString()
                control = self.getControl(name)
            except ControlNotFound:
                continue

            value = query.value(1)
            defaults[control] = value
        return defaults

    def connectControlsToSQLCommands(self):
        """
            Loops all the controls and connects update signals
            in order to use SQL commands correctly.

            Note: We check all control because we can use SQL on non
            field bound controls in order to show information.
        """
        for control in self.forminstance.findChildren(QWidget):
            self.connectSQL(control)

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
        query = QSqlQuery()
        query.prepare("SELECT value FROM ComboBoxItems WHERE control = :contorl")
        query.bindValue(":control", name)
        query.exec_()
        log("LAST ERROR")
        log(query.lastError().text())
        items = []
        while query.next():
            value = query.value(0).toString()
            if not value.isEmpty():
                items.append(str(value))

        if not text in comboitems and not text in items:
            query = QSqlQuery()
            query.prepare("INSERT INTO ComboBoxItems (control, value)" \
                          "VALUES (:control,:value)")
            query.bindValue(":control", name)
            query.bindValue(":value", text)
            query.exec_()
            log("LAST ERROR FOR INSERT")
            log(query.lastError().text())

    def updateControl(self, control, mapping, sql, *args):
        """
            Update control with result from SQL query.
        """
        query = QSqlQuery()
        query.prepare(sql)
        # Loop though all the placeholders and get value from the
        # function assigned to each one.
        for holder, function in mapping.items():
            value = function()
            query.bindValue(":%s" % holder, value)

        query.exec_()

        for key, value in query.boundValues().items():
            log("%s is %s" % (key, value.toString()))

        if isinstance(control, QComboBox):
            control.clear()
            control.addItem("")
            while query.next():
                value = query.value(0).toString()
                if not value.isEmpty():
                    control.addItem(value)

    def connectSQL(self, control):
        sql = control.property("sql").toString()
        if not sql.isEmpty():
            log("QUERY:%s" % sql)
            placeholders = re.findall(r':(\w+)', sql)
            mapping = {}
            # Loop though all the sql placeholders and look for a
            # control with that name to get updates from.
            for holder in placeholders:
                linked_control = self.getControl(holder)
                if linked_control is None:
                    continue

                if isinstance(linked_control, QListWidget):
                    mapping[holder] = lambda c = linked_control: c.currentItem().text()
                    linked_control.currentItemChanged.connect(partial(self.updateControl, \
                                                                      control, mapping, sql ))

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
                control.currentItemChanged.emit(None, items[0])
            except IndexError:
                pass

        elif isinstance(control, QLineEdit) or isinstance(control, QTextEdit):
            control.setText(value.toString())

        elif isinstance(control, QCheckBox) or isinstance(control, QGroupBox):
            control.setChecked(value.toBool())

        elif isinstance(control, QPlainTextEdit):
            control.setPlainText(value.toString())

        elif isinstance(control, QComboBox):
            # Add items stored in the database
            query = QSqlQuery()
            query.prepare("SELECT value FROM ComboBoxItems WHERE control = :contorl")
            query.bindValue(":control", control.objectName())
            query.exec_()
            while query.next():
                newvalue = query.value(0).toString()
                if not newvalue.isEmpty():
                    control.addItem(newvalue)

            itemindex = control.findText(value.toString())
            if itemindex == -1:
                control.insertItem(0,value.toString())
                control.setCurrentIndex(0)
            else:
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

                elif isinstance(control, QTextEdit) or isinstance(control, QPlainTextEdit):
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

                elif isinstance(control, QListWidget):
                    item = control.currentItem()
                    if item:
                        value = item.text()
                    else:
                        return QString("")

                info("Setting value to %s from %s" % (value, control.objectName()))
                qgsfeature.changeAttribute(index, value)

                # Save the value to the database as a default if it is needed.
                if self.shouldSaveValue(control):
                    self.saveDefault(control, value)
                else:
                    self.removeDefault(control)

        return qgsfeature

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
            log("save button found for %s" % control.objectName())
        except ControlNotFound:
            return

        log("_save button for %s is %s" % (control.objectName(), str(button.isChecked()) ))
        return button.isChecked()

    def bindSaveValueButton(self, control, indefaults=False):
        try:
            button = self.getControl(control.objectName() + "_save", QToolButton)
        except ControlNotFound:
            return

        button.setCheckable(True)
        button.setIcon(QIcon(":/icons/save_default"))
        button.setIconSize(QSize(24, 24))
        button.setChecked(indefaults)

    def removeDefault(self, control):
        name = control.objectName()
        query = QSqlQuery()
        query.prepare("DELETE FROM DefaultValues WHERE control = :control")
        query.bindValue(":control", name)
        query.exec_()

    def saveDefault(self, control, value):
        self.removeDefault(control)
        name = control.objectName()
        query = QSqlQuery()
        query.prepare("INSERT INTO DefaultValues (control, value)" \
                      "VALUES (:control,:value)")
        query.bindValue(":control", name)
        query.bindValue(":value", value)
        query.exec_()

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