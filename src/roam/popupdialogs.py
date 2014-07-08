from PyQt4.QtCore import Qt, QSize, QEvent
from PyQt4.QtGui import QDialog, QToolButton, QApplication, QWidget

from roam.ui.ui_deletefeature import Ui_DeleteFeatureDialog
from roam.ui.ui_actionpicker import Ui_ActionPickerDialog
from roam.ui.ui_actionpickerwidget import Ui_actionpicker

class Dialogbase(QDialog):
    def __init__(self, parent=None):
        if parent is None:
            parent = QApplication.activeWindow()

        super(Dialogbase, self).__init__(parent, Qt.FramelessWindowHint)

        self.setupUi(self)
        self.setModal(True)
        self.parent().installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.resizetoparent()
        elif event.type() == QEvent.MouseButtonPress:
            self.close()
        return object.eventFilter(object, event)

    def showEvent(self, event):
        self.resizetoparent()

    def resizetoparent(self):
        width = self.parent().width()
        self.resize(width, self.sizeHint().height())
        y = self.parent().y()
        y += self.parent().height() / 2
        half = self.height() / 2
        self.move(self.parent().geometry().x(), y - half)

    def mousePressEvent(self, *args, **kwargs):
        self.close()

class DeleteFeatureDialog(Ui_DeleteFeatureDialog, Dialogbase):
    def __init__(self, msg=None, parent=None):
        super(DeleteFeatureDialog, self).__init__(parent)
        if msg:
            self.deletelabel.setText(msg)

class ActionPickerWidget(Ui_actionpicker, QWidget):
    def __init__(self, parent=None):
        super(ActionPickerWidget, self).__init__(parent)
        self.setupUi(self)

    def setTile(self, title):
        self.label.setText(title)

    def addAction(self, action):
        button = QToolButton(self)
        button.setProperty("action", True)
        button.setIconSize(QSize(64,64))
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)

        self.actionsLayout.addWidget(button)

    def addactions(self, actions):
        for action in actions:
            self.addAction(action)

class PickActionDialog(Ui_ActionPickerDialog, Dialogbase):
    def __init__(self, msg=None, parent=None):
        super(PickActionDialog, self).__init__(parent)
        if msg:
            self.label.setText(msg)

    def addAction(self, action):
        button = QToolButton(self)
        button.setProperty("action", True)
        button.setIconSize(QSize(64,64))
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        action.triggered.connect(self.close)

        self.actionsLayout.addWidget(button)


    def addactions(self, actions):
        for action in actions:
            self.addAction(action)
