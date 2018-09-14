import os
import sys
import subprocess
import collections
import types
import tempfile
import json
import copy

from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, QObject, QSize, QEvent, QProcess, Qt, QPyNullVariant, QRegExp
from PyQt4.QtGui import (QWidget,
                        QAction,
                         QDialogButtonBox,
                         QStackedWidget,
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
                         QDoubleSpinBox,
                         QVBoxLayout,
                        QSizePolicy,
                        QTabWidget)

from qgis.core import QgsFields, QgsFeature, QgsGPSConnectionRegistry, QGis, QgsGeometry, QgsPoint
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
import roam.config

from roam.ui.ui_geomwidget import Ui_GeomWidget

values_file = os.path.join(tempfile.gettempdir(), "Roam")

nullcheck = qgisutils.nullcheck

import contextlib
import time

totals = collections.defaultdict(int)

@contextlib.contextmanager
def timed(title):
    ts = time.time()
    yield
    th = time.time()
    took = th - ts
    totals[title] += took
    message = "{} {}".format(title, took)
    print message


class GeomWidget(Ui_GeomWidget, QStackedWidget):
    def __init__(self, parent=None):
        super(GeomWidget, self).__init__(parent)
        self.setupUi(self)
        self.geom = None
        self.edited = False

    def set_geometry(self, geom):
        if not geom:
            return

        self.geom = geom
        if self.geom.type() == QGis.Point:
            self.setCurrentIndex(0)
            point = geom.asPoint()
            self.xedit.setText(str(point.x()))
            self.yedit.setText(str(point.y()))
            self.xedit.textChanged.connect(self.mark_edited)
            self.yedit.textChanged.connect(self.mark_edited)
        else:
            self.setCurrentIndex(1)

    def geometry(self):
        if self.geom.type() == QGis.Point:
            x = float(self.xedit.text())
            y = float(self.yedit.text())
            return QgsGeometry.fromPoint(QgsPoint(x, y))

    def mark_edited(self):
        self.edited = True


def loadsavedvalues(form):
    attr = {}
    savedvaluesfile = os.path.join(values_file, "{}.json".format(form.savekey))
    try:
        utils.log(savedvaluesfile)
        with open(savedvaluesfile, 'r') as f:
            attr = json.loads(f.read())
    except IOError:
        utils.log('No saved values found for %s' % id)
    except ValueError:
        utils.log('No saved values found for %s' % id)
    return attr


def savevalues(form, values):
    savedvaluesfile = os.path.join(values_file, "{}.json".format(form.savekey))
    folder = os.path.dirname(savedvaluesfile)
    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(savedvaluesfile, 'w') as f:
        json.dump(values, f)


def buildfromui(uifile, base):
    widget = uic.loadUi(uifile, base)
    return installflickcharm(widget)


