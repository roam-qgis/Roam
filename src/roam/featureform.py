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
                         QDateTimeEdit,
                         QBoxLayout,
                         QSpacerItem,
                         QFormLayout)

from qgis.core import QgsFields, QgsFeature

from roam.editorwidgets.core import WidgetsRegistry
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

def buildfromui(uifile):
    return uic.loadUi(uifile)

def buildfromauto(formconfig):
    widgetsconfig = formconfig['widgets']

    outlayout = QFormLayout()
    outwidget = QWidget()
    outwidget.setLayout(outlayout)
    for config in widgetsconfig:
        widgettype = config['widget']
        field = config['field']
        name = config.get('name', field)
        label = QLabel(name)
        label.setObjectName(field + "_label")
        widgetwrapper = WidgetsRegistry.createwidget(widgettype,
                                                    layer=None,
                                                    field=field,
                                                    widget=None,
                                                    label=label,
                                                    config=None)
        widget = widgetwrapper.widget
        widget.setObjectName(field)
        layoutwidget = QWidget()
        layoutwidget.setLayout(QBoxLayout(QBoxLayout.LeftToRight))
        layoutwidget.layout().addWidget(widget)
        if config.get('rememberlastvalue', False):
            savebutton = QToolButton()
            savebutton.setObjectName('{}_save'.format(field))
            layoutwidget.layout().addWidget(savebutton)

        hidden = config.get('hidden', False)
        if not hidden:
            outlayout.addRow(label, layoutwidget)

    outlayout.addItem(QSpacerItem(10,10))
    return outwidget


