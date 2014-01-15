import functools
import os.path
import os
import getpass

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest, QgsFeature, QgsExpression
from qgis.gui import QgsMessageBar

from roam.utils import log, info, warning, error
from roam import featureform
from roam.uifiles import dataentry_widget, dataentry_base
from roam.flickwidget import FlickCharm
from roam import featureform
from roam.deletefeaturedialog import DeleteFeatureDialog


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
    def within(geom, geom2):
        return geom.within(geom2)

    def contains(geom, geom2):
        return geom2.contains(geom)

    layername = defaultconfig['layer']
    op = defaultconfig['op']
    field = defaultconfig['field']

    ops = {'within': within,
           'contains': contains}

    layer = QgsMapLayerRegistry.instance().mapLayersByName(layername)[0]
    func = ops[op]
    rect = feature.geometry().boundingBox()
    rect = canvas.mapRenderer().mapToLayerCoordinates(layer, rect)
    rq = QgsFeatureRequest().setFilterRect(rect)
    features = layer.getFeatures(rq)
    geometry = feature.geometry()
    for f in features:
        if func(geometry, f.geometry()):
            return f[field]
    raise DefaultError('No features found')

defaultproviders = {'spatial-query': spatial_query}


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

    def __init__(self, canvas, bar, parent=None):
        super(DataEntryWidget, self).__init__(parent)
        self.setupUi(self)
        self.featureform = None
        self.feature = None
        self.project = None
        self.canvas = canvas
        self.bar = bar

        self.flickwidget = FlickCharm()
        self.flickwidget.activateOn(self.scrollArea)

        toolbar = QToolBar()
        size = QSize(32, 32)
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
        self.layout().insertWidget(2, toolbar)

    def deletefeature(self):
        box = DeleteFeatureDialog(QApplication.activeWindow())

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
        if not self.featureform.allpassing:
            self.bar.pushMessage("Missing fields", "Some fields are still required.",
                                 QgsMessageBar.WARNING, duration=2)
            return

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
            self.featureform.featuresaved(after)
            self.featuresaved.emit()

        self.accepted.emit()
        self.featureform = None

    def formrejected(self, message=None, level=featureform.RejectedException.WARNING):
        self.clear()
        self.rejected.emit(message, level)

    def formvalidation(self, passed):
        self.missingfieldaction.setVisible(not passed)

    def setwidget(self, widget):
        self.clearcurrentwidget()
        self.scrollAreaWidgetContents.layout().insertWidget(0, widget)

    def clear(self):
        self.featureform = None
        self.clearcurrentwidget()

    def clearcurrentwidget(self):
        item = self.scrollAreaWidgetContents.layout().itemAt(0)
        if item and item.widget():
            widget = item.widget()
            widget.setParent(None)
            widget.deleteLater()

    def openform(self, form, feature, project):
        """
        Opens a form for the given feature.
        """

        defaults = {}
        editing = feature.id() > 0
        if not editing:
            defaults = getdefaults(form.widgetswithdefaults(), feature, form.QGISLayer, self.canvas)

        self.actionDelete.setVisible(editing)

        for field, value in defaults.iteritems():
            feature[field] = value

        self.formvalidation(passed=True)
        self.feature = feature
        self.featureform = form.create_featureform(feature, defaults)
        self.featureform.rejected.connect(self.formrejected)

        # Call the pre loading events for the form
        layers = iter(QgsMapLayerRegistry.instance().mapLayers())

        self.project = project
        try:
            self.featureform.load(feature, layers, editing)
        except featureform.RejectedException as rejected:
            self.formrejected(rejected.message, rejected.level)
            return

        self.featureform.formvalidation.connect(self.formvalidation)
        self.featureform.helprequest.connect(self.helprequest.emit)
        self.featureform.bind()

        self.actionSave.setVisible(True)
        self.setwidget(self.featureform)

        self.featureform.loaded()
