from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QDialog, QApplication

from uifiles import featurefeature_dialog


class DeleteFeatureDialog(featurefeature_dialog, QDialog):
    def __init__(self, parent=None):
        super(DeleteFeatureDialog, self).__init__(parent, Qt.FramelessWindowHint)
        self.setupUi(self)
        self.setModal(True)

    def showEvent(self, event):
        self.resizetoparent()

    def resizetoparent(self):
        width = self.parent().width()
        self.resize(width, self.sizeHint().height())
        y = self.parent().y()
        y += self.parent().height() / 2
        self.move(self.parent().pos().x(), y)

