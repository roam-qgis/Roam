"""
RoamEvents is an event sink for common signals used though out Roam.

These can be raised and handled anywhere in the application.
"""
from PyQt4.QtCore import pyqtSignal, QObject, QUrl
from PyQt4.QtGui import QWidget

from qgis.core import QgsFeature, QgsPoint

class _Events(QObject):
    # Emit when you need to open a image in the main window

    INFO = 0
    WARNING = 1
    CRITICAL = 2
    SUCCESS = 3

    openimage = pyqtSignal(object)

    #Emit to open a url
    openurl = pyqtSignal(QUrl)

    # Emit when requesting to open a feature form.
    openfeatureform = pyqtSignal(object, QgsFeature, bool, bool, object, object)
    deletefeature = pyqtSignal(object, QgsFeature)

    snappingChanged = pyqtSignal(bool)

    def delete_feature(self, form, feature):
        self.deletefeature.emit(form, feature)

    def load_feature_form(self, form, feature, editmode, clearcurrent=True, callback=None, cancel_callback=None):
        """
        Load a form into the data entry tab.
        :param form: The Form to load. See roam.project.Form
        :param feature: Feature to load
        :param editmode: Open in edit mode
        :param clearcurrent: Clear the current stack of open widgets.
        """
        self.openfeatureform.emit(form, feature, editmode, clearcurrent, callback, cancel_callback)

    editgeometry = pyqtSignal(object, QgsFeature)

    editgeometry_complete = pyqtSignal(object, QgsFeature)

    # Emit when you need to open the on screen keyboard
    openkeyboard = pyqtSignal()

    selectioncleared = pyqtSignal()
    selectionchanged = pyqtSignal(dict)
    activeselectionchanged = pyqtSignal(object, QgsFeature, list)

    projectloaded = pyqtSignal(object)
    closeProject = pyqtSignal(object)
    projectClosing = pyqtSignal()
    projectClosed = pyqtSignal(object)

    helprequest = pyqtSignal(QWidget, str)

    onShowMessage = pyqtSignal(str, str, int, int, str)

    featuresaved = pyqtSignal()

    ## Raised when a form is saved in the application.
    ## Args are: Form, QgsFeature
    formSaved = pyqtSignal(object, object)

    sync_complete = pyqtSignal()

    def close_project(self, project=None):
        self.closeProject.emit(project)

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
