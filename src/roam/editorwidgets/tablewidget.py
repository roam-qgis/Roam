from PyQt4.QtGui import QTableView, QHeaderView, QWidget, QToolBar
from PyQt4.QtCore import pyqtSignal

from roam.editorwidgets.uifiles.ui_tablewidget import Ui_tablewidget


class TableWidget(Ui_tablewidget, QWidget):
    addRecord = pyqtSignal()
    editRecord = pyqtSignal(object)

    def __init__(self, parent=None):
        super(TableWidget, self).__init__(parent)
        self.setupUi(self)
        self.table.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.addButton.pressed.connect(self.addRecord.emit)
        self.editButton.pressed.connect(self._edit_selected)

    def _edit_selected(self):
        try:
            index = self.table.selectedIndexes()[0]
        except IndexError:
            return

        model = self.table.model()
        mapkey = model.data(index)
        self.editRecord.emit(mapkey)

    def setModel(self, model):
        self.table.setModel(model)

