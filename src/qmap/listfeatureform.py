import resources_rc

from PyQt4.QtGui import QDialog, QListWidgetItem, QApplication
from PyQt4.QtCore import pyqtSignal, Qt
from qgis.core import QgsFeature, QgsVectorLayer, QgsExpression

from uifiles import features_widget, features_base

class ListFeaturesForm(features_widget, QDialog):
    openFeatureForm = pyqtSignal(QgsVectorLayer, QgsFeature)

    def __init__(self, parent):
        super(ListFeaturesForm, self).__init__(parent)
        self.setupUi(self)
        self.featureList.itemClicked.connect(self.openForm)
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = parent.geometry()
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
        index = layer.fieldNameIndex(layer.displayField())
        if index < 0:
            display = QgsExpression.replaceExpressionText(layer.displayField(), feature, layer )
        else:
            display = feature[index]
        self.setText("{0} ({1})".format(display, layer.name()))
        
    @property
    def qgsFeature(self):
        return self.feature

    @property
    def layer(self):
        return self._layer