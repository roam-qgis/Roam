from PyQt4.QtGui import QSizePolicy, QWidget, QPushButton
from PyQt4.QtCore import Qt

from htmlviewer import showHTMLReport
from qgis.gui import QgsMessageBar

class BaseForm(object):
    def __init__(self, dialog, layer, feature):
        self.dialog = dialog
        self.layer = layer
        self.feature = feature

        self.bar = QgsMessageBar(dialog)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.bar.setSizePolicy(sizePolicy)
        self.dialog.layout().addWidget(self.bar)

        self.dialog.setWindowFlags(Qt.Dialog | Qt.Desktop)

    def control(self, name):
        """
        Return a control from the dialog using its name
        """
        return self.dialog.findChild(QWidget, name)

    def __getattr__(self, name):
        """
        Override __getattr__ so that we can do control lookup using . notation.
        """
        control = self.control(name)
        if control:
            return control
        else:
            raise AttributeError(name)

    def _showMessageBarError(self, message, error, extrainfo):
        """
            Show a message bar reporting a error to the user.
        """
        def showdialog():
            """
                Show the dialog with the error message
            """
            dlg = QDialog(self.dialog)
            dlg.setLayout(QGridLayout())
            text = QTextEdit()
            text.setPlainText(error + "\n\n\n\n" + extrainfo)
            dlg.layout().addWidget(text)
            dlg.exec_()

        self.errorwidget = self.bar.createMessage("Error with database",
                                                                message)
        button = QPushButton(self.errorwidget)
        button.setText("Show Error")
        button.pressed.connect(partial(showdialog))
        self.errorwidget.layout().addWidget(button)
        self.bar.pushWidget(self.errorwidget, level=QgsMessageBar.CRITICAL)


def classFactory(iface):
    from qmap import QMap
    return QMap(iface)

