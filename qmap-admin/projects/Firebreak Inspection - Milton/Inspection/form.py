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

	def addImageWidgets(self):
		layout = self.getControl("frame" + str(visit)).layout()
		picture = QMapImageWidget(image)
		picture.setFixedSize(100,100)
		layout.addWidget(picture)

	def loadPhotos(self):
		def loadPhotoOrDefault(imagefield, visit=1):
			""" Load the image into the label """
			if not f is None:
				image = f[imagefield].toByteArray()
			else:
				image = None

			name = "%s_%s" % (imagefield, str(visit))
			imagecontrol = self.getControl(name)
			imagecontrol.loadImage(image)

		photolayer = QgsMapLayerRegistry.instance().mapLayersByName("Photo")[0]
		ID = self.feature['ID'].toInt()[0]

		if ID == 0:
			return

		photolayer.setSubsetString("INSPECTIONID = %s" % str(ID))
		features = list(photolayer.getFeatures())
		
		count = 1
		for f in features:
			loadPhotoOrDefault('PHOTO1', count)
			loadPhotoOrDefault('PHOTO2', count)
			loadPhotoOrDefault('PHOTO3', count)
			count += 1

def open(dialog, layer, feature):
	form = InspectionForm(dialog, layer, feature)
	form.setAddress()

	# Anything greater then 0 is an existing feature.
	if feature.id() > 0:
		form.disableInspectionSection()
	
	form.loadPhotos()

