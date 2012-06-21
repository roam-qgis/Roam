from PyQt4.QtGui import QDialog, QListWidgetItem, QApplication
from PyQt4.QtCore import pyqtSignal, Qt
from qgis.core import QgsFeature, QgsMapLayer
from Form import Form

from ui_listfeatures import Ui_ListFeatueForm

class ListFeaturesForm(QDialog):
    openFeatureForm = pyqtSignal(object, QgsFeature, QgsMapLayer)

    def __init__(self):
        QDialog.__init__(self)
        self.ui = Ui_ListFeatueForm()
        self.ui.setupUi(self)
        self.ui.featureList.itemClicked.connect(self.openForm)
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = QApplication.desktop().screenGeometry(0)
        self.move( scr.center() - self.rect().center() )

    def loadFeatureList(self, featureDict):
        for feature, formAndLayer in featureDict.items():

            #TODO We don't handle default forms just yet
            if formAndLayer[0] == "Default":
                continue
                
            featureitem = FeatureItem( feature, formAndLayer[0], formAndLayer[1] )
            self.ui.featureList.addItem( featureitem )

    def openForm(self, item):
        form = item.editForm
        feature = item.qgsFeature
        layer = item.layer
        self.close()
        self.openFeatureForm.emit(form, feature, layer)
        
class FeatureItem(QListWidgetItem):
    def __init__(self, feature, form, layer):
        QListWidgetItem.__init__(self)
        self.editform = form
        self.feature = feature
        self._layer = layer
        formname = "Default"''
        if not form == "Default":
            formname = form.formName()

        self.setText("%s for item no. %s" % ( formname , str(self.feature.id()) ))
        
    @property
    def editForm(self):
        return self.editform

    @property
    def qgsFeature(self):
        return self.feature

    @property
    def layer(self):
        return self._layer