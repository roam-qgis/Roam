from PyQt4.QtGui import *
from PyQt4.QtCore import (QDate, Qt, QVariant, pyqtSignal, QSettings, QObject, QString, QSignalMapper)
from qgis.core import QgsMessageLog
from qgis.gui import QgsAttributeEditor
from SelectFeatureTool import SelectFeatureTool
import os
import functools

class FormBinder(QObject):
    beginSelectFeature = pyqtSignal()
    endSelectFeature = pyqtSignal()
    """
    Handles binding of values to and out of the form.
    """
    def __init__(self, layer, formInstance, canvas, settingspath):
        QObject.__init__(self)
        self.layer = layer
        self.canvas = canvas
        self.forminstance = formInstance
        self.fields = self.layer.pendingFields()
        self.fieldtocontrol = {}
        self.settingspath = settingspath
        self.actionlist = []
        self.settings = QSettings(self.settingspath, QSettings.IniFormat)

    def bindFeature(self, qgsfeature):
        """
        Binds a features values to the form.
        """    
        for index, value in qgsfeature.attributeMap().items():
            field = self.fields[index]
            if self.bindByName(field.name(), value):
                self.fieldtocontrol[index] = control

    def bindByName(self, controlname, value):
        QgsMessageLog.logMessage("Binding by name %s" % (controlname), "SDRC")
        control = self.forminstance.findChild(QWidget, controlname)

        if control is None:
            QgsMessageLog.logMessage("Control is null", "SDRC")
            return False

        return self.bindValueToControl(control, value)

    def bindValueToControl(self,control, value):
        failedbind = False
        if isinstance(control, QCalendarWidget):
            control.setSelectedDate(QDate.fromString( value.toString(), Qt.ISODate ))

        elif isinstance(control, QLineEdit):
            control.setText(value.toString())

        elif isinstance(control, QCheckBox):
            control.setChecked(value.toBool())

        elif isinstance(control, QComboBox):
            itemindex = control.findText(value.toString())
            if itemindex < 0:
                failedbind = True

            control.setCurrentIndex( itemindex )
        elif isinstance(control, QDoubleSpinBox):
            control.setValue( value.toDouble()[0] )

        elif isinstance(control, QSpinBox):
            control.setValue( value.toInt()[0] )

        if not failedbind:
            QgsMessageLog.logMessage("Binding %s to %s" % (control.objectName() , str(value)) ,"SDRC")
        else:
            QgsMessageLog.logMessage("Can't bind %s to %s" % (control.objectName() ,value.toString()) ,"SDRC")

        return failedbind
                    
    def unbindFeature(self, qgsfeature):
        """
        Unbinds the feature from the form saving the values back to the QgsFeature.

        Notes:
            If the parent of the control is a QGroupBox and is disabled, the control is ignored for changing.
        """
        import time
        for index, control in self.fieldtocontrol.items():
                value = None
                if isinstance(control, QLineEdit):
                    value = control.text()
                    
                if isinstance(control, QCalendarWidget):
                    value = control.selectedDate().toString( Qt.ISODate )

                if isinstance(control, QCheckBox):
                    value = 0
                    if control.isChecked():
                        value = 1
                if isinstance(control, QComboBox):
                    value = control.currentText()

                if isinstance(control, QDoubleSpinBox) or isinstance(control, QSpinBox):
                    value = control.value()

                QgsMessageLog.logMessage("Setting value to %s from %s" % (value, control.objectName()), "SDRC")

                qgsfeature.changeAttribute( index, value)
        return qgsfeature

    def bindSelectButtons(self):
        for group in self.settings.childGroups():
            control = self.forminstance.findChild(QToolButton, group)

            if control is None:
                continue
            
            name = control.objectName()
            control.clicked.connect(functools.partial(self.selectFeatureClicked, name))
            control.setIcon(QIcon(":/icons/select"))

    def selectFeatureClicked(self, controlName):
        settings = QSettings(self.settingspath, QSettings.IniFormat)
        layername = settings.value("%s/layer" % controlName ).toString()
        column = settings.value("%s/column" % controlName).toString()
        bindto = settings.value("%s/bindto" % controlName).toString()
        QgsMessageLog.logMessage("Getting feature for %s %s" % (layername, column), "SDRC")
        self.tool = SelectFeatureTool(self.canvas, layername, column, bindto)
        self.tool.foundFeature.connect(self.bind)
        self.canvas.setMapTool(self.tool)
        self.beginSelectFeature.emit()

    def bind(self, feature, value, bindto):
        self.bindByName(bindto, value)
        self.endSelectFeature.emit()