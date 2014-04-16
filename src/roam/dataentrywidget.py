import functools
import os.path
import os
import getpass

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest, QgsFeature, QgsExpression, QGis, QgsGeometry
from qgis.gui import QgsMessageBar

from roam.utils import log, error
from roam.api import featureform
from roam.api import RoamEvents
from roam.ui.uifiles import dataentry_widget, dataentry_base
from roam.flickwidget import FlickCharm
from roam.popupdialogs import DeleteFeatureDialog
from roam.structs import CaseInsensitiveDict

def qgsfunction(args, group, **kwargs):
    """
    Decorator function used to define a user expression function.

    Custom functions should take (values, feature, parent) as args,
    they can also shortcut naming feature and parent args by using *args
    if they are not needed in the function.

    Functions should return a value compatible with QVariant

    Eval errors can be raised using parent.setEvalErrorString()

    Functions must be unregistered when no longer needed using
    QgsExpression.unregisterFunction

    Example:
      @qgsfunction(2, 'test'):
      def add(values, feature, parent):
        pass

      Will create and register a function in QgsExpression called 'add' in the
      'test' group that takes two arguments.

      or not using feature and parent:

      @qgsfunction(2, 'test'):
      def add(values, *args):
        pass
    """
    helptemplate = ''
    class QgsExpressionFunction(QgsExpression.Function):
        def __init__(self, name, args, group, helptext=''):
            QgsExpression.Function.__init__(self, name, args, group, helptext)

        def func(self, values, feature, parent):
            pass

    def wrapper(func):
        name = kwargs.get('name', func.__name__)
        help = func.__doc__ or ''
        help = help.strip()
        if args == 0 and not name[0] == '$':
            name = '${0}'.format(name)
        func.__name__ = name
        f = QgsExpressionFunction(name, args, group, '')
        f.func = func
        register = kwargs.get('register', True)
        if register:
            QgsExpression.registerFunction(f)
        return f
    return wrapper

capturegeometry = None

@qgsfunction(1, 'roam_geomvertex')
def roam_geomvertex(values, feature, parent):
    if capturegeometry:
        nodeindex = values[0]
        if capturegeometry.type() == QGis.Line:
            line = capturegeometry.asPolyline()
            try:
                node = line[nodeindex]
            except IndexError:
                return None
            node = QgsGeometry.fromPoint(node)
            return node
    return None

@qgsfunction(0, 'roamgeometry')
def _roamgeometry(values, feature, parent):
    return capturegeometry

class DefaultError(Exception):
    pass


def getdefaults(widgets, feature, layer, canvas):
    defaults = {}
    for field, config in widgets:
        default = config.get("default", None)
        if default is None:
            continue
        if isinstance(default, dict):
            defaultconfig = default
            try:
                defaulttype = defaultconfig['type']
                defaultprovider = defaultproviders[defaulttype]
                value = defaultprovider(feature, layer, field, defaultconfig, canvas)
            except KeyError as ex:
                log(ex)
                continue
            except DefaultError as ex:
                log(ex)
                value = None
        else:
            # Pass it though a series of filters to get the default value
            if '[%' in default and '%]' in default:
                # TODO Use regex
                default = QgsExpression.replaceExpressionText(default, feature, layer )
            value = os.path.expandvars(default)

        log("Default value: {}".format(value))
        defaults[field] = value

    defaults.update(featureform.loadsavedvalues(layer))
    return defaults

def layer_value(feature, layer, field, defaultconfig, canvas):
    layername = defaultconfig['layer']
    expression = defaultconfig['expression']
    field = defaultconfig['field']

    searchlayer = QgsMapLayerRegistry.instance().mapLayersByName(layername)[0]
    rect = feature.geometry().boundingBox()
    rect.scale(10)
    rect = canvas.mapRenderer().mapToLayerCoordinates(layer, rect)
    rq = QgsFeatureRequest().setFilterRect(rect)
    features = searchlayer.getFeatures(rq)
    global capturegeometry
    capturegeometry = feature.geometry()

    exp = QgsExpression(expression)
    exp.prepare(searchlayer.pendingFields())

    for f in features:
        if exp.evaluate(f):
            return f[field]

    raise DefaultError('No features found')

