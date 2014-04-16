from PyQt4.QtCore import QModelIndex, pyqtSignal, QSize
from PyQt4.QtGui import QWidget

from roam.flickwidget import FlickCharm
from roam.ui.ui_list import Ui_BigList


class BigList(Ui_BigList, QWidget):
    itemselected = pyqtSignal(QModelIndex)

    def __init__(self, parent=None):
        super(BigList, self).__init__(parent)
        self.setupUi(self)
        self.listView.clicked.connect(self.itemselected)
        self.charm = FlickCharm()
        self.charm.activateOn(self.listView)

    def setmodel(self, model):
        self.listView.setModel(model)

    def setlabel(self, fieldname):
        self.fieldnameLabel.setText(fieldname)

    def show(self):
        super(BigList, self).show()

        width = self.parent().width()
        height = self.parent().height()
        self.move(width / 4, 0)
        self.resize(QSize(width / 2, height))


