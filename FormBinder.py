from PyQt4.QtGui import QWidget, QLineEdit, QCheckBox, QComboBox, QCalendarWidget
from PyQt4.QtCore import QDate, Qt, QVariant
from qgis.core import QgsMessageLog
from qgis.gui import QgsAttributeEditor

class FormBinder():
    """
    Handles binding of values to and out of the form.
    """
    def __init__(self, layer, formInstance):
        self.layer = layer
        self.forminstance = formInstance
        self.fields = self.layer.pendingFields()
        self.fieldtocontrol = {}

    def bindFeature(self, qgsfeature):
        for index, value in qgsfeature.attributeMap().items():
            field = self.fields[index]
            control = self.forminstance.findChild(QWidget, field.name())
            if not control is None:
                if isinstance(control, QCalendarWidget):
                    control.setSelectedDate(QDate.fromString( value.toString(), Qt.ISODate ))
                    pass
                if isinstance(control, QLineEdit):
                    control.setText(value.toString())
                if isinstance(control, QCheckBox):
                    control.setChecked(value.toBool())
                    
                self.fieldtocontrol[id] = control
                QgsMessageLog.logMessage("Binding %s to %s" % (control.objectName() ,value.toString()) ,"SDRC")

    def unbindFeature(self, qgsfeature):
        for index, control in self.fieldtocontrol.items():
                value = None
                QgsMessageLog.logMessage(str(index))
                if isinstance(control, QLineEdit):
                    value = control.text()
                QgsMessageLog.logMessage("Setting value %s" % value, "SDRC")
        return qgsfeature

