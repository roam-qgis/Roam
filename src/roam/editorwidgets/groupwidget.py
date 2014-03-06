from PyQt4.QtGui import QGroupBox

from roam.editorwidgets.core import EditorWidget

class GroupWidget(EditorWidget):
    widgettype = 'Group'
    isgroup = True

    def __init__(self, *args, **kwargs):
        super(GroupWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return QGroupBox(parent)

    def initWidget(self, widget):
        self.setTitle(self.label)


