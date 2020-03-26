import yaml
from PyQt5.QtCore import Qt, QMimeData, QByteArray
from PyQt5.QtGui import QStandardItemModel

from configmanager.models import WidgetItem


class WidgetsModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(WidgetsModel, self).__init__(parent)

    def widgets(self):
        """
        Return the widgets in the model in a list.
        """
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            yield item.getwidget()

    def addwidget(self, widget, parent):
        item = WidgetItem(widget)
        if not parent.isValid():
            self.invisibleRootItem().appendRow(item)
        else:
            parentitem = self.itemFromIndex(parent)
            parentitem.appendRow(item)

        index = self.indexFromItem(item)
        return index

    def loadwidgets(self, widgets):
        """
        Load the widgets into the model.
        """
        for widget in widgets:
            item = WidgetItem(widget)
            if item.iscontainor():
                item.loadchildren()
            self.invisibleRootItem().appendRow(item)

    def idFromIndex(self, index):
        item = self.item(index, 0)
        return item.id

    def indexFromId(self, id):
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item.id == id:
                return row

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsDropEnabled

        item = self.itemFromIndex(index)
        return item.flags()

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-roamwidget"]

    def mimeData(self, indexes):
        data = QMimeData()
        widgets = []
        for index in indexes:
            widget = index.data(Qt.UserRole)
            widgets.append(widget)

        widgettext = yaml.dump(widgets).encode("utf-8")
        _bytes = QByteArray(widgettext)
        data.setData(self.mimeTypes()[0], _bytes)
        return data

    def dropMimeData(self, mimedata, action, row, column, parent):
        data = mimedata.data(self.mimeTypes()[0]).data()
        data = data.decode("utf-8")
        widgets = yaml.load(data)

        droptarget = self.itemFromIndex(parent)
        if not droptarget:
            droptarget = self.invisibleRootItem()

        if row == -1:
            row = droptarget.rowCount()

        for widget in widgets:
            item = WidgetItem(widget)
            if getattr(droptarget, "iscontainor", False):
                droptarget.appendRow(item)
            else:
                # This isn't fully right but seems to work...
                # self.beginMoveRows(parent, 0, 0, parent, row)
                droptarget.insertRow(row, item)
                # self.endMoveRows()
            # item.loadchildren()

        return True