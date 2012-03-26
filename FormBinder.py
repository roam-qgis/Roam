from PyQt4.QtGui import QWidget, QLineEdit
from qgis.core import QgsMessageLog

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
        for id, value in qgsfeature.attributeMap().items():
            field = self.fields[id]
            control = self.forminstance.findChild(QWidget, field.name())
            if not control is None:
                if isinstance(control, QLineEdit):
                    control.setText( value.toString() )
                    
                self.fieldtocontrol[id] = control

    def unbindFeature(self, qgsfeature):
        for index, control in self.fieldtocontrol.items():
                value = None
                if isinstance(control, QLineEdit):
                    value = control.text()

                QgsMessageLog.logMessage("Changing value %s" % value ,"SDRC")
                qgsfeature.changeAttribute( index, value)
        return qgsfeature

