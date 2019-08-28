import math
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QPushButton, QWidget, QHBoxLayout, QButtonGroup, QVBoxLayout, QGridLayout, QBoxLayout
from qgis.PyQt.QtGui import QIcon

from roam.editorwidgets.core import EditorWidget


class OptionWidget(EditorWidget):
    widgettype = 'Option Row'

    def __init__(self, *args, **kwargs):
        super(OptionWidget, self).__init__(*args, **kwargs)
        self._bindvalue = None
        self.group = QButtonGroup()
        self.group.buttonClicked.connect(self.emitvaluechanged)

    def createWidget(self, parent=None):
        widget = QWidget(parent)
        return widget

    def _buildfromlist(self, listconfig, multiselect):
        def chunks(l, n):
            """ Yield successive n-sized chunks from l.
            """
            for i in range(0, len(l), n):
                yield l[i:i + n]

        items = listconfig['items']
        wrap = self.config.get('wrap', 0)
        showcolor = self.config.get('always_color', False)
        if wrap > 0:
            rows = list(chunks(items, wrap))
        else:
            rows = [items]

        for rowcount, row in enumerate(rows):
            for column, item in enumerate(row):
                parts = item.split(';')
                data = parts[0]
                try:
                    desc = parts[1]
                except IndexError:
                    desc = data

                button = QPushButton()
                button.setCheckable(multiselect)
                self.group.setExclusive(not multiselect)

                icon = QIcon()
                try:
                    path = parts[2]
                    if path.startswith("#"):
                        # Colour the button with the hex value.
                        # If show color is enabled we always show the color regardless of selection.
                        if not showcolor:
                            style = """
                                QPushButton::checked {{
                                    border: 3px solid rgb(137, 175, 255);
                                    background-color: {colour};
                                }}""".format(colour=path)
                        else:
                            style = """
                                QPushButton::checked {{
                                    border: 3px solid rgb(137, 175, 255);
                                }}
                                QPushButton {{
                                    background-color: {colour};
                                }}""".format(colour=path)
                        button.setStyleSheet(style)
                    elif path.endswith("_icon"):
                        icon = QIcon(":/icons/{}".format(path))
                    else:
                        icon = QIcon(path)
                except:
                    icon = QIcon()

                button.setCheckable(True)
                button.setText(desc)
                button.setProperty("value", data)
                button.setIcon(icon)
                button.setIconSize(QSize(24, 24))
                if isinstance(self.widget.layout(), QBoxLayout):
                    self.widget.layout().addWidget(button)
                else:
                    self.widget.layout().addWidget(button, rowcount, column)
                self.group.addButton(button)

    def initWidget(self, widget, config):
        if not widget.layout():
            widget.setLayout(QGridLayout())
            widget.layout().setContentsMargins(0, 0, 0, 0)

    def updatefromconfig(self):
        super(OptionWidget, self).updatefromconfig()

        for button in self.group.buttons():
            self.group.removeButton(button)
            self.widget.layout().removeWidget(button)
            button.deleteLater()
            button.setParent(None)

        listconfig = self.config['list']
        multiselect = self.config.get('multi', False)
        self._buildfromlist(listconfig, multiselect)

        super(OptionWidget, self).endupdatefromconfig()

    def validate(self, *args):
        button = self.group.checkedButton()
        if button:
            return True

        return False

    @property
    def buttons(self):
        return self.group.buttons()

    @property
    def nullvalues(self):
        return ['NULL']

    @property
    def multioption(self):
        return self.config.get('multi', False)

    def setvalue(self, value):
        def set_button(setvalue):
            for button in self.group.buttons():
                buttonvalue = button.property("value")
                if (setvalue is None and buttonvalue in self.nullvalues) or buttonvalue == str(setvalue):
                    button.setChecked(True)
                    self.emitvaluechanged()
                    return

        if value in self.nullvalues:
            value = None

        if self.multioption and value:
            values = value.split(';')
        else:
            values = [value]

        for value in values:
            set_button(value)

    def value(self):
        def _returnvalue():
            if self.multioption:
                _values = []
                checked = [button for button in self.group.buttons() if button.isChecked()]
                for button in checked:
                    value = button.property("value")
                    _values.append(value)
                if not _values:
                    return None
                return ";".join(_values)
            else:
                checked = self.group.checkedButton()
                if not checked:
                    return None

                value = checked.property("value")
                return value

        returnvalue = _returnvalue()

        if returnvalue in self.nullvalues:
            returnvalue = None

        return returnvalue
