__author__ = 'Nathan.Woodrow'

from PyQt4.QtGui import QWidget
from PyQt4.Qsci import QsciLexerSQL

from configmanager.ui.nodewidgets import ui_layersnode, ui_layernode, ui_infonode
from configmanager.models import CaptureLayersModel, LayerTypeFilter


class WidgetBase(QWidget):
    def set_project(self, project):
        self.project = project


class InfoNode(ui_infonode.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(InfoNode, self).__init__(parent)
        self.setupUi(self)
        self.Editor.setLexer(QsciLexerSQL())
        self.Editor.setMarginWidth(0, 0)


class LayerWidget(ui_layernode.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(LayerWidget, self).__init__(parent)
        self.setupUi(self)


class LayersWidget(ui_layersnode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(LayersWidget, self).__init__(parent)
        self.setupUi(self)

        self.selectlayermodel = CaptureLayersModel(watchregistry=True)
        self.selectlayerfilter = LayerTypeFilter(geomtypes=[])
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)
        self.selectlayermodel.dataChanged.connect(self.selectlayerschanged)

        self.selectLayers.setModel(self.selectlayerfilter)

    def selectlayerschanged(self):
        pass

    def set_project(self, project):
        super(LayersWidget, self).set_project(project)
        self.selectlayermodel.config = project.settings
        self.selectlayermodel.refresh()

