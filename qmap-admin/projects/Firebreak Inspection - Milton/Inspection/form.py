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
		self.selectbutton.clicked.connect(self.selectImage)
		self.deletebutton.clicked.connect(self.removeImage)
		self.isDefault = True
		self.loadImage(data)
		self.image.mouseReleaseEvent = self.imageClick
		

	def selectImage(self):
		# Show the file picker
		image  = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.jpg)")
		if image.isEmpty():
			return

		pix = QPixmap(image)
		self.loadFromPixMap(pix)

	def removeImage(self):
		pix = QPixmap(":/images/add.png")
		self.loadFromPixMap(pix)
		self.image.setScaledContents(False)
		self.isDefault = True

	def imageClick(self, event):
		if self.isDefault:
			self.selectImage()
		else:
			label = QLabel()
			label.setPixmap(self.image.pixmap())
			label.setScaledContents(True)
			dlg = QDialog()
			dlg.setWindowTitle("Image Viewer")
			dlg.setLayout(QGridLayout())
			dlg.layout().setContentsMargins(0,0,0,0)
			dlg.layout().setSizeConstraint(QLayout.SetNoConstraint)
			dlg.resize(600,600)
			dlg.layout().addWidget(label)
			dlg.exec_()

	def loadFromPixMap(self, pixmap):
		self.image.setScaledContents(True)
		self.image.setPixmap(pixmap)
		self.isDefault = False

	def loadImage(self, data):
		""" 
			Load the image into the widget using a bytearray 

			An empty picture will result in the default placeholder
			image.
		"""
		if data.isEmpty():
			self.isDefault = True
			return

		pix = QPixmap()
		r = pix.loadFromData(data, 'JPG')
		self.image.setScaledContents(True)
		self.image.setPixmap(pix)
		self.isDefault = False

	def getImage(self):
		""" Return the loaded image """
		if self.isDefault:
			return None

		pix = self.image.pixmap()
		bytes = QByteArray()
		buf = QBuffer(bytes)
		buf.open(QIODevice.WriteOnly)
		pix.save(buf, "JPG")
		return bytes

	def enterEvent(self, event):
		# Don't show the image controls if we are on the default image
		if self.isDefault:
			return

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

		def loadPhotoOrDefault(imagefield, visit=1):
			""" Load the image into the label """
			if not f is None:
				image = f[imagefield].toByteArray()
			else:
				image = None

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
		except IndexError:
			f = None

		loadPhotoOrDefault('PHOTO1')
		loadPhotoOrDefault('PHOTO2')
		loadPhotoOrDefault('PHOTO3')

		try:
			f = features[1]
		except IndexError:
			f = None

		loadPhotoOrDefault('PHOTO1',2)
		loadPhotoOrDefault('PHOTO2',2)
		loadPhotoOrDefault('PHOTO3',2)


def open(dialog, layer, feature):
	form = InspectionForm(dialog, layer, feature)
	form.setAddress()

	# Anything greater then 0 is an existing feature.
	# if feature.id() > 0:
	# 	form.disableInspectionSection()
	
	form.loadPhotos()

