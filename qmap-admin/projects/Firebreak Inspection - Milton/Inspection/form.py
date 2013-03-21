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

	def loadPhotos(self):

		def loadPhoto(imagefield, visit=1):
			""" Load the image into the label """
			image = f[imagefield].toByteArray()
			if not image:
				return
				
			pix = QPixmap()
			r = pix.loadFromData(image, 'JPG')
			label = self.getControl("%s_%s" % (imagefield,visit))
			label.setScaledContents(True)
			label.setPixmap(pix)

		photolayer = QgsMapLayerRegistry.instance().mapLayersByName("Photo")[0]
		ID = str(self.feature['ID'].toString())
		photolayer.setSubsetString("INSPECTIONID = %s" % ID)
		features = list(photolayer.getFeatures())
		f = features[0]
		loadPhoto('PHOTO1')
		loadPhoto('PHOTO2')
		loadPhoto('PHOTO3')
		try:
			f = features[1]
			loadPhoto('PHOTO1',2)
			loadPhoto('PHOTO2',2)
			loadPhoto('PHOTO3',2)
		except IndexError:
			pass


def open(dialog, layer, feature):
	form = InspectionForm(dialog, layer, feature)
	form.setAddress()

	# # Anything greater then 0 is an existing feature.
	# if feature.id() > 0:
	# 	form.disableInspectionSection()
	
	form.loadPhotos()

