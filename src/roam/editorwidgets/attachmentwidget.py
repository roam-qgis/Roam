import shutil
import os
from PyQt4.QtCore import pyqtSignal, QUrl
from PyQt4.QtGui import QWidget, QAction, QIcon, QFileDialog, QPixmap, QDesktopServices

from roam.editorwidgets.core import EditorWidget, registerwidgets
from roam.editorwidgets.uifiles import ui_attachmentwidget
from roam.popupdialogs import PickActionDialog

import roam.utils


def copy_attachment(attachment, dest):
    """
    Copy the attachment to the given folder. If the file already exists the new path is returned
    but no copy happens.
    :param attachment: The path to the attachment to copy.
    :param dest: The destination folder.
    :return: The new path of the attachment.
    """
    return move_attachment(attachment, dest, copy_only=True)


def move_attachment(attachment, dest, copy_only=False):
    """
    Move the attachment to the given folder. If the file already exists the new path is returned
    but no move happens.
    :param attachment: The path to the attachment to move.
    :param dest: The destination folder.
    :return: The new path of the attachment.
    """
    if not os.path.exists(dest):
        os.makedirs(dest)
    newpath = os.path.join(dest, os.path.basename(attachment))
    if os.path.exists(newpath):
        return newpath
    if copy_only:
        shutil.copyfile(attachment, newpath)
    else:
        shutil.move(attachment, newpath)
    return newpath


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
            self.attachmentInfoLabel.setText(self.filename)
            self.attachmentImage.setPixmap(QPixmap(":/icons/view-attachment"))
        else:
            self.attachmentremoved.emit()
            self.attachmentInfoLabel.setText("")
            self.attachmentImage.setPixmap(QPixmap(":/icons/attachment"))


class AttachmentWidget(EditorWidget):
    widgettype = 'Attachment'

    def __init__(self, *args, **kwargs):
        super(AttachmentWidget, self).__init__(*args)
        self.defaultlocation = ''
        self.savelocation = ''
        self.action = True
        self.modified = False
        self.filename = None

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
        if not attachment:
            return

        if self.action == "move":
            print "Moving file"
            attachment = move_attachment(attachment, self.savelocation)
        elif self.action == "copy":
            print "Copying file"
            attachment = copy_attachment(attachment, self.savelocation)

        name = os.path.basename(attachment)
        self.filename = name
        self.widget.filename = attachment

        print "Attachment:", self.value()

        self.modified = True

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')
        self.action = self.config.get('action', 'copy')
        attachpath = os.path.join(self.context['project'].folder, "_attachments")
        self.savelocation = self.config.get('savelocation', attachpath)
        if not self.savelocation:
            self.savelocation = attachpath

    def validate(self, *args):
        return self.filename is not None

    def setvalue(self, value):
        self.filename = value

    def value(self):
        return self.filename
