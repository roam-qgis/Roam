import functools
import os.path
import os
import getpass

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest, QgsFeature, QgsExpression, QGis, QgsGeometry
from qgis.gui import QgsMessageBar

from roam.editorwidgets.core import LargeEditorWidget
from roam.utils import log, error
from roam.api import featureform, RoamEvents
from roam.ui.uifiles import dataentry_widget, dataentry_base
from roam.flickwidget import FlickCharm
from roam.popupdialogs import DeleteFeatureDialog
from roam.structs import CaseInsensitiveDict

import roam.qgisfunctions
import roam.defaults as defaults
import roam.editorwidgets.core

from roam.ui.ui_featureformwidget import Ui_Form

class FeatureFormWidget(Ui_Form, QWidget):
    # Raise the cancel event, takes a reason and a level
    cancel = pyqtSignal(str, int)
    featuresaved = pyqtSignal()

    def __init__(self, parent=None):
        super(FeatureFormWidget, self).__init__(parent)
        self.setupUi(self)

        toolbar = QToolBar()
        size = QSize(48, 48)
        toolbar.setIconSize(size)
        style = Qt.ToolButtonTextUnderIcon
        toolbar.setToolButtonStyle(style)
        self.actionDelete = toolbar.addAction("Delete")
        self.actionDelete.triggered.connect(self.delete_feature)

        label = 'Required fields marked in <b style="background-color:rgba(255, 221, 48,150)">yellow</b>'
        self.missingfieldsLabel = QLabel(label)
        self.missingfieldsLabel.hide()
        self.missingfieldaction = toolbar.addWidget(self.missingfieldsLabel)

        spacer = QWidget()
        spacer2 = QWidget()
        spacer2.setMinimumWidth(20)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        toolbar.addWidget(spacer)
        self.actionCancel = toolbar.addAction("Cancel")
        toolbar.addWidget(spacer2)
        self.actionSave = toolbar.addAction("Save")
        self.actionSave.triggered.connect(self.save_feature)

        self.layout().insertWidget(0, toolbar)

        self.flickwidget = FlickCharm()
        self.flickwidget.activateOn(self.scrollArea)

        self.featureform = None
        self.values = {}
        self.config = {}

    def set_featureform(self, featureform):
        """
        Note: There can only be one feature form.  If you need to show another one make a new FeatureFormWidget
        """
        self.featureform = featureform
        self.featureform.formvalidation.connect(self._update_validation)
        #self.featureform.helprequest.connect(self.helprequest.emit)
        #self.featureform.showlargewidget.connect(self.setlargewidget)
        self.featureform.enablesave.connect(self.actionSave.setEnabled)
        self.featureform.rejected.connect(self.cancel.emit)

        self.scrollAreaWidgetContents.layout().addWidget(self.featureform)

    def delete_feature(self):
        raise NotImplementedError

    def save_feature(self):
        raise NotImplementedError

    def set_config(self, config):
        self.config = config
        editmode = config['editmode']
        allowsave = config.get('allowsave', True)
        self.featureform.editingmode = editmode
        self.actionDelete.setVisible(editmode)
        self.actionSave.setEnabled(allowsave)

    def _update_validation(self, passed):
        # Show the error if there is missing fields
        self.missingfieldaction.setVisible(not passed)

    def bind_values(self, values):
        self.values = values
        self.featureform.bindvalues(values)
        self.featureform.loaded()

    def before_load(self):
        self.featureform.load(self.config['feature'], self.config['layers'], self.values)