def buildfromauto(formconfig, base):
    widgetsconfig = copy.deepcopy(formconfig['widgets'])

    try:
        widgetsconfig = base.get_widgets(widgetsconfig)
    except AttributeError:
        pass

    newstyle = formconfig.get("newstyle", False)
    hassections = any(config['widget'] == "Section" for config in widgetsconfig)

    def make_layout():
        if newstyle:
            return QVBoxLayout()
        else:
            layout = QFormLayout()
            layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
            return layout

    def make_tab(tabwidget, name):
        widget = QWidget()
        widget.setLayout(make_layout())
        tabwidget.addTab(widget, name)
        return widget, widget.layout()

    if hassections:
        outwidget = QTabWidget(base)
        outlayout = None
        base.setLayout(QVBoxLayout())
        base.layout().setContentsMargins(0,0,0,0)
        base.layout().addWidget(outwidget)
    else:
        outwidget = base
        outlayout = make_layout()
        outwidget.setLayout(outlayout)

    if roam.config.settings.get("form_geom_edit", False):
        geomwidget = GeomWidget()
        geomwidget.setObjectName("__geomwidget")
        outlayout.addRow("Geometry", geomwidget)

    insection = False
    for config in widgetsconfig:
        widgettype = config['widget']

        ## Make the first tab if one isn't defined already and we have other sections in the config
        if not insection and hassections and not widgettype == "Section":
            name = formconfig['label']
            tabwidget, outlayout = make_tab(outwidget, name)
            insection = True

        if widgettype == 'Section':
            # Add a spacer to the last widget
            if outlayout:
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
                outlayout.addItem(QSpacerItem(10, 500))
                outlayout.addWidget(spacer)

            name = config['name']
            tabwidget, outlayout = make_tab(outwidget, name)
            installflickcharm(tabwidget)
            insection = True
            continue

        field = config['field']
        name = config.get('name', field)
        if not field:
            utils.warning("Field can't be null for {}".format(name))
            utils.warning("Skipping widget")
            continue

        label = QLabel(name)
        label.setObjectName(field + "_label")
        labelwidget = QWidget()
        labelwidget.setLayout(QBoxLayout(QBoxLayout.LeftToRight))
        labelwidget.layout().addWidget(label)
        labelwidget.layout().setContentsMargins(0,0,0,0)

        widget = roam.editorwidgets.core.createwidget(widgettype, parent=base)
        widget.setObjectName(field)
        layoutwidget = QWidget()
        layoutwidget.setLayout(QBoxLayout(QBoxLayout.LeftToRight))
        layoutwidget.layout().addWidget(widget)
        layoutwidget.layout().setContentsMargins(0,0,0,10)

        if config.get('rememberlastvalue', False):
            savebutton = QToolButton()
            savebutton.setObjectName('{}_save'.format(field))
            if newstyle:
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                labelwidget.layout().addWidget(spacer)
                labelwidget.layout().addWidget(savebutton)
            else:
                layoutwidget.layout().addWidget(savebutton)

        if newstyle:
            outlayout.addWidget(labelwidget)
            outlayout.addWidget(layoutwidget)
        else:
            outlayout.addRow(labelwidget, layoutwidget)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    outlayout.addWidget(spacer)
    if not hassections:
        outlayout.addItem(QSpacerItem(10, 500))
        installflickcharm(outwidget)
    return base


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
    accepted = pyqtSignal()
    enablesave = pyqtSignal(bool)
    showlargewidget = pyqtSignal(object, object, object, dict)

    def __init__(self, form, formconfig, feature, defaults, parent, *args, **kwargs):
        super(FeatureFormBase, self).__init__(parent)
        self.form = form
        self.formconfig = formconfig
        self.boundwidgets = CaseInsensitiveDict()
        self.requiredfields = CaseInsensitiveDict()
        self.feature = feature
        self.geomwidget = None
        self.defaults = defaults
        self.bindingvalues = CaseInsensitiveDict()
        self.editingmode = kwargs.get("editmode", False)
        self.widgetidlookup = {}
        self._has_save_buttons = False
        self.star_all_button = QAction(QIcon(":/icons/save_default_all"), "Star All", self, triggered=self.star_all)

    def open_large_widget(self, widgettype, lastvalue, callback, config=None):
        self.showlargewidget.emit(widgettype, lastvalue, callback, config)

    def form_actions(self):
        builtin = []
        if self._has_save_buttons:
            builtin.append(self.star_all_button)
        useractions = self.user_form_actions()
        if not useractions:
            useractions = []
        return builtin + useractions

    def star_all(self):
        """
        Star or unstar all buttons on the form.
        :param star_all: True to star all buttons on the form.
        """
        checked = self.star_all_button.text() == "Star All"
        buttons = self._field_save_buttons()
        for button in buttons:
            button.setChecked(checked)

        if checked:
            self.star_all_button.setText("Star None")
        else:
            self.star_all_button.setText("Star All")

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
        self.geomwidget = self.findcontrol("__geomwidget")

        widgetsconfig = copy.deepcopy(self.formconfig['widgets'])

        try:
            widgetsconfig = self.get_widgets(widgetsconfig)
        except AttributeError:
            pass

        layer = self.form.QGISLayer
        # Crash in QGIS if you lookup a field that isn't found.
        # We just make a dict with all fields lower because QgsFields is case sensitive.
        fields = {field.name().lower():field for field in layer.pendingFields().toList()}

        # Build a lookup for events
        self.events = collections.defaultdict(list)
        for event in self.form.events:
            self.events[event['source']].append(event)

        widgetsconfig = copy.deepcopy(widgetsconfig)
        self.sectionwidgets = {}

        currentsection = None
        for config in widgetsconfig:
            widgettype = config['widget']
            if widgettype == "Section":
                name = config['name']
                currentsection = name
                self.sectionwidgets[name] = []
                continue

            field = config['field']
            if not field:
                utils.info("Skipping widget. No field defined")
                continue

            field = field.lower()

            if field in self.boundwidgets:
                utils.warning("Can't bind the same field ({}) twice.".format(field))
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
            widgetconfig['formwidget'] = self
            try:
                qgsfield = fields[field]
            except KeyError:
                utils.log("No field for ({}) found".format(field))

            context = dict(project=self.form.project,
                           form=self.form,
                           featureform=self)
            try:
                widgetwrapper = roam.editorwidgets.core.widgetwrapper(widgettype=widgettype,
                                                                      layer=self.form.QGISLayer,
                                                                      field=qgsfield,
                                                                      widget=widget,
                                                                      label=label,
                                                                      config=widgetconfig,
                                                                      context=context)
            except EditorWidgetException as ex:
                utils.exception(ex)
                continue

            widgetwrapper.default_events = config.get('default_events', ['capture'])
            readonlyrules = config.get('read-only-rules', [])

            if self.editingmode and 'editing' in readonlyrules:
                widgetwrapper.readonly = True
            elif 'insert' in readonlyrules or 'always' in readonlyrules:
                widgetwrapper.readonly = True

            widgetwrapper.hidden = config.get('hidden', False)

            widgetwrapper.newstyleform = self.formconfig.get("newstyle", False)
            widgetwrapper.required = config.get('required', False)
            widgetwrapper.id = config.get('_id', '')

            # Only connect widgets that have events
            if widgetwrapper.id in self.events:
                widgetwrapper.valuechanged.connect(partial(self.check_for_update_events, widgetwrapper))

            widgetwrapper.valuechanged.connect(self.updaterequired)

            try:
                changedslot = getattr(self, "widget_{}_changed".format(field))
                widgetwrapper.valuechanged.connect(changedslot)
            except AttributeError:
                pass

            widgetwrapper.largewidgetrequest.connect(RoamEvents.show_widget.emit)

            self._bindsavebutton(field)
            self.boundwidgets[field] = widgetwrapper
            try:
                self.widgetidlookup[config['_id']] = widgetwrapper
            except KeyError:
                pass

            if currentsection:
                self.sectionwidgets[currentsection].append(widgetwrapper)

    def widgets_for_section(self, name):
        try:
            return self.sectionwidgets[name]
        except KeyError:
            return []

    def get_widget_from_id(self, id):
        try:
            return self.widgetidlookup[id]
        except KeyError:
            return None

    def check_for_update_events(self, widget, value):
        if not self.feature:
            return

        from qgis.core import QgsExpression, QgsExpressionContext, QgsExpressionContextScope
        # If we don't have any events for this widgets just get out now
        if not widget.id in self.events:
            return

        events = self.events[widget.id]
        events = [event for event in events if event['event'].lower() == 'update']
        if not events:
            return

        feature = self.to_feature(no_defaults=True)

        for event in events:
            action = event['action'].lower()
            targetid = event['target']
            if targetid == widget.id:
                utils.log("Can't connect events to the same widget. ID {}".format(targetid))
                continue

            widget = self.get_widget_from_id(targetid)

            if not widget:
                utils.log("Can't find widget for id {} in form".format(targetid))
                continue

            condition = event['condition']
            expression = event['value']

            context = QgsExpressionContext()
            scope = QgsExpressionContextScope()
            scope.setVariable("value", value)
            scope.setVariable("field", widget.field)
            context.setFeature(feature)
            context.appendScope(scope)

            conditionexp = QgsExpression(condition)
            exp = QgsExpression(expression)

            if action.lower() == "show":
                widget.hidden = not conditionexp.evaluate(context)
            if action.lower() == "hide":
                widget.hidden = conditionexp.evaluate(context)
            if action == 'widget expression':
                if conditionexp.evaluate(context):
                    newvalue = self.widget_default(field, feature=feature)
                    widget.setvalue(newvalue)
            if action == 'set value':
                if conditionexp.evaluate(context):
                    newvalue = exp.evaluate(context)
                    widget.setvalue(newvalue)

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
        if self.geomwidget and self.feature:
            self.geomwidget.set_geometry(self.feature.geometry())

    def bind_feature(self, feature):
        self.feature = feature
        values = self.form.values_from_feature(feature)
        self.bindvalues(values)

    def getvalues(self, no_defaults=False):
        def shouldsave(field):
            name = "{}_save".format(field)
            button = self.findcontrol(name)
            if not button is None:
                return button.isChecked()

        savedvalues = {}
        values = CaseInsensitiveDict(self.bindingvalues)
        for field, wrapper in self.boundwidgets.iteritems():
            if not no_defaults and wrapper.get_default_value_on_save:
                value = self.widget_default(field)
            else:
                value = wrapper.value()
                extradata = wrapper.extraData()
                values.update(extradata)

            # TODO this should put pulled out and unit tested. MOVE ME!
            # NOTE: This is photo widget stuff and really really doesn't belong here.
            if hasattr(wrapper, 'savetofile') and wrapper.savetofile and wrapper.saveable:
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

    def findcontrol(self, name, all=False):
        regex = QRegExp("^{}$".format(QRegExp.escape(name)))
        regex.setCaseSensitivity(Qt.CaseInsensitive)
        try:
            if all:
                return self.findChildren(QWidget, regex)
            else:
                widget = self.findChildren(QWidget, regex)[0]
        except IndexError:
            widget = None
        return widget

    def _field_save_buttons(self):
        """
        Return all the save buttons for the form.
        :return:
        """
        for field in self.boundwidgets.keys():
            name = "{}_save".format(field)
            savebutton = self.findcontrol(name)
            if savebutton:
                yield savebutton

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
        self._has_save_buttons = True

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

    def widget_default(self, name, feature=None):
        """
        Return the default value for the given widget
        """
        try:
            widgetconfig = self.form.widget_by_field(name)
        except IndexError:
            raise KeyError("Widget with name {} not found on form".format(name))

        if not 'default' in widgetconfig:
            raise KeyError('Default value not defined for this field {}'.format(name))

        if not feature:
            feature = self.feature

        return defaults.widget_default(widgetconfig, feature, self.form.QGISLayer)

    def close_form(self, reason=None, level=1):
        self.rejected.emit(reason, level)

    def to_feature(self, no_defaults=False):
        """
        Create a QgsFeature from the current form values
        """
        if not self.feature:
            return

        feature = QgsFeature(self.feature.fields())
        feature.setGeometry(QgsGeometry(self.feature.geometry()))
        try:
            values, _ = self.getvalues(no_defaults=no_defaults)
        except TypeError:
            values, _ = self.getvalues()

        self.updatefeautrefields(feature, values)
        self.update_geometry(feature)
        return feature


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
        formstyle = roam.roam_style.featureform()
        formstyle += featureform.styleSheet()
        featureform.setStyleSheet(formstyle)

        featureform.createhelplinks()
        featureform.setProperty('featureform', featureform)

        featureform.setupui()
        featureform.uisetup()

        return featureform

    def user_form_actions(self):
        """
        Override and return a list of QActions to provide custom actions for the form UI.
        :return: None or a list-of-QActions
        """
        return None

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
    def incompletewidgets(self):
        return [w.labeltext for w in self.boundwidgets.itervalues() if not w.passing]

    @property
    def missingfields(self):
        return [field for field, valid in self.requiredfields.iteritems() if valid == False]

    def updatefeautrefields(self, feature, values):
        def field_or_null(v):
            if v == '' \
                    or v is None \
                    or isinstance(v, QPyNullVariant):
                return QPyNullVariant(str)
            return v

        for key, value in values.iteritems():
            try:
                feature[key] = field_or_null(value)
            except KeyError:
                continue

        return feature

    def save(self, ignore_required=False):
        """
        Save the values from the form into the set feature

        Override this method to handle saving things your own way if needed.
        """
        if not self.allpassing and not ignore_required:
            raise MissingValuesException.missing_values(self.incompletewidgets)

        def save_images(values):
            for field, wrapper in self.boundwidgets.iteritems():
                # HACK. Fix me. This is pretty messy
                if hasattr(wrapper, 'savetofile') and wrapper.savetofile and wrapper.modified:
                    filename = values[field]
                    folder = self.form.project.image_folder
                    if not wrapper.saveable:
                        continue

                    saved = wrapper.save(folder, filename)
                    if not saved:
                        raise FeatureSaveException("Image Error",
                                                   "Could not save image for control {}".format(wrapper.label),
                                                   QgsMessageBar.CRITICAL)
                elif type(wrapper).__name__ == "MultiImageWidget" and wrapper.modified:
                    ## This is a bit of a heck checking the widget name like this
                    ## but this whole thing needs to be refactored out anyway.
                    saved = wrapper.save()
                    if not saved:
                        raise FeatureSaveException("Widget Save Error",
                                                   "Could not save images for control {}".format(wrapper.label),
                                                   QgsMessageBar.CRITICAL)
        if not self.accept():
            raise FeatureSaveException.not_accepted()

        layer = self.form.QGISLayer
        values, savedvalues = self.getvalues()
        save_images(values)
        self.updatefeautrefields(self.feature, values)
        self.update_geometry(self.feature)
        layer.startEditing()
        if self.editingmode:
            roam.utils.info("Updating feature {}".format(self.feature.id()))
            layer.updateFeature(self.feature)
            # qgisutils.update_feature(layer, self.feature)
        else:
            roam.utils.info("Adding feature {}".format(self.feature.id()))
            layer.addFeature(self.feature)
            savevalues(self.form, savedvalues)

        saved = layer.commitChanges()

        if not saved:
            errors = layer.commitErrors()
            raise FeatureSaveException.not_saved(errors)

        feature = QgsFeature(self.feature)
        form = self.form
        RoamEvents.formSaved.emit(form, feature)

        self.featuresaved(self.feature, values)
        self.accepted.emit()


    def update_geometry(self, feature):
        if self.geomwidget and self.geomwidget.edited:
            geometry = self.geomwidget.geometry()
            feature.setGeometry(geometry)
        return feature

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



