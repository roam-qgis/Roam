import os
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QWidget, QAction, QIcon, QFileDialog

from roam.editorwidgets.core import EditorWidget, registerwidgets
from roam.editorwidgets.uifiles import ui_attachmentwidget
from roam.popupdialogs import PickActionDialog

import roam.utils


class RoamAttachmentWidget(ui_attachmentwidget.Ui_attachmentWidget, QWidget):
    attachmentloaded = pyqtSignal()
    attachmentremoved = pyqtSignal()
    attachmentloadrequest = pyqtSignal()

    def __init__(self, parent=None):
        super(RoamAttachmentWidget, self).__init__(parent)
        self.setupUi(self)

        self.setStyleSheet(":hover {background-color: #dddddd;}")
        self.selectbutton.clicked.connect(self.attachmentloadrequest.emit)
        self.deletebutton.clicked.connect(self.removeAttachment)
        self.attachmentImage.mouseReleaseEvent = self.attach
        self.removeAttachment()
        self.filename = None

    def removeAttachment(self):
        self.attachmentremoved.emit()
        self.isDefault = True

    def attach(self, event):
        if self.isDefault:
            self.attachmentloadrequest.emit()

    @property
    def isDefault(self):
        return self.filename is None

    @isDefault.setter
    def isDefault(self, value):
        self.filename = None
        self.selectbutton.setVisible(not value)
        self.deletebutton.setVisible(not value)
        if value:
            self.attachmentloaded.emit()
        else:
            self.attachmentremoved.emit()


class AttachmentWidget(EditorWidget):
    widgettype = 'Attachment'

    def __init__(self, *args, **kwargs):
        super(AttachmentWidget, self).__init__(*args)
        self.defaultlocation = ''
        self.savetofile = True
        self.movetolocation = True
        self.modified = False
        self.filename = None

        self.selectAction = QAction(QIcon(r":\widgets\folder"), "Add Attachment", None)
        self.selectAction.triggered.connect(self._select_attachment)

    def createWidget(self, parent):
        return RoamAttachmentWidget(parent)

    def initWidget(self, widget):
        widget.attachmentloaded.connect(self.emitvaluechanged)
        widget.attachmentremoved.connect(self.emitvaluechanged)
        widget.attachmentloadrequest.connect(self.showpicker)

    def showpicker(self):
        actionpicker = PickActionDialog(msg="Select attachment")
        actionpicker.addactions(self.actions)
        actionpicker.exec_()

    @property
    def actions(self):
        yield self.selectAction

    def _select_attachment(self):
        # Show the file picker
        defaultlocation = os.path.expandvars(self.defaultlocation)
        attachment = QFileDialog.getOpenFileName(self.widget, "Select Attachment", defaultlocation)
        roam.utils.debug(attachment)
        if not attachment:
            return

        # TODO Move attachment to set folder.
        name = os.path.basename(self.filename)
        self.filename = name

        self.modified = True

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')
        # self.movetolocation = self.config.get('copyormove', True)

    def validate(self, *args):
        return self.filename is not None

    def setvalue(self, value):
        self.filename = value

    def value(self):
        return self.filename
