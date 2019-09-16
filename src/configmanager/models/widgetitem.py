from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QIcon, QFont

from configmanager.icons import widgeticon


class WidgetItem(QStandardItem):
    def __init__(self, widget):
        super(WidgetItem, self).__init__()
        self.widget = widget
        self.setDropEnabled(False)

    def flags(self):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        if self.iscontainor():
            flags |= Qt.ItemIsDropEnabled
        return flags

    def setData(self, value, role=None):
        if role == Qt.UserRole:
            self.widget = value

        super(WidgetItem, self).setData(value, role)

    @property
    def field(self):
        return self.widget.get('field', '')

    @property
    def id(self):
        return self.widget.get('_id', '')

    def data(self, role):
        if role == Qt.DisplayRole:
            name = self.widget.get('name', None)
            if self.iscontainor():
                length = len(self.widget.get('config', {}).get('widgets', []))
                return "{} ({} items)".format(name, length)

            if self.is_section:
                return "Section - {}".format(name)

            field = (self.widget.get('field', '') or '').lower()
            text = name or field
            return "{} ({})".format(text, self.widget['widget'])
        elif role == Qt.UserRole:
            return self.widget
        elif role == Qt.DecorationRole:
            if self.is_section:
                return QIcon(":/icons/Section")
            return widgeticon(self.widget['widget'])
        elif role == Qt.FontRole:
            if self.is_section:
                font = QFont()
                font.setBold(True)
                return font

    def iscontainor(self):
        return self.widget['widget'] == 'Group'

    @property
    def is_section(self):
        return self.widget['widget'] == 'Section'

    def loadchildren(self):
        if not self.iscontainor():
            return

        for widget in self.widget['config'].get('widgets', []):
            item = WidgetItem(widget)
            if item.iscontainor():
                item.loadchildren()
            self.appendRow(item)

    def getwidget(self):
        if self.iscontainor():
            # If this is a group then loop over all the sub items.
            rows = self.rowCount()
            widgets = self.widget['config']['widgets'] = []
            for row in range(rows):
                item = self.child(row, 0)
                widgets.append(item.getwidget())

        return self.widget