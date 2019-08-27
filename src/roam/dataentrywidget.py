import functools
import os.path
import os
import getpass
import inspect

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest, QgsFeature, QgsExpression, QGis, QgsGeometry

from roam.editorwidgets.featureformwidget import FeatureFormWidgetEditor
from roam.utils import log, error
from roam.api import featureform, RoamEvents
from roam.ui.uifiles import dataentry_widget, dataentry_base
from roam.structs import CaseInsensitiveDict

import roam.defaults as defaults
import roam.editorwidgets.core


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
        self.project = None
        self.canvas = canvas
        self.widgetstack = []

    def formrejected(self, message=None, level=featureform.RejectedException.WARNING):
        self.rejected.emit(message, level)

    def cleanup(self, wrapper, *args):
        # Pop the widget off the current widget stack and kill it.
        if len(args) == 2:
            message = args[0]
            if message:
                level = args[1]
                RoamEvents.raisemessage("Message", message, level=level)

        try:
            index = self.widgetstack.index(wrapper)
            del self.widgetstack[index]
        except ValueError:
            pass
        index = self.stackedWidget.indexOf(wrapper.widget)
        if index == -1:
            return
        self.clearwidget(index)
        wrapper.deleteLater()
        wrapper.setParent(None)

    def add_widget(self, widgettype, lastvalue, callback, config, initconfig=None, cancel_callback=None):
        if not initconfig:
            initconfig = {}

        if inspect.isclass(widgettype):
            widget = widgettype.createwidget(config=initconfig)
            largewidgetwrapper = widgettype.for_widget(widget, None, None, None, None, map=self.canvas)
        else:
            # If the user passes in a instance we can just use that and trust they have set it up right.
            largewidgetwrapper = widgettype
            widget = largewidgetwrapper.widget

        largewidgetwrapper.finished.connect(callback)

        largewidgetwrapper.initWidget(widget, config)
        largewidgetwrapper.config = config
        if isinstance(lastvalue, QPixmap):
            lastvalue = QPixmap(lastvalue)
        largewidgetwrapper.setvalue(lastvalue)

        # This is a bit crappy but will do now
        # until the rest is refactored
        if initconfig.get('suppressform', False) and isinstance(largewidgetwrapper, FeatureFormWidgetEditor):
            largewidgetwrapper.before_load()
            largewidgetwrapper.after_load()
            largewidgetwrapper.save()
            self.lastwidgetremoved.emit()
            return

        largewidgetwrapper.largewidgetrequest.connect(RoamEvents.show_widget.emit)
        largewidgetwrapper.finished.connect(functools.partial(self.cleanup, largewidgetwrapper))
        largewidgetwrapper.cancel.connect(functools.partial(self.cleanup, largewidgetwrapper))
        if cancel_callback:
            largewidgetwrapper.cancel.connect(cancel_callback)

        try:
            largewidgetwrapper.before_load()
            position = self.stackedWidget.addWidget(widget)
            self.stackedWidget.setCurrentIndex(position)
            self.widgetstack.append(largewidgetwrapper)
            largewidgetwrapper.after_load()
        except roam.editorwidgets.core.RejectedException as rejected:
            self.formrejected(rejected.message, rejected.level)
            if self.stackedWidget.count() == 0:
                self.lastwidgetremoved.emit()

    def clear(self, dontemit=False):
        for i in xrange(self.stackedWidget.count()):
            self.clearwidget(i, dontemit)

    def clearwidget(self, position=0, dontemit=False):
        widget = self.stackedWidget.widget(position)
        self.stackedWidget.removeWidget(widget)
        if widget:
            widget.deleteLater()
            widget.setParent(None)

        if self.stackedWidget.count() == 0:
            if not dontemit:
                self.lastwidgetremoved.emit()

    def load_feature_form(self, feature, form, editmode, clear=True, callback=None,
                          cancel_callback=None):
        """
        Opens the form for the given feature.
        """

        def _sink(_):
            pass

        if not callback:
            callback = _sink

        if not cancel_callback:
            cancel_callback = _sink

        if clear:
            # Clear all the other open widgets that might be open.
            self.clear(dontemit=True)

        layer = form.QGISLayer
        attributes = feature.attributes()

        fields = [field.name().lower() for field in layer.pendingFields()]
        # Something is strange with default values and spatilite. Just delete them for now.
        if layer.dataProvider().name() == 'spatialite':
            pkindexes = layer.dataProvider().pkAttributeIndexes()
            for index in pkindexes:
                del fields[index]
                del attributes[index]
        values = CaseInsensitiveDict(zip(fields, attributes))

        savedvalues = {}
        if not editmode:
            savedvalues = featureform.loadsavedvalues(form)
            values.update(savedvalues)
            if form.template_values:
                values.update(form.template_values)

        suppressform = form.suppressform
        if editmode:
            suppressform = False

        initconfig = dict(form=form,
                          canvas=self.canvas,
                          editmode=editmode,
                          defaults=savedvalues,
                          suppressform=suppressform,
                          feature=feature)

        config = dict(editmode=editmode,
                      layers=QgsMapLayerRegistry.instance().mapLayers(),
                      feature=feature)

        if self.project:
            layertools = self.project.layer_tools(layer)
            config['tools'] = layertools
        self.add_widget(FeatureFormWidgetEditor, values, callback, config,
                        initconfig=initconfig,
                        cancel_callback=cancel_callback)
