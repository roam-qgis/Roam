from PyQt4.QtGui import QToolBar, QActionGroup
from PyQt4.QtCore import Qt, QPoint
from utils import log

class FloatingToolBar(QToolBar):
	"""
	A floating QToolBar with no border and is offset under its parent
	"""
	def __init__(self, name, parent):
		"""
		parent: The parent of this toolbar.  Should be another toolbar
		""" 
		QToolBar.__init__(self,name, parent)
		self.setMovable(False)
		self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint)
		self.setAllowedAreas(Qt.NoToolBarArea)
		self.actiongroup = QActionGroup(self)

	def addToActionGroup(self, action):
		self.actiongroup.addAction(action)

	def showToolbar(self, parentaction, defaultaction, toggled):
		if toggled:
			self.show()
			if defaultaction:
				defaultaction.toggle()
			widget = self.parent().widgetForAction(parentaction)
			x = self.parent().mapToGlobal(widget.pos()).x()
			y = self.parent().mapToGlobal(widget.pos()).y()
			newpoint = QPoint(x, y + self.parent().rect().height())
# 			if self.orientation() == Qt.Vertical:
# 				newpoint = QPoint(x, y + self.parent().rect().width())
			self.move(newpoint)
		else:
			action = self.actiongroup.checkedAction()
			if action:			
				action.toggle()
			self.hide()
