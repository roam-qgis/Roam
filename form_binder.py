import tempfile
import uuid
import os.path
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
from drawingpad import DrawingPad
import sdrcdatacapture
import tarfile

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
        self.images = []

    def bindFeature(self, qgsfeature):
        """
        Binds a features values to the form.
        """
        self.feature = qgsfeature
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
                
        elif isinstance(control, QLineEdit) or isinstance(control, QTextEdit):
            control.setText(value.toString())
            
        elif isinstance(control, QCheckBox) or isinstance(control, QGroupBox):
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
                button = parent.findChild(QPushButton, control.objectName() + "_pick" )
                if button:
                    button.setIcon(QIcon(":/icons/calender"))
                    button.setText("Pick")
                    button.setIconSize(QSize(24,24))
                    button.pressed.connect(functools.partial(self.pickDateTime, control, "DateTime" ))
        elif isinstance(control, QPushButton):
            if control.text() == "Drawing":
                control.setIcon(QIcon(":/icons/draw"))
                control.setIconSize(QSize(24,24))
                control.pressed.connect(functools.partial(self.loadDrawingTool, control, None))
                
        else:
            success = False

        if success:
            info("Binding %s to %s" % (control.objectName() , QVariant(value).toString()))
        else:
            warning("Can't bind %s to %s" % (control.objectName() ,value.toString()))

        return success

    def loadDrawingTool(self, control, image):
        self.forminstance.hide()
        curdir = os.path.dirname(__file__)
        id = self.feature.attributeMap()[self.layer.fieldNameIndex("UniqueID")].toString()
        name = str(id) + "_" + str(control.objectName()) + ".jpg"
        imagename = os.path.join(curdir, "data", str(self.layer.name()), "images", \
                                name)

        log("Looking for " + imagename)
        
        self.drawingpad = DrawingPad(imagename)
        self.drawingpad.rejected.connect(self.drawingPadReject)
        self.drawingpad.accepted.connect(functools.partial(self.drawingPadAccept, control))
        self.drawingpad.ui.actionMapSnapshot.triggered.connect(self.drawingPadMapSnapshot)
        self.drawingpad.showFullScreen()
        self.drawingpad.raise_()
        self.drawingpad.activateWindow()

    def drawingPadReject(self):
        self.forminstance.show()

    def drawingPadAccept(self, control):
        self.forminstance.show()
        name = "drawingFor_" + str(control.objectName())
        tempimage = os.path.join(tempfile.gettempdir(), name)
        self.images.append(tempimage + ".jpg")
        self.drawingpad.saveImage(tempimage)

    def drawingPadMapSnapshot(self):
        #TODO Refactor me!!
        image = QPixmap.fromImage(self.drawingpad.scribbleArea.image)
        tempimage = os.path.join(tempfile.gettempdir(), "mapcanvascapture.png")
        self.canvas.saveAsImage(tempimage, image)
        self.drawingpad.openImage(tempimage)
                    
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

                elif isinstance(control, QTextEdit):
                    value = control.toPlainText()
                    
                elif isinstance(control, QCalendarWidget):
                    value = control.selectedDate().toString( Qt.ISODate )

                elif isinstance(control, QCheckBox) or isinstance(control, QGroupBox):
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
            control.setIconSize(QSize(24,24))

    def selectFeatureClicked(self, controlName):
        layername = self.settings.value("%s/layer" % controlName ).toString()
        column = self.settings.value("%s/column" % controlName).toString()
        bindto = self.settings.value("%s/bindto" % controlName).toString()
        message = self.settings.value("%s/message" % controlName, "Please select a feature in the map").toString()
        searchsize = self.settings.value("%s/searchradius" % controlName, 5 ).toInt()[0]

        layer = None
        for l in self.canvas.layers():
            if l.name() == layername:
                layer = l
                break

        if layer is None:
            return 
        
        self.tool = SelectFeatureTool(self.canvas, layer, column, bindto, searchsize)
        self.tool.foundFeature.connect(self.bind)
        self.tool.setActive()
        self.canvas.setMapTool(self.tool)
        self.canvas.setCursor(self.tool.cursor)
        self.beginSelectFeature.emit(message)

    def bind(self, feature, value, bindto):
        self.bindByName(bindto, value)
        self.endSelectFeature.emit()