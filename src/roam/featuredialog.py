import os
import sys
import subprocess
import types
import json

from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, QObject, QSize, QEvent, QProcess, Qt, QPyNullVariant
from PyQt4.QtGui import (QWidget,
                         QDialogButtonBox,
                         QStatusBar,
                         QLabel,
                         QGridLayout,
                         QToolButton,
                         QIcon,
                         QLineEdit,
                         QPlainTextEdit,
                         QComboBox,
                         QDateTimeEdit)

from qgis.core import QgsFields

from roam.editorwidgets.core import WidgetsRegistry
from roam.helpviewdialog import HelpViewDialog
from roam import utils

style = """
            QCheckBox::indicator {
                 width: 40px;
                 height: 40px;
             }

            * {
                font: 20px "Segoe UI" ;
            }

            QLabel {
                color: #4f4f4f;
            }

            QDialog { background-color: rgb(255, 255, 255); }
            QScrollArea { background-color: rgb(255, 255, 255); }

            QPushButton {
                border: 1px solid #e1e1e1;
                 padding: 6px;
                color: #4f4f4f;
             }

            QPushButton:hover {
                border: 1px solid #e1e1e1;
                 padding: 6px;
                background-color: rgb(211, 228, 255);
             }

            QCheckBox {
                color: #4f4f4f;
            }

            QComboBox {
                border: 1px solid #d3d3d3;
            }

            QComboBox::drop-down {
            width: 30px;
            }
"""

values_file = os.path.join(os.environ['APPDATA'], "Roam")


def loadsavedvalues(layer):
    attr = {}
    id = str(layer.id())
    savedvaluesfile = os.path.join(values_file, "%s.json" % id)
    try:
        utils.log(savedvaluesfile)
        with open(savedvaluesfile, 'r') as f:
            attr = json.loads(f.read())
    except IOError:
        utils.log('No saved values found for %s' % id)
    except ValueError:
        utils.log('No saved values found for %s' % id)
    return attr


def savevalues(layer, values):
    savedvaluesfile = os.path.join(values_file, "%s.json" % str(layer.id()))
    print savedvaluesfile
    folder = os.path.dirname(savedvaluesfile)
    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(savedvaluesfile, 'w') as f:
        json.dump(values, f)


def nullcheck(value):
    if isinstance(value, QPyNullVariant):
        return None
    else:
        return value


class FeatureForm(QObject):
    requiredfieldsupdated = pyqtSignal(bool)
    formvalidation = pyqtSignal(bool)

    def __init__(self, widget, layer, layerconfig, qmaplayer):
        super(FeatureForm, self).__init__()
        self.widget = widget
        self.qmaplayer = qmaplayer
        self.layerconfig = layerconfig
        self.layer = layer
        self.boundwidgets = []
        self.requiredfields = {}
        self.feature = None

    @classmethod
    def from_layer(cls, layer, layerconfig, qmaplayer, parent=None):
        formconfig = layerconfig['form']
        formtype = formconfig['type']
        if formtype == 'custom':
            uifile = os.path.join(qmaplayer.folder, "form.ui")
            widget = uic.loadUi(uifile)
        else:
            raise NotImplemented('Other form types not supported yet')

        widget.setStyleSheet(style)

        form = cls(widget, layer, layerconfig, qmaplayer)
        widgettypes = [QLineEdit, QPlainTextEdit, QDateTimeEdit]
        map(form._installeventfilters, widgettypes)
        widget.setProperty('featureform', form)

        return form

    def _installeventfilters(self, widgettype):
        for widget in self.widget.findChildren(widgettype):
            widget.installEventFilter(self)

    def eventFilter(self, parent, event):
        """ Handle mouse click events for disabled widget state """
        if event.type() == QEvent.FocusIn:
            cmd = r'C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe'
            os.startfile(cmd)

        return QObject.eventFilter(self, parent, event)

    def accept(self):
        #TODO Call form module accept method
        return True

    def reject(self):
        #TODO Call form module reject method
        return True

    def acceptbutton(self):
        try:
            buttonbox = self.widget.findChildren(QDialogButtonBox)[0]
            savebutton = buttonbox.button(QDialogButtonBox.Save)
            return savebutton
        except IndexError:
            return None

    def updaterequired(self, field, passed):
        self.requiredfields[field] = passed
        passed = all(valid for valid in self.requiredfields.values())
        self.formvalidation.emit(passed)

    def validateall(self, widgetwrappers):
        for wrapper in widgetwrappers:
            wrapper.validate()

    def bindfeature(self, feature, defaults={}):
        fieldsconfig = self.layerconfig['fields']
        self.feature = feature
        # Ummm why do the fields go out of scope :S
        self.fields = QgsFields(self.feature.fields())

        for field, config in fieldsconfig.iteritems():
            widget = self.widget.findChild(QWidget, field)
            label = self.widget.findChild(QLabel, "{}_label".format(field))
            widgetconfig = config['widget']
            widgettype = widgetconfig['widgettype']
            widgetwrapper = WidgetsRegistry.createwidget(widgettype, self.layer, field, widget, label, widgetconfig)

            if widgetwrapper is None:
                print("No widget found for {}".format(widgettype))
                continue

            if config.get('required', False):
                # All widgets state off as false unless told otherwise
                self.requiredfields[field] = False
                widgetwrapper.setrequired()
                widgetwrapper.validationupdate.connect(self.updaterequired)

            value = defaults.get(field, nullcheck(feature[field]))
            widgetwrapper.setvalue(value)
            self.bindsavebutton(field, defaults, feature.id() > 0)
            self.boundwidgets.append(widgetwrapper)

        self.validateall(self.boundwidgets)
        self.createhelplinks(self.widget)

    def bindsavebutton(self, field, defaults, editmode):
        button = self.widget.findChild(QToolButton, "{}_save".format(field))
        if not button:
            return

        button.setCheckable(not editmode)
        button.setIcon(QIcon(":/icons/save_default"))
        button.setIconSize(QSize(24, 24))
        button.setChecked(field in defaults)
        button.setVisible(not editmode)

    def createhelplinks(self, widget):
        for label in widget.findChildren(QLabel):
            self.createhelplink(label, self.qmaplayer.folder)

    def createhelplink(self, label, folder):
        def showhelp(url):
            """
            Show the help viewer for the given field
            """
            dlg = HelpViewDialog()
            dlg.loadFile(url)
            dlg.exec_()

        def getHelpFile():
            # TODO We could just use the tooltip from the control to show help
            # rather then having to save out a html file.
            name = label.objectName()
            if name.endswith("_label"):
                name = name[:-6]
            filename = "{}.html".format(name)
            filepath = os.path.join(folder, "help", filename)
            if os.path.exists(filepath):
                return filepath
            else:
                return None

        if label is None:
            return

        helpfile = getHelpFile()
        if helpfile:
            text = '<a href="{}">{}<a>'.format(helpfile, label.text())
            label.setText(text)
            label.linkActivated.connect(partial(showhelp))

    def getupdatedfeature(self):
        def shouldsave(field):
            button = self.widget.findChild(QToolButton, "{}_save".format(field))
            if button:
                return button.isChecked()

        self.feature.setFields(self.fields)
        savedvalues = {}
        for wrapper in self.boundwidgets:
            value = wrapper.value()
            field = wrapper.field
            if shouldsave(field):
                savedvalues[field] = value
            self.feature[field] = value

        return self.feature, savedvalues
