from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor

class MoveTool(QgsMapTool):
	def __init__(self, canvas, layers):
		QgsMapTool.__init__(self, canvas)
		self.band = None
		self.feature = None
		self.startcoord = None
		self.layers = layers

	def canvasMoveEvent(self, event):
		"""
		Override of QgsMapTool mouse move event
		"""
		if self.band:
			point = self.toMapCoordinates(event.pos())
			offsetX = point.x() - self.startcoord.x()
			offsetY = point.y() - self.startcoord.y()
			self.band.setTranslationOffset(offsetX, offsetY)
			self.band.updatePosition()
			self.band.update()

	def canvasPressEvent(self, event):
		"""
		Override of QgsMapTool mouse press event
		"""
		self.band = None
		self.feature = None
		self.layer = None
		self.feature = None

		if not self.layers:
			return

		# Stops at the first feature found
		for layer in self.layers:
			point = self.toLayerCoordinates(layer, event.pos())
			searchRadius = (QgsTolerance.toleranceInMapUnits( 10, layer,
															 self.canvas().mapRenderer(), QgsTolerance.Pixels))

			rect = QgsRectangle()                                                 
			rect.setXMinimum( point.x() - searchRadius );
			rect.setXMaximum( point.x() + searchRadius );
			rect.setYMinimum( point.y() - searchRadius );
			rect.setYMaximum( point.y() + searchRadius );
			
			rq = QgsFeatureRequest().setFilterRect(rect)
			try:
				f = layer.getFeatures(rq).next()
			except StopIteration:
				continue
			
			if f:
				self.band = self.createRubberBand()
				self.band.setToGeometry(f.geometry(), layer)
				self.band.show()
				self.startcoord = self.toMapCoordinates(event.pos())
				self.feature = f
				self.layer = layer
				self.layer.startEditing()
				return

	def canvasReleaseEvent(self, event):
		"""
		Override of QgsMapTool mouse release event
		"""
		if not self.band:
			return

		if not self.layer:
			return

		if not self.feature:
			return

		startpoint = self.toLayerCoordinates(self.layer, self.startcoord)
		endpoint = self.toLayerCoordinates(self.layer, event.pos())

		dx = endpoint.x() - startpoint.x()
		dy = endpoint.y() - startpoint.y()

		self.layer.translateFeature(self.feature.id(), dx, dy)

		self.band.hide()
		self.band = None
		self.layer.commitChanges()
		self.canvas().refresh()

	def deactivate(self):
		"""
		Deactive the tool.
		"""
		self.band = None

	def createRubberBand(self):
		"""
		Creates a new rubber band.
		"""
		band = QgsRubberBand(self.canvas())
		band.setColor(QColor.fromRgb(237,85,9))
		band.setWidth(6)
		return band