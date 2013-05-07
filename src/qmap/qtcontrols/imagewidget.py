import PyQt4.uic
import images_rc
import os
import PyQt4
from PyQt4.QtGui import QLabel, QDialog, QFileDialog, QPixmap, QGridLayout, QLayout
from PyQt4.QtCore import QByteArray, QBuffer, QIODevice

basepath = os.path.dirname(__file__)
uipath = os.path.join(basepath,'imagewidget.ui')
widgetForm, baseClass= PyQt4.uic.loadUiType(uipath)

class QMapImageWidget(baseClass, widgetForm):
	def __init__(self, data=None, parent=None):
		super(QMapImageWidget, self).__init__(parent)
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
		if image is None or image.isEmpty():
			return

		pix = QPixmap(image)
		self.loadFromPixMap(pix)

	def removeImage(self):
		pix = QPixmap(":/images/add.png")
		self.loadFromPixMap(pix)
		self.image.setScaledContents(False)
		self.isDefault = True

	def openImageViewer(self):
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

	def imageClick(self, event):
		if self.isDefault:
			self.selectImage()
		else:
			self.openImageViewer()
			

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
		if data is None or data.isEmpty():
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
		by = QByteArray()
		buf = QBuffer(by)
		buf.open(QIODevice.WriteOnly)
		pix.save(buf, "JPG")
		return by

	def enterEvent(self, event):
		# Don't show the image controls if we are on the default image
		if self.isDefault:
			return

		self.selectbutton.setVisible(True)
		self.deletebutton.setVisible(True)
		
	def leaveEvent(self, event):
		self.selectbutton.setVisible(False)
		self.deletebutton.setVisible(False)