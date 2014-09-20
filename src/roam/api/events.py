"""
RoamEvents is an event sink for common signals used though out Roam.

These can be raised and handled anywhere in the application.
"""
from PyQt4.QtCore import pyqtSignal, QObject, QUrl
from PyQt4.QtGui import QWidget

from qgis.core import QgsFeature, QgsPoint

class _Events(QObject):
    # Emit when you need to open a image in the main window
    openimage = pyqtSignal(object)

    #Emit to open a url
    openurl = pyqtSignal(QUrl)

    # Emit when requesting to open a feature form.
    openfeatureform = pyqtSignal(object, QgsFeature, bool, bool, object)

    def load_feature_form(self, form, feature, editmode, clearcurrent=True, callback=None):
        """
        Load a form into the data entry tab.
        :param form: The Form to load. See roam.project.Form
        :param feature: Feature to load
        :param editmode: Open in edit mode
        :param clearcurrent: Clear the current stack of open widgets.
        """
        self.openfeatureform.emit(form, feature, editmode, clearcurrent, callback)

    editgeometry = pyqtSignal(object, QgsFeature)

    editgeometry_complete = pyqtSignal(object, QgsFeature)

    # Emit when you need to open the on screen keyboard
    openkeyboard = pyqtSignal()

    selectioncleared = pyqtSignal()
    selectionchanged = pyqtSignal(dict)

    projectloaded = pyqtSignal(object)

    helprequest = pyqtSignal(QWidget, str)

    onShowMessage = pyqtSignal(str, str, int, int, str)

    featuresaved = pyqtSignal()

    def raisemessage(self, title, message, level=0, duration=0, extra=''):
        """
        Raise a message for Roam to show.
        :param title: The title of the message.
        :param message: The message body
        :param level:
        :param time: How long the message should be shown for.
        :param extra: Any extra information to show the user on click.
        """
        self.onShowMessage.emit(title, message, level, duration, extra)

    show_widget = pyqtSignal(object, object, object, dict)


RoamEvents = _Events()
