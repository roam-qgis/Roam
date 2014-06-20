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
    featuredeleted = pyqtSignal()

    def __init__(self, parent=None):
        super(FeatureFormWidget, self).__init__(parent)
        self.setupUi(self)

        toolbar = QToolBar()
        size = QSize(48, 48)
        toolbar.setIconSize(size)
        style = Qt.ToolButtonTextUnderIcon
        toolbar.setToolButtonStyle(style)
        self.actionDelete = toolbar.addAction(QIcon(":/icons/delete"), "Delete")
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
        self.actionCancel = toolbar.addAction(QIcon(":/icons/cancel"), "Cancel")
        toolbar.addWidget(spacer2)
        self.actionSave = toolbar.addAction(QIcon(":/icons/save"), "Save")
        self.actionSave.triggered.connect(self.save_feature)

        self.layout().insertWidget(0, toolbar)

        self.flickwidget = FlickCharm()
        self.flickwidget.activateOn(self.scrollArea)

        self.featureform = None
        self.values = {}
        self.config = {}
        self.feature = None

    def set_featureform(self, featureform):
        """
        Note: There can only be one feature form.  If you need to show another one make a new FeatureFormWidget
        """
        self.featureform = featureform
        self.featureform.formvalidation.connect(self._update_validation)
        self.featureform.helprequest.connect(functools.partial(RoamEvents.helprequest.emit, self))
        self.featureform.showlargewidget.connect(RoamEvents.show_widget.emit)
        self.featureform.enablesave.connect(self.actionSave.setEnabled)
        self.featureform.rejected.connect(self.cancel.emit)

        self.scrollAreaWidgetContents.layout().addWidget(self.featureform)

    def delete_feature(self):
        try:
            msg = self.featureform.deletemessage
        except AttributeError:
            msg = 'Do you really want to delete this feature?'

        box = DeleteFeatureDialog(msg, QApplication.activeWindow())

        if not box.exec_():
            return

        print self.featureform
        deleted, error = self.featureform.delete()
        if not deleted:
            RoamEvents.raisemessage(*error)

        self.featuredeleted.emit()

    def save_feature(self):
        saved, error = self.featureform.save()
        if not saved:
            RoamEvents.raisemessage(*error)

        self.featuresaved.emit()
        RoamEvents.featuresaved.emit()

    def set_config(self, config):
        self.config = config
        editmode = config['editmode']
        allowsave = config.get('allowsave', True)
        self.feature = config.get('feature', None)
        self.featureform.feature = self.feature
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
        return formwidget

    def initWidget(self, widget):
        widget.actionCancel.triggered.connect(self.cancelform)
        widget.featuresaved.connect(self.emitfished)
        widget.featuredeleted.connect(self.emitfished)

    def cancelform(self):
        self.emitcancel()

    def updatefromconfig(self):
        self.widget.set_config(self.config)

    def before_load(self):
        self.widget.before_load()

    def value(self):
        values, savedvalues = self.widget.featureform.getvalues()
        return values

    def setvalue(self, value):
        self.widget.bind_values(value)


class DataEntryWidget(dataentry_widget, dataentry_base):
    """
    """
    rejected = pyqtSignal(str, int)
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

    def formrejected(self, message=None, level=featureform.RejectedException.WARNING):
        self.rejected.emit(message, level)

    def add_widget(self, widgettype, lastvalue, callback, config, initconfig=None):
        def cleanup():
            # Pop the widget off the current widget stack and kill it.
            wrapper, position = self.widgetstack.pop()
            self.clearwidget(position)

        widget = widgettype.createwidget(config=initconfig)
        largewidgetwrapper = widgettype.for_widget(widget, None, None, None, None, map=self.canvas)
        largewidgetwrapper.largewidgetrequest.connect(RoamEvents.show_widget.emit)
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

    def clear(self, dontemit=False):
        for i in xrange(self.stackedWidget.count()):
            self.clearwidget(i, dontemit)

    def clearwidget(self, position=0, dontemit=False):
        widget = self.stackedWidget.widget(position)
        self.stackedWidget.removeWidget(widget)
        if widget:
            widget.deleteLater()

        if self.stackedWidget.count() == 0:
            if not dontemit:
                self.lastwidgetremoved.emit()

    def load_feature_form(self, feature, form, editmode, clear=True, callback=None):
        """
        Opens the form for the given feature.
        """
        print feature
        def _sink(_):
            pass

        if not callback:
            callback = _sink

        if clear:
            # Clear all the other open widgets that might be open.
            self.clear(dontemit=True)

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
            print defaultvalues
            defaultvalues.update(featureform.loadsavedvalues(layer))

        values.update(defaultvalues)

        initconfig = dict(form=form,
                          canvas=self.canvas)
        config = dict(editmode=editmode,
                      layers=QgsMapLayerRegistry.instance().mapLayers(),
                      feature=feature)

        self.add_widget(FeatureFormWidgetEditor, values, callback, config, initconfig=initconfig)
