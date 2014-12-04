import os
import sys
import subprocess
import types
import tempfile
import json

from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, QObject, QSize, QEvent, QProcess, Qt, QPyNullVariant, QRegExp
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
                         QFormLayout,
                         QSpinBox,
                         QDoubleSpinBox)

from qgis.core import QgsFields, QgsFeature, QgsGPSConnectionRegistry
from qgis.gui import QgsMessageBar

from roam.editorwidgets.core import EditorWidgetException
from roam import utils
from roam.flickwidget import FlickCharm
from roam.structs import CaseInsensitiveDict
from roam.api import RoamEvents, GPS
from roam.api import utils as qgisutils

import roam.editorwidgets.core
import roam.defaults as defaults
import roam.roam_style
import roam.utils

values_file = os.path.join(tempfile.gettempdir(), "Roam")

nullcheck = qgisutils.nullcheck


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
    folder = os.path.dirname(savedvaluesfile)
    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(savedvaluesfile, 'w') as f:
        json.dump(values, f)


def buildfromui(uifile, base):
    widget = uic.loadUi(uifile, base)
    return installflickcharm(widget)


def buildfromauto(formconfig, base):
    widgetsconfig = formconfig['widgets']

    outlayout = QFormLayout()
    outlayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    outwidget = base
    outwidget.setLayout(outlayout)
    for config in widgetsconfig:
        widgettype = config['widget']
        field = config['field']
        name = config.get('name', field)
        if not field:
            utils.warning("Field can't be null for {}".format(name))
            utils.warning("Skipping widget")
            continue
        label = QLabel(name)
        label.setObjectName(field + "_label")
        widget = roam.editorwidgets.core.createwidget(widgettype, parent=base)
        widget.setObjectName(field)
        layoutwidget = QWidget()
        layoutwidget.setLayout(QBoxLayout(QBoxLayout.LeftToRight))
        layoutwidget.layout().addWidget(widget)
        if config.get('rememberlastvalue', False):
            savebutton = QToolButton()
            savebutton.setObjectName('{}_save'.format(field))
            layoutwidget.layout().addWidget(savebutton)

        outlayout.addRow(label, layoutwidget)

    outlayout.addItem(QSpacerItem(10, 10))
    installflickcharm(outwidget)
    return outwidget


def installflickcharm(widget):
    """
    Installs the flick charm on every widget on the form.
    """
    widget.charm = FlickCharm()
    for child in widget.findChildren(QWidget):
        widget.charm.activateOn(child)
    return widget

RejectedException = roam.editorwidgets.core.RejectedException


FeatureSaveException = qgisutils.FeatureSaveException
MissingValuesException = qgisutils.MissingValuesException

class DeleteFeatureException(FeatureSaveException):
    pass


