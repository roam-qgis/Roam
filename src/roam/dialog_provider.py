import os.path
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsMapLayerRegistry, QgsFeatureRequest

from roam.utils import log, info, warning, error
from roam import featuredialog
from roam.helpviewdialog import HelpPage

form = None

class DefaultError(Exception):
    pass


def spatial_query(feature, layer, field, defaultconfig):
    layername = defaultconfig['layer']
    op = defaultconfig['op']
    field = defaultconfig['field']

    print defaultconfig

    layer = QgsMapLayerRegistry.instance().mapLayersByName(layername)[0]
    if op == 'contains':
        rect = feature.geometry().boundingBox()
        features = layer.getFeatures(QgsFeatureRequest().setFilterRect(rect))
        print features
        for f in features:
            print f
            geometry = feature.geometry()
            print f.geometry().contains(geometry)
            if f.geometry().contains(geometry):
                print "CONTAINS"
                print f[field]
                return f[field]
        raise DefaultError('No features found')

defaultproviders = {'spatial-query': spatial_query}

class DialogProvider(QObject):
    """
    A class to handle opening user form and creating all the required bindings

    @note: There is a little too much work in this class. Needs a bit of a clean up.
    """
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    featuresaved = pyqtSignal()
    failedsave = pyqtSignal(list)
    
    def __init__(self, canvas):
        QObject.__init__(self)
        self.canvas = canvas

    def openDialog(self, feature, form, parent=None):
        """
        Opens a form for the given feature
        """
        layer = form.QGISLayer
        def accept():
            if not featureform.accept():
                return

            feature, savedvalues = featureform.getupdatedfeature()
            layer.startEditing()
            if feature.id() > 0:
                layer.updateFeature(feature)
            else:
                layer.addFeature(feature)
                featuredialog.savevalues(layer, savedvalues)
            saved = layer.commitChanges()

            if not saved:
                self.failedsave.emit(layer.commitErrors())
                map(error, layer.commitErrors())
            else:
                self.featuresaved.emit()

            self.canvas.refresh()
            parent.showmap()
            self.accepted.emit()

        def reject():
            if not featureform.reject():
                return

            layer.rollBack()
            clearcurrentwidget()
            parent.showmap()
            parent.hidedataentry()
            self.rejected.emit()

        def formvalidation(passed):
            msg = None
            if not passed:
                msg = "Looks like some fields are missing. Check any fields marked in"
            parent.missingfieldsLabel.setText(msg)
            parent.savedataButton.setEnabled(passed)
            parent.yellowLabel.setVisible(not passed)

        def clearcurrentwidget():
            item = parent.scrollAreaWidgetContents.layout().itemAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        def showhelp(url):
            help = HelpPage(parent.stackedWidget)
            help.setHelpPage(url)
            help.show()

        # None of this saving logic belongs here.
        parent.savedataButton.pressed.connect(accept)
        parent.cancelButton.pressed.connect(reject)

        defaults = {}
        if not feature.id() > 0:
            for field, config in form.widgetswithdefaults():
                default = config.get("default", None)
                if default is None:
                    continue
                if isinstance(default, dict):
                    defaultconfig = default
                    try:
                        defaulttype = defaultconfig['type']
                        defaultprovider = defaultproviders[defaulttype]
                        value = defaultprovider(feature, layer, field, defaultconfig)
                    except KeyError:
                        continue
                    except DefaultError as ex:
                        log(ex)
                        value = None
                else:
                    value = default

                print "VALUE {}".format(value)
                defaults[field] = value
            defaults.update(featuredialog.loadsavedvalues(layer))

        featureform = form.featureform
        featureform.formvalidation.connect(formvalidation)
        featureform.helprequest.connect(showhelp)

        featureform.bindfeature(feature, defaults)

        clearcurrentwidget()

        parent.scrollAreaWidgetContents.layout().insertWidget(0, featureform.widget)
        parent.showdataentry()
