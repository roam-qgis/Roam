from PyQt4.QtGui import QPushButton, QIcon, QWidget

from qgis.gui import QgsMessageBarItem, QgsMessageBar

from qmap.popdialog import PopDownReport

import resources_rc
import qmap.utils

class MissingLayerItem(QgsMessageBarItem):
    def __init__(self, layers, parent=None):
        super(MissingLayerItem, self).__init__("Missing Layers")
        self.setIcon(QIcon(":/icons/sad"))
        message = "Seems like {} didn't load correctly".format(qmap.utils._pluralstring('layer', len(layers)))
        self.setText(message)
        self.setLevel(QgsMessageBar.WARNING)
        self.layers = layers
        self.report = PopDownReport(parent)
        self.button = QPushButton(self)
        self.button.setCheckable(True)
        self.button.setChecked(self.report.isVisible())
        self.button.setText("Show missing layers")
        self.button.toggled.connect(self.showError)
        self.button.toggled.connect(self.report.setVisible)
        self.setWidget(self.button)

    def hideEvent(self, event):
        self.report.hide()

    def showError(self):
        html = ["<h1>Missing Layers</h1>", "<ul>"]
        for layer in self.layers:
            html.append("<li>{}</li>".format(layer))
        html.append("</ul>")

        self.report.updateHTML("".join(html))