class FeatureFormBase(QWidget):
    requiredfieldsupdated = pyqtSignal(bool)
    formvalidation = pyqtSignal(bool)
    helprequest = pyqtSignal(str)
    showwidget = pyqtSignal(QWidget)
    loadform = pyqtSignal()
    rejected = pyqtSignal(str, int)
    enablesave = pyqtSignal(bool)
    showlargewidget = pyqtSignal(object, object, object, dict)

    def __init__(self, form, formconfig, feature, defaults, parent, *args, **kwargs):
        super(FeatureFormBase, self).__init__(parent)
        self.form = form
        self.formconfig = formconfig
        self.boundwidgets = CaseInsensitiveDict()
        self.requiredfields = CaseInsensitiveDict()
        self.feature = feature
        self.defaults = defaults
        self.bindingvalues = CaseInsensitiveDict()
        self.editingmode = kwargs.get("editmode", False)

    def open_large_widget(self, widgettype, lastvalue, callback, config=None):
        self.showlargewidget.emit(widgettype, lastvalue, callback, config)

    @property
    def is_capturing(self):
        return self.editingmode == False

    @is_capturing.setter
    def is_capturing(self, value):
        self.editingmode = not value

    def updaterequired(self, value):
        passed = self.allpassing
        self.formvalidation.emit(passed)

    def validateall(self):
        widgetwrappers = self.boundwidgets.itervalues()
        for wrapper in widgetwrappers:
            wrapper.validate()

    def setupui(self):
        """
        Setup the widget in the form
        """
        widgetsconfig = self.formconfig['widgets']

        layer = self.form.QGISLayer
        # Crash in QGIS if you lookup a field that isn't found.
        # We just make a dict with all fields lower because QgsFields is case sensitive.
        fields = {field.name().lower():field for field in layer.pendingFields().toList()}

        for config in widgetsconfig:
            widgettype = config['widget']
            field = config['field']
            if not field:
                utils.info("Skipping widget. No field defined")
                continue

            field = field.lower()

            if field in self.boundwidgets:
                utils.warning("Sorry you can't bind the same field ({}) twice.".format(field))
                utils.warning("{} for field {} has been ignored in setup".format(widget, field))
                continue

            widget = self.findcontrol(field)
            if widget is None:
                widget = roam.editorwidgets.core.createwidget(widgettype)
                config['hidden'] = True
                utils.info("No widget named {} found so we have made one.".format(field))

            label = self.findcontrol("{}_label".format(field))
            if label is None:
                utils.debug("No label found for {}".format(field))

            widgetconfig = config.get('config', {})
            qgsfield = fields[field]
            try:
                widgetwrapper = roam.editorwidgets.core.widgetwrapper(widgettype=widgettype,
                                                                      layer=self.form.QGISLayer,
                                                                      field=qgsfield,
                                                                      widget=widget,
                                                                      label=label,
                                                                      config=widgetconfig)
            except EditorWidgetException as ex:
                utils.exception(ex)
                continue

            readonlyrules = config.get('read-only-rules', [])

            if self.editingmode and 'editing' in readonlyrules:
                widgetwrapper.readonly = True
            elif 'insert' in readonlyrules or 'always' in readonlyrules:
                widgetwrapper.readonly = True

            widgetwrapper.hidden = config.get('hidden', False)

            widgetwrapper.required = config.get('required', False)

            widgetwrapper.valuechanged.connect(self.updaterequired)
            widgetwrapper.largewidgetrequest.connect(RoamEvents.show_widget.emit)

            self._bindsavebutton(field)
            self.boundwidgets[field] = widgetwrapper

    def bindvalues(self, values, update=False):
        """
        Bind the values to the form.
        """
        if not update:
            self.bindingvalues = CaseInsensitiveDict(values)
        else:
            for key, value in values.iteritems():
                try:
                    self.bindingvalues[key] = value
                except KeyError:
                    continue

        for field, value in values.iteritems():
            value = nullcheck(value)
            try:
                wrapper = self.boundwidgets[field]
                if hasattr(wrapper, 'savetofile') and wrapper.savetofile:
                    if value and not os.path.exists(value):
                        value = os.path.join(self.form.project.image_folder, value)

                self.boundwidgets[field].setvalue(value)
            except KeyError:
                utils.debug("Can't find control for field {}. Ignoring".format(field))

        self.validateall()

    def bind_feature(self, feature):
        self.feature = feature
        values = self.form.values_from_feature(feature)
        self.bindvalues(values)

    def getvalues(self):
        def shouldsave(field):
            name = "{}_save".format(field)
            button = self.findcontrol(name)
            if not button is None:
                return button.isChecked()

        savedvalues = {}
        values = CaseInsensitiveDict(self.bindingvalues)
        for field, wrapper in self.boundwidgets.iteritems():
            value = wrapper.value()
            # TODO this should put pulled out and unit tested
            if hasattr(wrapper, 'savetofile') and wrapper.savetofile:
                if wrapper.filename and self.editingmode:
                    name = os.path.basename(wrapper.filename)
                    name, extension = os.path.splitext(name)

                    if wrapper.modified:
                        if not name.endswith("_edited"):
                            newend = "_edited{}".format(extension)
                            value = name + newend
                        else:
                            value = os.path.basename(wrapper.filename)
                    else:
                        value = os.path.basename(wrapper.filename)
                else:
                    if wrapper.modified:
                        value = wrapper.get_filename()
                    else:
                        value = ''

            if shouldsave(field):
                savedvalues[field] = value
            values[field] = value

        return values, savedvalues

    def findcontrol(self, name):
        regex = QRegExp("^{}$".format(name))
        regex.setCaseSensitivity(Qt.CaseInsensitive)
        try:
            widget = self.findChildren(QWidget, regex)[0]
        except IndexError:
            widget = None
        return widget

    def _bindsavebutton(self, field):
        name = "{}_save".format(field)
        button = self.findcontrol(name)
        if button is None:
            return

        button.setCheckable(not self.editingmode)
        button.setIcon(QIcon(":/icons/save_default"))
        button.setIconSize(QSize(24, 24))
        button.setChecked(field in self.defaults)
        button.setVisible(not self.editingmode)

    def createhelplinks(self):
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

        for label in self.findChildren(QLabel):
            createhelplink(label, self.form.folder)

    def widget_default(self, name):
        """
        Return the default value for the given widget
        """
        try:
            widgetconfig = self.form.widget_by_field(name)
        except IndexError:
            raise KeyError("Widget with name {} not found on form".format(name))

        if not 'default' in widgetconfig:
            raise KeyError('Default value not defined for this field {}'.format(name))

        return defaults.widget_default(widgetconfig, self.feature, self.form.QGISLayer)

    def close_form(self, reason=None, level=1):
        self.rejected.emit(reason, level)