class FeatureFormWidgetEditor(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(FeatureFormWidgetEditor, self).__init__(*args, **kwargs)

    def createWidget(self, parent=None):
        config = self.initconfig
        form = config['form']
        canvas = config.get('canvas', None)
        formwidget = FeatureFormWidget()
        featureform = form.create_featureform(None, defaults={}, canvas=canvas)
        formwidget.set_featureform(featureform)
        self.featureform = featureform
        return formwidget

    def initWidget(self, widget):
        widget.actionCancel.triggered.connect(self.cancelform)
        widget.featuresaved.connect(self.emitfished)

    def cancelform(self):
        self.emitcancel()

    def updatefromconfig(self):
        self.widget.set_config(self.config)

    def before_load(self):
        self.widget.before_load()

    def value(self):
        values, savedvalues = self.featureform.getvalues()
        return values

    def setvalue(self, value):
        self.widget.bind_values(value)


class DataEntryWidget(dataentry_widget, dataentry_base):
    """
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal(str, int)
    finished = pyqtSignal()
    featuresaved = pyqtSignal()
    featuredeleted = pyqtSignal(object, object)
    failedsave = pyqtSignal(list)
    helprequest = pyqtSignal(str)
    openimage = pyqtSignal(object)
    lastwidgetremoved = pyqtSignal()

    def __init__(self, canvas, parent=None):
        super(DataEntryWidget, self).__init__(parent)
        self.setupUi(self)
        self.featureform = None
        self.feature = None
        self.fields = None
        self.project = None
        self.canvas = canvas
        self.widgetstack = []


    def deletefeature(self):
        # TODO ALl this needs to live in the feature form.
        try:
            msg = self.featureform.deletemessage
        except AttributeError:
            msg = 'Do you really want to delete this feature?'
        box = DeleteFeatureDialog(msg, QApplication.activeWindow())

        if not box.exec_():
            return

        featureid = self.feature.id()
        try:
            userdeleted = self.featureform.deletefeature()

            if not userdeleted:
                # If the user didn't add there own feature delete logic
                # we will just do it for them.
                layer = self.featureform.form.QGISLayer
                layer.startEditing()
                layer.deleteFeature(featureid)
                saved = layer.commitChanges()
                if not saved:
                    raise featureform.DeleteFeatureException(layer.commitErrors())

        except featureform.DeleteFeatureException as ex:
            self.failedsave.emit([ex.message])
            map(error, ex.message)
            return

        self.featureform.featuredeleted(self.feature)
        self.featuredeleted.emit(self.featureform.form.QGISLayer, featureid)

    def accept(self):
        # TODO ALl this needs to live in the feature form.
        fields = [w['field'] for w in self.featureform.formconfig['widgets']]

        def updatefeautrefields(feature):
            for key, value in values.iteritems():
                try:
                    if key in fields:
                        feature[key] = field_or_null(value)
                    else:
                        feature[key] = value
                except KeyError:
                    continue
            return feature

        def field_or_null(field):
            if field == '' or field is None or isinstance(field, QPyNullVariant):
                return QPyNullVariant(str)
            return field

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
        self.rejected.emit(message, level)

    def setlargewidget(self, widgettype, lastvalue, callback, config, initconfig=None):
        def cleanup():
            # Pop the widget off the current widget stack and kill it.
            wrapper, position = self.widgetstack.pop()
            print "Clean up"
            self.clearwidget(position)

        widget = widgettype.createwidget(config=initconfig)
        largewidgetwrapper = widgettype.for_widget(widget, None, None, None, None, map=self.canvas)
        largewidgetwrapper.largewidgetrequest.connect(self.setlargewidget)
        largewidgetwrapper.finished.connect(callback)
        largewidgetwrapper.finished.connect(cleanup)
        largewidgetwrapper.cancel.connect(cleanup)

        largewidgetwrapper.initWidget(widget)
        largewidgetwrapper.config = config
        largewidgetwrapper.setvalue(lastvalue)

        try:
            largewidgetwrapper.before_load()
            position = self.stackedWidget.addWidget(widget)
            self.stackedWidget.setCurrentIndex(position)
            self.widgetstack.append((largewidgetwrapper, position))
        except roam.editorwidgets.core.RejectedException as rejected:
            self.formrejected(rejected.message, rejected.level)

    def clear(self):
        for i in xrange(self.stackedWidget.count()):
            self.clearwidget(i)

    def clearwidget(self, position=0):
        widget = self.stackedWidget.widget(position)
        self.stackedWidget.removeWidget(widget)
        if widget:
            widget.deleteLater()

        if self.stackedWidget.count() == 0:
            self.lastwidgetremoved.emit()

    def save_feature(self, values):
        print values

    def openform(self, form, feature, project, editmode):
        """
        Opens a form for the given feature.
        """

        # One capture geometry, even for sub forms?
        # HACK Remove me and do something smarter
        roam.qgisfunctions.capturegeometry = feature.geometry()

        # Hold a reference to the fields because QGIS will let the
        # go out of scope and we get crashes. Yay!
        layer = form.QGISLayer
        self.fields = feature.fields()
        attributes = feature.attributes()

        fields = [field.name().lower() for field in self.fields]
        # Something is strange with default values and spatilite. Just delete them for now.
        if layer.dataProvider().name() == 'spatialite':
            pkindexes = layer.dataProvider().pkAttributeIndexes()
            for index in pkindexes:
                del fields[index]
                del attributes[index]
        values = CaseInsensitiveDict(zip(fields, attributes))

        defaultvalues = {}
        if not editmode:
            defaultwidgets = form.widgetswithdefaults()
            defaultvalues = defaults.default_values(defaultwidgets, feature, layer)
            defaultvalues.update(featureform.loadsavedvalues(layer))

        values.update(defaultvalues)

        initconfig = dict(form=form,
                          canvas=self.canvas)
        config = dict(editmode=editmode,
                      layers=QgsMapLayerRegistry.instance().mapLayers(),
                      feature=feature)

        self.setlargewidget(FeatureFormWidgetEditor, values, self.save_feature, config, initconfig=initconfig)
