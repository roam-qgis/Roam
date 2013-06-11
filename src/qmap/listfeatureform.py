from PyQt4.QtGui import QDialog, QListWidgetItem, QApplication
from PyQt4.QtCore import pyqtSignal, Qt
from qgis.core import QgsFeature, QgsMapLayer
from ui_listfeatures import Ui_ListFeatueForm

class ListFeaturesForm(QDialog):
    openFeatureForm = pyqtSignal(QgsFeature, QgsMapLayer)

    def __init__(self):
        QDialog.__init__(self)
        self.ui = Ui_ListFeatueForm()
        self.ui.setupUi(self)
        self.ui.featureList.itemClicked.connect(self.openForm)
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = QApplication.desktop().screenGeometry(0)
        self.move( scr.center() - self.rect().center() )

    def loadFeatureList(self, featuresmaps):
        for feature, layer  in featuresmaps:               
            featureitem = FeatureItem( feature, layer )
            self.ui.featureList.addItem( featureitem )

    def openForm(self, item):
        feature = item.qgsFeature
        layer = item.layer
        self.close()
        self.openFeatureForm.emit(feature, layer)
        
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