from PyQt4.QtGui import *
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
        """
        Binds a features values to the form.
        """    
        for index, value in qgsfeature.attributeMap().items():
            field = self.fields[index]
            control = self.forminstance.findChild(QWidget, field.name())
            failedbind = False
            
            if not control is None:
                if isinstance(control, QCalendarWidget):
                    control.setSelectedDate(QDate.fromString( value.toString(), Qt.ISODate ))

                if isinstance(control, QLineEdit):
                    control.setText(value.toString())

                if isinstance(control, QCheckBox):
                    control.setChecked(value.toBool())

                if isinstance(control, QComboBox):
                    itemindex = control.findText(value.toString())
                    if itemindex < 0:
                        failedbind = True

                    control.setCurrentIndex( itemindex )

                if isinstance(control, QDoubleSpinBox):
                    control.setValue( value.toDouble()[0] )

                if isinstance(control, QSpinBox):
                    control.setValue( value.toInt()[0] )
                    
                self.fieldtocontrol[index] = control
                
                if not failedbind:
                    QgsMessageLog.logMessage("Binding %s to %s" % (control.objectName() ,value.toString()) ,"SDRC")
                else:
                    QgsMessageLog.logMessage("Can't bind %s to %s" % (control.objectName() ,value.toString()) ,"SDRC")
                    
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

