import PyQt4.uic
import os
import PyQt4
from PyQt4.QtGui import (QLabel, QDialog, QFileDialog, 
						QPixmap, QGridLayout, QLayout, 
						QWidget)
from PyQt4.QtCore import (QByteArray, QBuffer, 
						QIODevice, QEvent, QObject, pyqtSignal)
import logging
import images_rc

basepath = os.path.dirname(__file__)
uipath = os.path.join(basepath,'imagewidget.ui')
widgetForm, baseClass= PyQt4.uic.loadUiType(uipath)

class QMapImageWidget(baseClass, widgetForm):
	openRequest = pyqtSignal(QPixmap)
	
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
		self.installEventFilter(self)
		
	def eventFilter(self, parent, event):
		""" Handle mouse click events for disabled widget state """
		if event.type() == QEvent.MouseButtonRelease:
			if self.isDefault:
				return QObject.eventFilter(self, parent, event)
			self.openRequest.emit(self.image.pixmap())
		
		return QObject.eventFilter(self, parent, event)
	def selectImage(self):
		# Show the file picker
		image  = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.jpg)")
		if image is None or not image:
			return

		pix = QPixmap(image)
		self.loadFromPixMap(pix)

	def removeImage(self):
		pix = QPixmap(":/images/images/add.png")
		self.loadFromPixMap(pix)
		self.image.setScaledContents(False)
		self.isDefault = True
		
	def imageClick(self, event):
		if self.isDefault:
			self.selectImage()
		else:
			self.openRequest.emit(self.image.pixmap())
			
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
		if data is None or not data:
			self.removeImage()
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
		# or in a disabled state
		if self.isDefault or not self.isEnabled():
			return

		self.selectbutton.setVisible(True)
		self.deletebutton.setVisible(True)
		
	def leaveEvent(self, event):
		self.selectbutton.setVisible(False)
		self.deletebutton.setVisible(False)