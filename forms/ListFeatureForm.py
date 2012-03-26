from PyQt4.QtGui import QDialog, QListWidgetItem
from ui_listfeatures import Ui_ListFeatueForm

class ListFeaturesForm(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.ui = Ui_ListFeatueForm()
        self.ui.setupUi(self)

    def loadFeatueList(self, featureDict):
        for feature,form in featureDict.items():
            featureitem = FeatureItem( feature, form )
            self.ui.featureList.addItem( featureitem )

class FeatureItem(QListWidgetItem):
    def __init__(self, feature, form):
        QListWidgetItem.__init__(self)
        self.editform = form
        self.feature = feature
        formname = "Default"
        if not form == "Default":
            formname = form.__formName__

        self.setText("Open %s from for %s" % ( formname , str(self.feature.id()) ))
        
    @property
    def editForm(self):
        return self.editform

    @property
    def qgsFeature(self):
        return self.feature