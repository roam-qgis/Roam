from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import PyQt4.uic
import os
import images_rc

basepath = os.path.dirname(__file__)
uipath = os.path.join(basepath,'imagewidget.ui')
widgetForm, baseClass= PyQt4.uic.loadUiType(uipath)

class PictureWidget(baseClass, widgetForm):
	def __init__(self, data=None, parent=None):
		super(PictureWidget, self).__init__(parent)
		self.setupUi(self)
		self.setStyleSheet(":hover {background-color: #dddddd;}")
		self.selectbutton.setVisible(False)
		self.deletebutton.setVisible(False)
		self.loadImage(data)

	def loadImage(self, data):
		if data is None:
			return

		pix = QPixmap()
		r = pix.loadFromData(data, 'JPG')
		self.image.setScaledContents(True)
		self.image.setPixmap(pix)

	def enterEvent(self, event):
		self.selectbutton.setVisible(True)
		self.deletebutton.setVisible(True)
		
	def leaveEvent(self, event):
		self.selectbutton.setVisible(False)
		self.deletebutton.setVisible(False)

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
			layout = self.getControl("frame" + str(visit)).layout()
			picture = PictureWidget(image)
			picture.setFixedSize(100,100)
			layout.addWidget(picture)

		photolayer = QgsMapLayerRegistry.instance().mapLayersByName("Photo")[0]
		ID = str(self.feature['ID'].toString())
		photolayer.setSubsetString("INSPECTIONID = %s" % ID)
		features = list(photolayer.getFeatures())
		
		try:
			f = features[0]
			loadPhoto('PHOTO1')
			loadPhoto('PHOTO2')
			loadPhoto('PHOTO3')
		except IndexError:
			pass

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
	if feature.id() > 0:
		form.disableInspectionSection()
	
	form.loadPhotos()

