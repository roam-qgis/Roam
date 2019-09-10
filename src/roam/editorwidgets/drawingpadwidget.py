from roam.editorwidgets.core import LargeEditorWidget
from roam.editorwidgets.imagewidget_utils import stamp_from_config
from roam.editorwidgets.uifiles import drawingpad


class DrawingPadWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(DrawingPadWidget, self).__init__(*args, **kwargs)
        self.canvas = kwargs.get('map', None)

    def createWidget(self, parent=None):
        pad1 = drawingpad.DrawingPad(parent=parent)
        return pad1

    def initWidget(self, widget, config):
        widget.toolStamp.pressed.connect(self.stamp_image)
        widget.actionSave.triggered.connect(self.emit_finished)
        widget.actionCancel.triggered.connect(self.emit_cancel)
        widget.canvas = self.canvas

    def stamp_image(self):
        image = self.widget.pixmap
        image = stamp_from_config(image, self.config)
        self.widget.pixmap = image

    def value(self):
        return self.widget.pixmap

    def setvalue(self, value):
        self.widget.pixmap = value