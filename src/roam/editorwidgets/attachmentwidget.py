import shutil
import os
from qgis.core import QgsExpression
from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.PyQt.QtWidgets import QWidget, QAction, QFileDialog
from qgis.PyQt.QtGui import QIcon, QPixmap, QDesktopServices

from roam.editorwidgets.core import EditorWidget, registerwidgets
from roam.editorwidgets.uifiles import ui_attachmentwidget
from roam.popupdialogs import PickActionDialog

import roam.utils


def copy_attachment(attachment, dest, filename=None):
    """
    Copy the attachment to the given folder. If the file already exists the new path is returned
    but no copy happens.
    :param attachment: The path to the attachment to copy.
    :param dest: The destination folder.
    :return: The new path of the attachment.
    """
    return move_attachment(attachment, dest, filename=filename, copy_only=True)


def move_attachment(attachment, dest, filename=None, copy_only=False):
    """
    Move the attachment to the given folder. If the file already exists the new path is returned
    but no move happens.
    :param attachment: The path to the attachment to move.
    :param dest: The destination folder.
    :return: The new path of the attachment.
    """
    if not os.path.exists(dest):
        os.makedirs(dest)
    if not filename:
        name = os.path.basename(attachment)
    else:
        # Use the new name and the ext from the old file.
        name = filename + os.path.splitext(attachment)[1]

    newpath = os.path.join(dest, name)
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
        if not self.valid:
            self.attachmentloadrequest.emit()
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.filename))

    @property
    def filename(self):
        return self._filename

    @property
    def valid(self):
        value = self.filename
        return value is not None and value != "" and not os.path.isdir(value)

    @filename.setter
    def filename(self, value):
        self._filename = value
        self.selectbutton.setVisible(self.valid)
        self.deletebutton.setVisible(self.valid)
        if self.valid:
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
        self.customname = ''
        self.action = True
        self.modified = False
        self.filename = None

    def createWidget(self, parent):
        return RoamAttachmentWidget(parent)

    def initWidget(self, widget, config):
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

        name = None
        # If there is a custom name set we eval it in the context of a QgsExpression
        if self.customname:
            feature = self.context['featureform'].to_feature()
            name = QgsExpression(self.customname).evaluate(feature)

        if self.action == "move":
            attachment = move_attachment(attachment, self.savelocation, filename=name)
        elif self.action == "copy":
            attachment = copy_attachment(attachment, self.savelocation, filename=name)

        self.widget.filename = attachment
        name = os.path.basename(attachment)
        self.filename = name

        self.modified = True

    def updatefromconfig(self):
        self.defaultlocation = self.config.get('defaultlocation', '')
        self.action = self.config.get('action', 'copy')
        self.customname = self.config.get('nameformat', '')
        attachpath = os.path.join(self.context['project'].folder, "_attachments")
        self.savelocation = self.config.get('savelocation', attachpath)
        if not self.savelocation:
            self.savelocation = attachpath

    def validate(self, *args):
        return self.filename is not None

    def setvalue(self, value):
        self.filename = value
        if not value:
            value = ''

        if os.path.isabs(value):
            self.widget.filename = value
        else:
            self.widget.filename = os.path.join(self.savelocation, value)

    def value(self):
        return self.filename
