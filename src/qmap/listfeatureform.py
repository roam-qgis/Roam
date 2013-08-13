import resources_rc

from PyQt4.QtGui import QDialog, QListWidgetItem, QApplication
from PyQt4.QtCore import pyqtSignal, Qt
from qgis.core import QgsFeature, QgsVectorLayer

from uifiles import features_widget, features_base

class ListFeaturesForm(features_widget, features_base):
    openFeatureForm = pyqtSignal(QgsVectorLayer, QgsFeature)

    def __init__(self):
        super(ListFeaturesForm, self).__init__()
        self.setupUi(self)
        self.featureList.itemClicked.connect(self.openForm)
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = QApplication.desktop().screenGeometry(0)
        self.move( scr.center() - self.rect().center() )

    def loadFeatureList(self, featuresmaps):
        for feature, layer  in featuresmaps:               
            featureitem = FeatureItem( feature, layer )
            self.featureList.addItem( featureitem )

    def openForm(self, item):
        feature = item.qgsFeature
        layer = item.layer
        self.close()
        self.openFeatureForm.emit(layer, feature)
        
class FeatureItem(QListWidgetItem):
    def __init__(self, feature, layer):
        QListWidgetItem.__init__(self)
        self.feature = feature
        self._layer = layer
        self.setText("{} on {}".format(feature.id(), layer.name()))
        
    @property
    def qgsFeature(self):
        return self.feature

    @property
    def layer(self):
        return self._layer