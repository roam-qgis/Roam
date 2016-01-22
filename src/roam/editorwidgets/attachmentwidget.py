import os
from PyQt4.QtCore import pyqtSignal, QUrl
from PyQt4.QtGui import QWidget, QAction, QIcon, QFileDialog, QPixmap, QDesktopServices

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
        self._filename = None
        self.selectbutton.setVisible(False)
        self.deletebutton.setVisible(False)

        self.setStyleSheet(":hover {background-color: #dddddd;}")
        self.selectbutton.clicked.connect(self.attachmentloadrequest.emit)
        self.deletebutton.clicked.connect(self.removeAttachment)
        self.attachmentImage.mouseReleaseEvent = self.attach

    def removeAttachment(self):
        self.attachmentremoved.emit()
        self.filename = None

    def attach(self, event):
        if self.isDefault:
            self.attachmentloadrequest.emit()
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.filename))

    @property
    def isDefault(self):
        return self.filename is None

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value
        self.selectbutton.setVisible(value is not None)
        self.deletebutton.setVisible(value is not None)
        if value:
            self.attachmentloaded.emit()
            # TODO Add some generic file icons here.
        else:
            self.attachmentremoved.emit()
            self.attachmentImage.setPixmap(QPixmap(":/widgets/add"))


class AttachmentWidget(EditorWidget):
    widgettype = 'Attachment'

    def __init__(self, *args, **kwargs):
        super(AttachmentWidget, self).__init__(*args)
        self.defaultlocation = ''
        self.savelocation = ''
        self.action = True
        self.modified = False
        self.filename = None

        # self.selectAction = QAction(QIcon(r":\widgets\folder"), "Add Attachment", None)
        # self.selectAction.triggered.connect(self._select_attachment)

    def createWidget(self, parent):
        return RoamAttachmentWidget(parent)

    def initWidget(self, widget):
        widget.attachmentloaded.connect(self.emitvaluechanged)
        widget.attachmentremoved.connect(self.emitvaluechanged)
        widget.attachmentloadrequest.connect(self._select_attachment)

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
        if self.action == "move":
            print "Moving file"
        elif self.action == "copy":
            print "Copying file"

        name = os.path.basename(attachment)
        self.filename = name
        self.widget.filename = attachment

        print "Attachment:", self.value()

        self.modified = True

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')
        self.action = self.config.get('action', 'copy')
        self.savelocation = self.config.get('savelocation', '')

    def validate(self, *args):
        return self.filename is not None

    def setvalue(self, value):
        self.filename = value

    def value(self):
        return self.filename
