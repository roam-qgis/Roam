from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

class InspectionForm():
	def __init__(self, dialog, layer, feature):
		self.dialog = dialog
		self.layer = layer
		self.feature = feature

		# Due to a bug in QGIS the fields are not passed into the
		# new feature we are given.  
		# No big deal we can just do it here.
		if feature.id() == 0:
			self.fields = self.layer.pendingFields()
			self.feature.setFields(self.fields)

	def getControl(self, name):
		return self.dialog.findChild(QWidget, name)

	def setAddress(self):
		address1 = str(self.feature['PROPERTY_ADDRESS1'].toString())
		address2 = str(self.feature['PROPERTY_ADDRESS2'].toString())
		newaddress = address1 + '\n' + address2
		addresscontrol = self.getControl("ADDRESS")
		addresscontrol.setPlainText(newaddress)

	def disableInspectionSection(self):
		inspectiongroup = self.getControl("InspectionGroup")
		inspectiongroup.setEnabled(False)

def open(dialog, layer, feature):
	form = InspectionForm(dialog, layer, feature)
	form.setAddress()

	# Anything greater then 0 is an existing feature.
	if feature.id() > 0:
		form.disableInspectionSection()
	
	# feature = list(layer.getFeatures(QgsFeatureRequest(feature.id())))[0]
	# image = feature[3].toByteArray()
	# pix = QPixmap()
	# r = pix.loadFromData(image, 'jpg')
	# label = dialog.findChild(QLabel, "PHOTO1")
	# label.setPixmap(pix)