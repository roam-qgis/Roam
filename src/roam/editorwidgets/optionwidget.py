from PyQt4.QtCore import QSize
from PyQt4.QtGui import QIcon, QPushButton, QWidget, QHBoxLayout, QButtonGroup

from roam.editorwidgets.core import EditorWidget


class OptionWidget(EditorWidget):
    widgettype = 'Option Row'

    def __init__(self, *args):
        super(OptionWidget, self).__init__(*args)
        self._bindvalue = None
        self.group = QButtonGroup()
        self.group.setExclusive(True)
        self.group.buttonClicked.connect(self.emitvaluechanged)

    def createWidget(self, parent):
        widget = QWidget(parent)
        return widget

    def _buildfromlist(self, listconfig):
        items = listconfig['items']
        for item in items:
            parts = item.split(';')
            data = parts[0]
            try:
                desc = parts[1]
            except IndexError:
                desc = data

            button = QPushButton()

            icon = QIcon()
            try:
                path = parts[2]
                if path.startswith("#"):
                    # Colour the button with the hex value
                    style = """
                        QPushButton:checked  {{
                            border: 3px solid rgb(137, 175, 255);
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
            self.widget.layout().addWidget(button)
            self.group.addButton(button)

    def initWidget(self, widget):
        if not widget.layout():
            widget.setLayout(QHBoxLayout())
            widget.layout().setContentsMargins(0, 0, 0, 0)

    def updatefromconfig(self):
        super(OptionWidget, self).updatefromconfig()

        for button in self.group.buttons():
            self.group.removeButton(button)
            self.widget.layout().removeWidget(button)
            button.deleteLater()
            button.setParent(None)

        listconfig = self.config['list']
        self._buildfromlist(listconfig)

        super(OptionWidget, self).endupdatefromconfig()

    def validate(self, *args):
        button = self.group.checkedButton()
        if button:
            return True

        return False

    @property
    def nullvalues(self):
        return ['NULL']

    def setvalue(self, value):
        if value in self.nullvalues:
            value = None

        for button in self.group.buttons():
            buttonvalue = button.property("value")
            if (value is None and buttonvalue in self.nullvalues) or buttonvalue == str(value):
                button.setChecked(True)
                self.emitvaluechanged()
                return

    def value(self):
        button = self.group.checkedButton()
        if not button:
            return None

        value = button.property("value")

        if value in self.nullvalues:
            value = None
        return value


