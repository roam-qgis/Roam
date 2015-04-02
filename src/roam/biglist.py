from PyQt4.QtCore import QModelIndex, pyqtSignal, QSize, Qt
from PyQt4.QtGui import QWidget, QDialog, QSortFilterProxyModel

from roam.flickwidget import FlickCharm
from roam.ui.ui_list import Ui_BigList


class BigList(Ui_BigList, QWidget):
    itemselected = pyqtSignal(QModelIndex)
    closewidget = pyqtSignal()
    savewidget = pyqtSignal()

    def __init__(self, parent=None, centeronparent=False, showsave=True):
        super(BigList, self).__init__(parent)
        self.setupUi(self)
        self.centeronparent = centeronparent
        self.listView.clicked.connect(self.selected)
        self.saveButton.pressed.connect(self.savewidget.emit)
        self.closebutton.pressed.connect(self.closewidget.emit)
        self._index = None
        self.search.textEdited.connect(self.set_filter)
        self.filtermodel = QSortFilterProxyModel()
        self.filtermodel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.listView.setModel(self.filtermodel)

        self.charm = FlickCharm()
        self.charm.activateOn(self.listView)

        self.saveButton.setVisible(showsave)

    def set_filter(self, text):
        self.filtermodel.setFilterRegExp(text + ".*")

    def selected(self, index):
        self._index = index
        self._index = self.filtermodel.mapToSource(index)
        self.itemselected.emit(self._index)

    def setmodel(self, model):
        self.filtermodel.setSourceModel(model)

    def setlabel(self, fieldname):
        self.fieldnameLabel.setText(fieldname)

    def currentindex(self):
        return self._index

    def setcurrentindex(self, index):
        if index is None:
            index = QModelIndex()
        if isinstance(index, int):
            index = self.listView.model().index(index, 0)
        self.listView.setCurrentIndex(index)

    def show(self):
        super(BigList, self).show()

        if self.centeronparent:
            width = self.parent().width()
            height = self.parent().height()
            self.move(width / 4, 0)
            self.resize(QSize(width /2, height))

