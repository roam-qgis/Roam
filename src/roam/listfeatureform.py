import resources_rc

from PyQt4.QtGui import QDialog, QListWidgetItem, QApplication, QIcon
from PyQt4.QtCore import pyqtSignal, Qt
from qgis.core import QgsFeature, QgsVectorLayer, QgsExpression

from roam.uifiles import features_widget, features_base


class ListFeaturesForm(features_widget, QDialog):
    openFeatureForm = pyqtSignal(object, QgsFeature)

    def __init__(self, parent):
        super(ListFeaturesForm, self).__init__(parent)
        self.setupUi(self)
        self.featureList.itemClicked.connect(self.openForm)
        self.setWindowFlags(Qt.FramelessWindowHint)
        scr = parent.geometry()
        self.move( scr.center() - self.rect().center() )

    def loadFeatureList(self, featuresmaps):
        print featuresmaps
        for feature, forms in featuresmaps.iteritems():
            print feature, forms
            for form in forms:
                print form.name
                featureitem = FeatureItem(feature, form)
                self.featureList.addItem(featureitem)

    def openForm(self, item):
        feature = item.feature
        form = item.form
        self.close()
        self.openFeatureForm.emit(form, feature)


class FeatureItem(QListWidgetItem):
    def __init__(self, feature, form):
        super(FeatureItem, self).__init__()
        self.feature = feature
        self.form = form

    def data(self, role):
        if role == Qt.DisplayRole:
            layer = self.form.QGISLayer
            displayfield = self.form.settings.get('display', '')
            if not displayfield:
                # If there is no display field set then just grab the first field
                display = self.feature[0]
            else:
                # If there is then run it as an expression
                display = QgsExpression.replaceExpressionText(layer.displayField(), self.feature, layer )
            return "{0} ({1})".format(display, self.form.label)
        elif role == Qt.DecorationRole:
            icon = QIcon(self.form.icon)
