# If pluginType is MODULE, the plugin loader will call moduleInformation.  The
# variable MODULE is inserted into the local namespace by the plugin loader.

pluginType = 0

# moduleInformation() must return a tuple (module, widget_list).  If "module"
# is "A" and any widget from this module is used, the code generator will write
# "import A".  If "module" is "A[.B].C", the code generator will write
# "from A[.B] import C".  Each entry in "widget_list" must be unique.
def moduleInformation():
    return "imagewidget", ("QMapImageWidget", )

from PyQt4 import QtGui, QtDesigner
from imagewidget import QMapImageWidget

class QMapImageWidgetPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent = None):
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self, parent)
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
	    return '<widget class="QMapImageWidget" name="imagewidget" header="imagewidget" />\n'

	def includeFile(self):
		return "imagewidget"



