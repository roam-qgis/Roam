import os.path
import os
import getpass

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest, QgsFeature, QgsExpression

from roam.utils import log, info, warning, error
from roam import featuredialog
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

    defaults.update(featuredialog.loadsavedvalues(layer))
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
    rejected = pyqtSignal()
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
        self.cancelButton.pressed.connect(self.reject)

    def accept(self):
        assert not self.featureform is None
        assert not self.project is None

        if not self.featureform.accept():
            return

        layer = self.featureform.form.QGISLayer
        before, after, savedvalues = self.featureform.getupdatedfeature()

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
            featuredialog.savevalues(layer, savedvalues)
        saved = layer.commitChanges()

        if not saved:
            self.failedsave.emit(layer.commitErrors())
            map(error, layer.commitErrors())
        else:
            self.featuresaved.emit()

        self.accepted.emit()
        self.finished.emit()

    def reject(self):
        assert not self.featureform is None

        if not self.featureform.reject():
            return

        self.featureform.form.QGISLayer.rollBack()
        self.clearcurrentwidget()
        self.rejected.emit()
        self.finished.emit()

    def formvalidation(self, passed):
        msg = None
        if not passed:
            msg = "Looks like some fields are missing. Check any fields marked in"
        self.missingfieldsLabel.setText(msg)
        self.savedataButton.setEnabled(passed)
        self.yellowLabel.setVisible(not passed)

    def setwidget(self, widget):
        self.clearcurrentwidget()
        self.scrollAreaWidgetContents.layout().insertWidget(0, widget)

    def clearcurrentwidget(self):
        item = self.scrollAreaWidgetContents.layout().itemAt(0)
        if item and item.widget():
            item.widget().setParent(None)

    def openform(self, form, feature, project):
        """
        Opens a form for the given feature
        """
        defaults = {}
        editing = feature.id() > 0
        if not editing:
            defaults = getdefaults(form.widgetswithdefaults(), feature, form.QGISLayer, self.canvas)

        for field, value in defaults.iteritems():
            feature[field] = value

        # Call the pre loading evnts for the form
        layers = iter(QgsMapLayerRegistry.instance().mapLayers())
        state, message = form.onformloading(form, feature, layers, editing)

        if not state:
            return state, message

        self.project = project
        self.featureform = form.featureform
        self.featureform.formvalidation.connect(self.formvalidation)
        self.featureform.helprequest.connect(self.helprequest.emit)
        self.featureform.bindfeature(feature, defaults)

        self.setwidget(self.featureform.widget)

        return True, None
