__author__ = 'Nathan.Woodrow'

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QPixmap
from PyQt4.Qsci import QsciLexerSQL, QsciScintilla

from qgis.core import QgsDataSourceURI

from configmanager.ui.nodewidgets import ui_layersnode, ui_layernode, ui_infonode, ui_projectinfo
from configmanager.models import CaptureLayersModel, LayerTypeFilter


class WidgetBase(QWidget):
    def set_project(self, project, treenode):
        self.project = project
        self.treenode = treenode

    def write_config(self):
        """
        Write the config back to the project settings.
        """
        pass


class ProjectInfoWidget(ui_projectinfo.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(ProjectInfoWidget, self).__init__(parent)
        self.setupUi(self)
        self.titleText.textChanged.connect(self.updatetitle)

    def updatetitle(self, text):
        self.project.settings['title'] = text
        self.titleText.setText(text)

    def setsplash(self, splash):
        pixmap = QPixmap(splash)
        w = self.splashlabel.width()
        h = self.splashlabel.height()
        self.splashlabel.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

    def set_project(self, project, treenode):
        super(ProjectInfoWidget, self).set_project(project, treenode)
        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)
        self.setsplash(project.splash)
        self.versionText.setText(self.project.version)

    def write_config(self):
        title = self.titleText.text()
        description = self.descriptionText.toPlainText()
        version = str(self.versionText.text())

        settings = self.project.settings
        settings['title'] = title
        settings['description'] = description
        settings['version'] = version


class InfoNode(ui_infonode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(InfoNode, self).__init__(parent)
        self.setupUi(self)
        self.Editor.setLexer(QsciLexerSQL())
        self.Editor.setMarginWidth(0, 0)
        self.Editor.setWrapMode(QsciScintilla.WrapWord)
        self.layer = None
        self.message_label.setVisible(False)

    def set_project(self, project, node):
        super(InfoNode, self).set_project(project, node)
        self.layer = node.layer
        # uri = QgsDataSourceURI(self.layer.dataProvider().dataSourceUri())
        source = self.layer.source()
        name = self.layer.dataProvider().name()
        if ".sqlite" in source or name == "mssql":
            self.setEnabled(True)
            self.message_label.setVisible(False)
        else:
            self.setEnabled(False)
            self.message_label.setVisible(True)
            return

        infoblock = self.project.info_query(node.key, node.layer.name())
        caption = infoblock.get("caption", node.text())
        query = infoblock.get("query", "")
        self.caption_edit.setText(caption)
        self.Editor.setText(query)

    def write_config(self):
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        if self.Editor.text():
            infoconfig[self.treenode.key] = {
                "caption": self.caption_edit.text(),
                "query": self.Editor.text(),
                "connection": "from_layer"
            }
        else:
            try:
                del infoconfig[self.treenode.key]
            except KeyError:
                pass

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayerWidget(ui_layernode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(LayerWidget, self).__init__(parent)
        self.setupUi(self)

    def set_project(self, project, node):
        super(LayerWidget, self).set_project(project, node)
        self.layer = node.layer
        tools = self.project.layer_tools(self.layer)
        delete = 'delete' in tools
        capture = 'capture' in tools
        edit_attr = 'edit_attributes' in tools
        edit_geom = 'edit_geom' in tools
        self.capture_check.setChecked(capture)
        self.delete_check.setChecked(delete)
        self.editattr_check.setChecked(edit_attr)
        self.editgeom_check.setChecked(edit_geom)
        self.datasouce_label.setText(self.layer.publicSource())

    def write_config(self):
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        capture = self.capture_check.isChecked()
        delete = self.delete_check.isChecked()
        editattr = self.editattr_check.isChecked()
        editgoem = self.editgeom_check.isChecked()
        tools = []
        if capture:
            tools.append("capture")
        if delete:
            tools.append("delete")
        if editattr:
            tools.append("edit_attributes")
        if editgoem:
            tools.append("edit_geom")

        infoconfig['tools'] = tools

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


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
        self.treenode.refresh()

    def set_project(self, project, node):
        super(LayersWidget, self).set_project(project, node)
        self.selectlayermodel.config = project.settings
        self.selectlayermodel.refresh()