defaultproviders = {'spatial-query': layer_value,
                    'layer-value': layer_value}


class DataEntryWidget(dataentry_widget, dataentry_base):
    """
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal(str, int)
    finished = pyqtSignal()
    featuresaved = pyqtSignal()
    featuredeleted = pyqtSignal()
    failedsave = pyqtSignal(list)
    helprequest = pyqtSignal(str)
    openimage = pyqtSignal(object)

    def __init__(self, canvas, parent=None):
        super(DataEntryWidget, self).__init__(parent)
        self.setupUi(self)
        self.featureform = None
        self.feature = None
        self.fields = None
        self.project = None
        self.canvas = canvas

        self.flickwidget = FlickCharm()
        self.flickwidget.activateOn(self.scrollArea)

        toolbar = QToolBar()
        size = QSize(48, 48)
        toolbar.setIconSize(size)
        style = Qt.ToolButtonTextUnderIcon
        toolbar.setToolButtonStyle(style)
        self.actionSave.triggered.connect(self.accept)
        self.actionCancel.triggered.connect(functools.partial(self.formrejected, None))
        self.actionDelete.triggered.connect(self.deletefeature)

        label = 'Required fields marked in <b style="background-color:rgba(255, 221, 48,150)">yellow</b>'
        self.missingfieldsLabel = QLabel(label)
        self.missingfieldsLabel.hide()
        toolbar.addAction(self.actionDelete)
        self.missingfieldaction = toolbar.addWidget(self.missingfieldsLabel)
        spacer = QWidget()
        spacer2 = QWidget()
        spacer2.setMinimumWidth(20)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        toolbar.addWidget(spacer)
        toolbar.addAction(self.actionCancel)
        toolbar.addWidget(spacer2)
        toolbar.addAction(self.actionSave)

        self.data_entry_page.layout().insertWidget(0, toolbar)

    def deletefeature(self):
        msg = self.featureform.deletemessage
        box = DeleteFeatureDialog(msg, QApplication.activeWindow())

        if not box.exec_():
            return

        try:
            userdeleted = self.featureform.deletefeature()

            if not userdeleted:
                # If the user didn't add there own feature delete logic
                # we will just do it for them.
                layer = self.featureform.form.QGISLayer
                layer.startEditing()
                layer.deleteFeature(self.feature.id())
                saved = layer.commitChanges()
                if not saved:
                    raise featureform.DeleteFeatureException(layer.commitErrors())

        except featureform.DeleteFeatureException as ex:
            self.failedsave.emit([ex.message])
            map(error, ex.message)
            return

        self.featureform.featuredeleted(self.feature)
        self.featuredeleted.emit()

    def accept(self):
        def updatefeautrefields(feature):
            for key, value in values.iteritems():
                try:
                    feature[key] = value
                except KeyError:
                    continue
            return feature

        if not self.featureform.allpassing:
            RoamEvents.raisemessage("Missing fields", "Some fields are still required.",
                                     QgsMessageBar.WARNING, duration=2)
            return

        if not self.featureform:
            return

        if not self.featureform.accept():
            return

        layer = self.featureform.form.QGISLayer
        before = QgsFeature(self.feature)
        before.setFields(self.fields, initAttributes=False)

        values, savedvalues = self.featureform.getvalues()

        after = QgsFeature(self.feature)
        after.setFields(self.fields, initAttributes=False)
        after = updatefeautrefields(after)

        layer.startEditing()
        if after.id() > 0:
            if self.project.historyenabled(layer):
                # Mark the old one as history
                before['status'] = 'H'
                after['status'] = 'C'
                after['dateedited'] = QDateTime.currentDateTime()
                after['editedby'] = getpass.getuser()
                layer.addFeature(after)
                layer.updateFeature(before)
            else:
                layer.updateFeature(after)
        else:
            layer.addFeature(after)
            featureform.savevalues(layer, savedvalues)

        saved = layer.commitChanges()

        if not saved:
            self.failedsave.emit(layer.commitErrors())
            map(error, layer.commitErrors())
        else:
            self.featureform.featuresaved(after, values)
            self.featuresaved.emit()

        self.accepted.emit()
        self.featureform = None

    def formrejected(self, message=None, level=featureform.RejectedException.WARNING):
        self.clear()
        self.rejected.emit(message, level)

    def formvalidation(self, passed):
        self.missingfieldaction.setVisible(not passed)

    def setlargewidget(self, widgettype, lastvalue, callback):
        def cleanup():
            self.stackedWidget.setCurrentIndex(0)
            self.clearcurrentwidget(self.fullscreenwidget)
            del self.largewidgetwrapper

        widget = widgettype.createwidget()
        self.largewidgetwrapper = widgettype.for_widget(widget, None, None, None, None, map=self.canvas)
        self.largewidgetwrapper.finished.connect(callback)
        self.largewidgetwrapper.finished.connect(cleanup)
        self.largewidgetwrapper.cancel.connect(cleanup)

        self.clearcurrentwidget(self.fullscreenwidget)
        self.fullscreenwidget.layout().insertWidget(0, widget)
        self.stackedWidget.setCurrentIndex(1)

        self.largewidgetwrapper.initWidget(widget)
        self.largewidgetwrapper.setvalue(lastvalue)

    def setwidget(self, widget):
        self.clearcurrentwidget(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.layout().insertWidget(0, widget)
        self.stackedWidget.setCurrentIndex(0)

    def clear(self):
        self.featureform = None
        self.clearcurrentwidget(self.fullscreenwidget)
        self.clearcurrentwidget(self.scrollAreaWidgetContents)

    def clearcurrentwidget(self, parent):
        item = parent.layout().itemAt(0)
        if item and item.widget():
            widget = item.widget()
            widget.setParent(None)
            widget.deleteLater()

    def openform(self, form, feature, project):
        """
        Opens a form for the given feature.
        """

        defaults = {}
        editing = feature.id() >= 0
        layer = form.QGISLayer
        if not editing:
            defaults = getdefaults(form.widgetswithdefaults(), feature, layer, self.canvas)

        self.actionDelete.setVisible(editing)

        for field, value in defaults.iteritems():
            feature[field] = value

        self.formvalidation(passed=True)
        self.feature = feature
        # Hold a reference to the fields because QGIS will let the
        # go out of scope and we get crashes. Yay!
        self.fields = self.feature.fields()
        self.featureform = form.create_featureform(feature, defaults, canvas=self.canvas)
        self.featureform.rejected.connect(self.formrejected)
        self.featureform.enablesave.connect(self.actionSave.setEnabled)

        # Call the pre loading events for the form
        layers = QgsMapLayerRegistry.instance().mapLayers()

        self.project = project
        fields = [field.name().lower() for field in self.fields]
        attributes = feature.attributes()

        if layer.dataProvider().name() == 'spatialite':
            pkindexes = layer.dataProvider().pkAttributeIndexes()
            for index in pkindexes:
                del fields[index]
                del attributes[index]

        values = CaseInsensitiveDict(zip(fields, attributes))

        try:
            self.featureform.load(feature, layers, values)
        except featureform.RejectedException as rejected:
            self.formrejected(rejected.message, rejected.level)
            return

        self.featureform.formvalidation.connect(self.formvalidation)
        self.featureform.helprequest.connect(self.helprequest.emit)
        self.featureform.bindvalues(values)
        self.featureform.showlargewidget.connect(self.setlargewidget)

        self.actionSave.setVisible(True)
        self.setwidget(self.featureform)

        self.featureform.loaded()
