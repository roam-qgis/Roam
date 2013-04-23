from PyQt4 import QtGui, QtDesigner
from imagewidget import QMapImageWidget

class QMapImageWidgetPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent = None):
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False

    def initialize(self, core):
    	if self.initialized:
    		return

    	self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
    	return QMapImageWidget(parent=parent)

    def name(self):
    	return "QMapImageWidget"

    def group(self):
    	return "QMap"

    def icon(self):
    	return QtGui.QIcon()

    def toolTip(self):
    	return ""

    def whatsThis(self):
    	return ""

    def isContainer(self):
    	return False

	def domXml(self):
	    return '<widget class="QMapImageWidget" name=\"imagewidget\" />\n'

	def includeFile(self):
		return "imagewidget"



