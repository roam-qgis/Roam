from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import Qt
import qmap

class MoveTool(QgsMapTool):
	def __init__(self, canvas):
		QgsMapTool.__init__(self, canvas)
		self.band = None
		self.feature = None
		self.startcoord = None
		self.canvas = canvas

	def canvasMoveEvent(self, event):
		if self.band:
			point = QgsMapTool.toMapCoordinates(self, event.pos())
			offsetX = point.x() - self.startcoord.x()
			offsetY = point.y() - self.startcoord.y()
			self.band.setTranslationOffset(offsetX, offsetY)
			self.band.updatePosition()
			self.band.update()

	def canvasPressEvent(self, event):
		self.band = None
		self.feature = None
		self.layer = None
		self.feature = None

		if not qmap.QMap.layerformmap:
			return

		# Stops at the first feature found
		for layer in qmap.QMap.layerformmap.iterkeys():
			point = QgsMapTool.toLayerCoordinates(self, layer, event.pos())
			searchRadius = (QgsTolerance.toleranceInMapUnits( 10, layer,
															 self.canvas.mapRenderer(), QgsTolerance.Pixels))

			rect = QgsRectangle()                                                 
			rect.setXMinimum( point.x() - searchRadius );
			rect.setXMaximum( point.x() + searchRadius );
			rect.setYMinimum( point.y() - searchRadius );
			rect.setYMaximum( point.y() + searchRadius );
			
			layer.select([], rect, True, True)
			f = QgsFeature()
			if layer.nextFeature(f):
				self.band = self.createRubberBand()
				self.band.setToGeometry(f.geometry(), layer)
				self.band.show()
				self.startcoord = QgsMapTool.toMapCoordinates(self, event.pos())
				self.feature = f
				self.layer = layer
				self.layer.startEditing()
				return

	def canvasReleaseEvent(self, event):
		if not self.band:
			return

		if not self.layer:
			return

		if not self.feature:
			return

		startpoint = QgsMapTool.toLayerCoordinates(self, self.layer, self.startcoord)
		endpoint = QgsMapTool.toLayerCoordinates(self, self.layer, event.pos())

		dx = endpoint.x() - startpoint.x()
		dy = endpoint.y() - startpoint.y()

		self.layer.translateFeature(self.feature.id(), dx, dy)

		self.band.hide()
		self.band = None
		self.layer.commitChanges()
		self.canvas.refresh()

	def deactivate(self):
		self.band = None
		QgsMapTool.deactivate(self)

	def createRubberBand(self):
		band = QgsRubberBand(self.canvas)
		band.setColor(Qt.red)
		band.setWidth(5)
		return band