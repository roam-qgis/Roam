import functools
import os.path
import os
import getpass

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest, QgsFeature, QgsExpression

from roam.utils import log, info, warning, error
from roam import featureform
from roam.uifiles import dataentry_widget, dataentry_base
from roam.flickwidget import FlickCharm


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


def spatial_query(feature, layer, field, defaultconfig, canvas):
    layername = defaultconfig['layer']
    op = defaultconfig['op']
    field = defaultconfig['field']

    layer = QgsMapLayerRegistry.instance().mapLayersByName(layername)[0]
    if op == 'contains':
        rect = feature.geometry().boundingBox()
        rect = canvas.mapRenderer().mapToLayerCoordinates(layer, rect)
        rq = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
        features = layer.getFeatures(rq)
        for f in features:
            geometry = feature.geometry()
            if f.geometry().contains(geometry):
                return f[field]
        raise DefaultError('No features found')

defaultproviders = {'spatial-query': spatial_query}


class DataEntryWidget(dataentry_widget, dataentry_base):
    """
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal(str)
    finished = pyqtSignal()
    featuresaved = pyqtSignal()
    failedsave = pyqtSignal(list)
    helprequest = pyqtSignal(str)

    def __init__(self, canvas, parent=None):
        super(DataEntryWidget, self).__init__(parent)
        self.setupUi(self)
        self.featureform = None
        self.project = None
        self.canvas = canvas

        self.flickwidget = FlickCharm()
        self.flickwidget.activateOn(self.scrollArea)

        self.savedataButton.pressed.connect(self.accept)
        self.cancelButton.pressed.connect(functools.partial(self.reject, None))

    def accept(self):
        if not self.featureform:
            return

        if not self.featureform.accept():
            return

        layer = self.featureform.form.QGISLayer
        before, after, savedvalues = self.featureform.unbind()

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
            self.featuresaved.emit()

        self.accepted.emit()
        self.finished.emit()
        self.featureform = None

    def reject(self, message):
        # Tell the form it is rejected
        if self.featureform:
            self.featureform.reject(message)

    def formrejected(self, message=None):
        self.clearcurrentwidget()
        self.rejected.emit(message)
        self.finished.emit()
        self.featureform = None

    def formvalidation(self, passed):
        msg = None
        if not passed:
            msg = "Looks like some fields are missing. Check any fields marked in"
        self.missingfieldsLabel.setText(msg)
        self.savedataButton.setEnabled(passed)
        self.yellowLabel.setVisible(not passed)

    def showwidget(self, widget):
        self.savedataButton.hide()
        self.setwidget(widget)

    def setwidget(self, widget):
        print "SET WIDGET", widget
        self.clearcurrentwidget()
        self.scrollAreaWidgetContents.layout().insertWidget(0, widget)

    def clearcurrentwidget(self):
        item = self.scrollAreaWidgetContents.layout().itemAt(0)
        if item and item.widget():
            widget = item.widget()
            widget.deleteLater()

    def continueload(self):
        self.featureform.showwidget.disconnect()
        self.featureform.loadform.disconnect()

        self.featureform.formvalidation.connect(self.formvalidation)
        self.featureform.helprequest.connect(self.helprequest.emit)
        self.featureform.bind()

        self.savedataButton.show()
        self.setwidget(self.featureform.widget)

        self.featureform.loaded()

    def openform(self, form, feature, project):
        """
        Opens a form for the given feature.

        This method is connected using signals rather then a normal top down method.
        If the loadform signal is emitted from the FeatureForm
        the data entry widget will continue to bind and load the form.  If rejected is emitted
        the form will be rejected and the message will be shown to the user.

        This allows for pre form load checks that allow the form to show pre main form widgets
        using showwidget.
        """

        defaults = {}
        editing = feature.id() > 0
        if not editing:
            defaults = getdefaults(form.widgetswithdefaults(), feature, form.QGISLayer, self.canvas)

        for field, value in defaults.iteritems():
            feature[field] = value

        self.formvalidation(passed=True)
        self.feature = feature
        self.featureform = form.create_featureform(feature, defaults)
        self.featureform.showwidget.connect(self.showwidget)
        self.featureform.loadform.connect(self.continueload)
        self.featureform.rejected.connect(self.formrejected)

        # Call the pre loading evnts for the form
        layers = iter(QgsMapLayerRegistry.instance().mapLayers())

        self.project = project
        self.featureform.loading(feature, layers, editing)