class FeatureForm(FeatureFormBase):
    """
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

    def __init__(self, form, formconfig, feature, defaults, parent, *args, **kwargs):
        super(FeatureForm, self).__init__(form, formconfig, feature, defaults, parent, *args, **kwargs)
        self.deletemessage = 'Do you really want to delete this feature?'
        GPS.gpsposition.connect(self.ongpsupdated)

    @classmethod
    def from_form(cls, form, formconfig, feature, defaults, parent=None, *args, **kwargs):
        """
        Create a feature form the given Roam form.
        :param form: A Roam form
        :param parent:
        :return:
        """
        formtype = formconfig['type']
        featureform = cls(form, formconfig, feature, defaults, parent, *args, **kwargs)

        if formtype == 'custom':
            uifile = os.path.join(form.folder, "form.ui")
            featureform = buildfromui(uifile, base=featureform)
        elif formtype == 'auto':
            featureform = buildfromauto(formconfig, base=featureform)
        else:
            raise NotImplemented('Other form types not supported yet')

        featureform.setObjectName("featureform")

        featureform.setWindowTitle(form.label)
        featureform.setContentsMargins(3, 0, 3, 9)
        formstyle = roam.roam_style.featureform
        formstyle += featureform.styleSheet()
        featureform.setStyleSheet(formstyle)

        featureform.createhelplinks()
        featureform.setProperty('featureform', featureform)

        featureform.setupui()
        featureform.uisetup()

        return featureform

    def toNone(self, value):
        """
        Convert the value to a None type if it is a QPyNullVariant, because noone likes that
        crappy QPyNullVariant type.

        :return: A None if the the value is a instance of QPyNullVariant. Returns the given value
                if not.
        """
        return nullcheck(value)

    def uisetup(self):
        """
        Called when the UI is fully constructed.  You should connect any signals here.
        """
        pass

    def load(self, feature, layers, values):
        """
        Called before the form is loaded. This method can be used to do pre checks and halt the loading of the form
        if needed.

        When implemented, this method should always return a tuple with a pass state and a message.

        Calling self.reject("Your message") will stop the opening of the form and show the message to the user.

            >>> self.cancelload("Sorry you can't load this form now")

        You may alter the QgsFeature given. It will be passed to the form after this method returns.
        """
        pass

    def featuresaved(self, feature, values):
        """
        Called when the feature is saved in QGIS.

        The values that are taken from the form as passed in too.
        :param feature:
        :param values:
        :return:
        """
        pass

    def deletefeature(self):
        """
        Return False if you do not wish to override the delete logic.
        Raise a DeleteFeatureException if you need to raise a error else
        roam will assume everything was fine.
        :return:
        """
        return False

    def featuredeleted(self, feature):
        pass


    def loaded(self):
        pass

    def accept(self):
        return True

    @property
    def gpsconnection(self):
        try:
            return QgsGPSConnectionRegistry.instance().connectionList()[0]
        except IndexError:
            return None

    def ongpsupdated(self, position, info):
        self.ongpsupdate(info)

    def ongpsupdate(self, info):
        """
        This method has been replaced with ongpsupdated. To handle GPS information in your form use
        it instead or listen to roam.api.GPS.gpspostion signal.
        """
        pass

    def cancelload(self, message=None, level=RejectedException.WARNING):
        raise RejectedException(message, level)

    def saveenabled(self, enabled):
        self.enablesave.emit(enabled)

    @property
    def allpassing(self):
        """
        Checks all widgets to see if they are in a pass state or not
        """
        for wrapper in self.boundwidgets.itervalues():
            # print wrapper.labeltext, wrapper.passing
            if not wrapper.passing:
                return False
        return True

    @property
    def missingfields(self):
        return [field for field, valid in self.requiredfields.iteritems() if valid == False]

    def save(self):
        """
        Save the values from the form into the set feature

        Override this method to handle saving things your own way if needed.
        """
        if not self.allpassing:
            raise MissingValuesException.missing_values()

        def updatefeautrefields(feature):
            def field_or_null(field):
                if field == '' or field is None or isinstance(field, QPyNullVariant):
                    return QPyNullVariant(str)
                return field

            for key, value in values.iteritems():
                try:
                    fields = [w['field'] for w in self.formconfig['widgets']]
                    if key in fields:
                        feature[key] = field_or_null(value)
                    else:
                        feature[key] = value
                except KeyError:
                    continue
            return feature

        def save_images(values):
            for field, wrapper in self.boundwidgets.iteritems():
                # HACK. Fix me. This is pretty messy
                if hasattr(wrapper, 'savetofile') and wrapper.savetofile and wrapper.modified:
                    filename = values[field]
                    folder = self.form.project.image_folder
                    saved = wrapper.save(folder, filename)
                    if not saved:
                        raise FeatureSaveException("Image Error",
                                                   "Could not save image for control {}".format(wrapper.label),
                                                   QgsMessageBar.CRITICAL)

        if not self.accept():
            raise FeatureSaveException.not_accepted()

        layer = self.form.QGISLayer
        values, savedvalues = self.getvalues()
        save_images(values)
        updatefeautrefields(self.feature)
        if self.editingmode:
            roam.utils.info("Updating feature {}".format(self.feature.id()))
            qgisutils.update_feature(layer, self.feature)
        else:
            roam.utils.info("Adding feature {}".format(self.feature.id()))
            saved = layer.dataProvider().addFeatures([self.feature])
            if not saved:
                raise FeatureSaveException.not_saved(layer.dataProvider().error().message())

            savevalues(layer, savedvalues)

        self.featuresaved(self.feature, values)

    def delete(self):
        """
        Delete the feature that is bound to this form from the forms layer
        Override this method to add your own delete logic
        """
        layer = self.form.QGISLayer
        userdeleted = self.deletefeature()

        if not userdeleted:
            # If the user didn't add there own feature delete logic
            # we will just do it for them.
            layer = self.form.QGISLayer
            featureid = self.feature.id()
            layer.startEditing()
            layer.deleteFeature(featureid)
            saved = layer.commitChanges()
            if not saved:
                errors = layer.commitErrors()
                raise DeleteFeatureException.not_saved(errors)