class FeatureForm(QObject):
    """
    An object that represents a feature form in Roam.  This object will create and bind
    the widget for the form config.

    You may override this in forms __init__.py module in order to add custom logic in the following
    places:

        - loading
        - loaded
        - accpet
        - reject
        - featuresaved


    class MyModule(FeatureForm):
        def __init__(self, widget, form, formconfig):
            super(MyModule, self).__init__(widget, form, formconfig)

        def accept(self):
            ....


    In order to register your feature form class you need to call `form.registerform` from the init_form method
    in your form module

    def init_form(form):
        form.registerform(MyModule)


    You can access form settings using:

        >>> self.formconfigs

    You can get the QGIS layer for the form using:

        >>> self.form.QGISLayer/
    """
    requiredfieldsupdated = pyqtSignal(bool)
    formvalidation = pyqtSignal(bool)
    helprequest = pyqtSignal(str)
    showwidget = pyqtSignal(QWidget)
    loadform = pyqtSignal()
    rejected = pyqtSignal(str)

    def __init__(self, widget, form, formconfig, feature, defaults):
        super(FeatureForm, self).__init__()
        self.widget = widget
        self.form = form
        self.formconfig = formconfig
        self.boundwidgets = []
        self.requiredfields = {}
        self.feature = feature
        self.fields = self.feature.fields()
        self.defaults = defaults

    @classmethod
    def from_form(cls, form, formconfig, feature, defaults, parent=None):
        """
        Create a feature form the given Roam form.
        :param form: A Roam form
        :param parent:
        :return:
        """
        formtype = formconfig['type']
        if formtype == 'custom':
            uifile = os.path.join(form.folder, "form.ui")
            widget = buildfromui(uifile)
        elif formtype == 'auto':
            widget = buildfromauto(formconfig)
        else:
            raise NotImplemented('Other form types not supported yet')

        widget.setStyleSheet(style)

        featureform = cls(widget, form, formconfig, feature, defaults)
        featureform.createhelplinks(widget)
        widget.setProperty('featureform', featureform)

        widgettypes = [QLineEdit, QPlainTextEdit, QDateTimeEdit]
        map(featureform._installeventfilters, widgettypes)

        return featureform

    def _installeventfilters(self, widgettype):
        for widget in self.widget.findChildren(widgettype):
            widget.installEventFilter(self)

    def eventFilter(self, parent, event):
        """ Handle mouse click events for disabled widget state """
        if event.type() == QEvent.FocusIn:
            cmd = r'C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe'
            os.startfile(cmd)

        return QObject.eventFilter(self, parent, event)

    def load(self, feature, layers, editing):
        """
        Called before the form is loaded. This method can be used to do pre checks and halt the loading of the form
        if needed.

        When implemented, this method should always return a tuple with a pass state and a message.

        Calling self.continue_() will let the form continue to be opened.
        Calling self.reject("Your message") will stop the opening of the form and show the message to the user.

            >>> self.reject("Sorry you can't load this form now")

            or

            >>> self.continue_()

        You may alter the QgsFeature given.
        """
        self.continue_()


    def continue_(self):
        self.loadform.emit()

    def loaded(self):
        pass

    def accept(self):
        return True

    def reject(self, message=None):
        self.rejected.emit(message)

    @property
    def allpassing(self):
        return all(valid for valid in self.requiredfields.values())

    def updaterequired(self, field, passed):
        self.requiredfields[field] = passed
        passed = self.allpassing
        self.formvalidation.emit(passed)

    def validateall(self, widgetwrappers):
        for wrapper in widgetwrappers:
            wrapper.validate()

    @property
    def editingmode(self):
        return self.feature.id() > 0

    def bind(self):
        """
        Binds the given feature to the to the feature form.
        :param feature:
        :param defaults: The lookup containing the default values.  Note: This is only used to toggle
        the save buttons.  Default values should be set before the feature is given to the bind function.
        :return:
        """
        widgetsconfig = self.formconfig['widgets']

        for config in widgetsconfig:
            widgettype = config['widget']
            print widgettype
            field = config['field']
            widget = self.widget.findChild(QWidget, field)
            label = self.widget.findChild(QLabel, "{}_label".format(field))
            widgetconfig = config.get('config', {})
            widgetwrapper = WidgetsRegistry.createwidget(widgettype,
                                                         self.form.QGISLayer,
                                                         field,
                                                         widget,
                                                         label,
                                                         widgetconfig)

            print widgetwrapper
            if widgetwrapper is None:
                print("No widget found for {}".format(widgettype))
                continue

            readonlyrules = config.get('read-only-rules', [])

            if self.editingmode and 'editing' in readonlyrules:
                widgetwrapper.readonly = True
            elif 'insert' in readonlyrules:
                widgetwrapper.readonly = True

            if 'always' in readonlyrules:
                widgetwrapper.readonly = True

            widgetwrapper.hidden = config.get('hidden', False)

            if config.get('required', False) and not widgetwrapper.hidden:
                # All widgets state off as false unless told otherwise
                self.requiredfields[field] = False
                widgetwrapper.setrequired()
                widgetwrapper.validationupdate.connect(self.updaterequired)

            try:
                print "Null Check"
                print self.feature.fields().toList()
                value = nullcheck(self.feature[field])
                print value
            except KeyError:
                utils.warning("Can't find field {}".format(field))
                value = None

            widgetwrapper.setvalue(value)
            self._bindsavebutton(field)
            self.boundwidgets.append(widgetwrapper)

        self.validateall(self.boundwidgets)

    def unbind(self):
        def shouldsave(field):
            button = self.widget.findChild(QToolButton, "{}_save".format(field))
            if button:
                return button.isChecked()

        before = QgsFeature(self.feature)
        before.setFields(self.fields, initAttributes=False)
        after = QgsFeature(self.feature)
        after.setFields(self.fields, initAttributes=False)

        self.feature.setFields(self.fields, initAttributes=False)
        savedvalues = {}
        for wrapper in self.boundwidgets:
            value = wrapper.value()
            field = wrapper.field
            if shouldsave(field):
                savedvalues[field] = value
            self.feature[field] = value

        return before, self.feature, savedvalues

    def _bindsavebutton(self, field):
        button = self.widget.findChild(QToolButton, "{}_save".format(field))
        if not button:
            return

        button.setCheckable(not self.feature.id() > 0)
        button.setIcon(QIcon(":/icons/save_default"))
        button.setIconSize(QSize(24, 24))
        button.setChecked(field in self.defaults)
        button.setVisible(not self.editingmode)

    def createhelplinks(self, widget):
        def createhelplink(label, folder):
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
                label.linkActivated.connect(self.helprequest.emit)

        for label in widget.findChildren(QLabel):
            createhelplink(label, self.form.folder)


