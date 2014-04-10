from PyQt4.QtCore import Qt, QSize
from PyQt4.QtGui import QDialog, QToolButton, QApplication

from roam.ui.uifiles import featurefeature_dialog
from roam.ui.uifiles import actionpicker_widget

class Dialogbase(QDialog):
    def __init__(self, msg=None, parent=None):
        if parent is None:
            parent = QApplication.activeWindow()

        super(Dialogbase, self).__init__(parent, Qt.FramelessWindowHint)
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

class DeleteFeatureDialog(featurefeature_dialog, Dialogbase):
    def __init__(self, msg=None, parent=None):
        super(DeleteFeatureDialog, self).__init__(msg, parent)
        if msg:
            self.deletelabel.setText(msg)

class PickActionDialog(actionpicker_widget, Dialogbase):
    def __init__(self, msg=None, parent=None):
        super(PickActionDialog, self).__init__(msg, parent)
        if msg:
            self.label.setText(msg)

    def addAction(self, action):
        button = QToolButton()
        button.setIconSize(QSize(64,64))
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        action.triggered.connect(self.close)

        self.actionsLayout.addWidget(button)


    def addactions(self, actions):
        for action in actions:
            self.addAction(action)
