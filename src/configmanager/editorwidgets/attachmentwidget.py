import functools

from PyQt5.QtGui import QFileDialog
from PyQt5.QtCore import QDir

from qgis.gui import QgsExpressionBuilderDialog

from configmanager.editorwidgets.core import ConfigWidget
from configmanager.editorwidgets.uifiles.ui_attachmentwidget_config import Ui_Form


class AttachmentWidgetConfig(Ui_Form, ConfigWidget):
    description = 'Generic attachment widget'

    def __init__(self, parent=None):
        super(AttachmentWidgetConfig, self).__init__(parent)
        self.setupUi(self)
        self.defaultLocationText.textChanged.connect(self.widgetchanged)
        self.locatioButton.pressed.connect(functools.partial(self.openfilepicker, self.defaultLocationText))
        self.locatioButton_2.pressed.connect(functools.partial(self.openfilepicker, self.saveLocationText))

        self.saveLocationText.textChanged.connect(self.widgetchanged)
        self.namingText.textChanged.connect(self.widgetchanged)
        self.fileActionGroup.buttonClicked[int].connect(self.widgetchanged)
        self.nameExpressionButton.pressed.connect(self.show_builder)

    def show_builder(self):
        dlg = QgsExpressionBuilderDialog(None)
        if dlg.exec_():
            self.namingText.setText(dlg.expressionText())

    def selected_action(self):
        button = self.fileActionGroup.checkedButton()
        name = button.objectName()
        if name == "noActionButton":
            return "none"
        elif name == "moveButton":
            return "move"
        elif name == "copyButton":
            return "copy"

        return "copy"

    def action_to_button(self, action):
        if action == "none":
            self.noActionButton.setChecked(True)
        elif action == "move":
            self.moveButton.setChecked(True)
        elif action == "copy":
            self.copyButton.setChecked(True)
        else:
            self.copyButton.setChecked(True)

    def openfilepicker(self, widget):
        startpath = widget.text() or QDir.homePath()
        path = QFileDialog.getExistingDirectory(self.parent(), "", startpath)
        widget.setText(path)

    def getconfig(self):
        location = self.defaultLocationText.text()
        savelocation = self.saveLocationText.text()
        nameing = self.namingText.text()
        action = self.selected_action()
        return {"defaultlocation": location,
                'action': action,
                'savelocation': savelocation,
                'nameformat': nameing}

    def setconfig(self, config):
        self.defaultLocationText.setText(config.get('defaultlocation', ''))
        self.saveLocationText.setText(config.get('savelocation', ''))
        self.namingText.setText(config.get('nameformat', ''))
        action = config.get('action', 'copy')
        self.action_to_button(action)
