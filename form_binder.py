from PyQt4.QtGui import *
from PyQt4.QtCore import (QDate, QTime,
                        Qt, QVariant, pyqtSignal, QSettings,
                        QObject, QString, QDateTime, QSize)
from utils import log, info, warning
from qgis.gui import QgsAttributeEditor
from select_feature_tool import SelectFeatureTool
import os
import functools
from datatimerpickerwidget import DateTimePickerDialog

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

    def bindFeature(self, qgsfeature):
        """
        Binds a features values to the form.
        """    
        for index, value in qgsfeature.attributeMap().items():
            field = self.fields[index]
            control = self.forminstance.findChild(QWidget, field.name())

            if control is None:
                warning("Can't find control called %s" % (field.name()))
                continue

            success = self.bindValueToControl(control, value)
            if success:
                self.fieldtocontrol[index] = control

    def bindByName(self, controlname, value):
        control = self.forminstance.findChild(QWidget, controlname)

        if control is None:
            warning("Can't find control called %s" % (field.name()))
            return False
        
        success = self.bindValueToControl(control, value)
        return success

    def bindValueToControl(self, control, value):
        success = True
        if isinstance(control, QCalendarWidget):
            control.setSelectedDate(QDate.fromString( value.toString(), Qt.ISODate ))

        elif isinstance(control, QLineEdit):
            control.setText(value.toString())

        elif isinstance(control, QCheckBox):
            control.setChecked(value.toBool())

        elif isinstance(control, QComboBox):
            itemindex = control.findText(value.toString())
            if itemindex < 0:
                success = False

            control.setCurrentIndex( itemindex )
            
        elif isinstance(control, QDoubleSpinBox):
            control.setValue( value.toDouble()[0] )

        elif isinstance(control, QSpinBox):
            control.setValue( value.toInt()[0] )

        elif isinstance(control, QDateTimeEdit):
            control.setDateTime(QDateTime.fromString( value.toString(), Qt.ISODate ))
            # Wire up the date picker button
            parent = control.parentWidget()
            if parent:
                button = parent.findChild(QPushButton)
                if button:
                    button.setIcon(QIcon(":/icons/calender"))
                    button.setText("Pick")
                    button.setIconSize(QSize(24,24))
                    button.pressed.connect(functools.partial(self.pickDateTime, control, "DateTime" ))
        else:
            success = False

        if success:
            info("Binding %s to %s" % (control.objectName() , QVariant(value).toString()))
        else:
            warning("Can't bind %s to %s" % (control.objectName() ,value.toString()))

        return success
                    
    def unbindFeature(self, qgsfeature):
        """
        Unbinds the feature from the form saving the values back to the QgsFeature.

        Notes:
            If the parent of the control is a QGroupBox and is disabled, the control is ignored for changing.
        """
        for index, control in self.fieldtocontrol.items():
                value = None
                if isinstance(control, QLineEdit):
                    value = control.text()
                    
                elif isinstance(control, QCalendarWidget):
                    value = control.selectedDate().toString( Qt.ISODate )

                elif isinstance(control, QCheckBox):
                    value = 0
                    if control.isChecked():
                        value = 1
                elif isinstance(control, QComboBox):
                    value = control.currentText()

                elif isinstance(control, QDoubleSpinBox) or isinstance(control, QSpinBox):
                    value = control.value()

                elif isinstance(control, QDateTimeEdit):
                    value = control.dateTime().toString( Qt.ISODate )

                info("Setting value to %s from %s" % (value, control.objectName()))

                qgsfeature.changeAttribute( index, value)
        return qgsfeature

    def pickDateTime(self, control, mode):
        dlg = DateTimePickerDialog(mode)
        dlg.setDateTime(control.dateTime())
        if dlg.exec_():
            if hasattr(control, 'setDate'):
                control.setDate(dlg.getSelectedDate())

            if hasattr(control, 'setTime'):
                control.setTime(dlg.getSelectedTime())
            
    def bindSelectButtons(self):
        for group in self.settings.childGroups():
            control = self.forminstance.findChild(QToolButton, group)

            if control is None:
                continue
            
            name = control.objectName()
            control.clicked.connect(functools.partial(self.selectFeatureClicked, name))
            control.setIcon(QIcon(":/icons/select"))

    def selectFeatureClicked(self, controlName):
        layername = self.settings.value("%s/layer" % controlName ).toString()
        column = self.settings.value("%s/column" % controlName).toString()
        bindto = self.settings.value("%s/bindto" % controlName).toString()
        message = self.settings.value("%s/message" % controlName, "Please select a feature in the map").toString()

        self.tool = SelectFeatureTool(self.canvas, layername, column, bindto)
        self.tool.foundFeature.connect(self.bind)
        self.tool.setActive()
        self.canvas.setMapTool(self.tool)
        self.canvas.setCursor(self.tool.cursor)
        self.beginSelectFeature.emit(message)

    def bind(self, feature, value, bindto):
        self.bindByName(bindto, value)
        self.endSelectFeature.emit()