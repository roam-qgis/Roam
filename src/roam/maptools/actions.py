"""
Contains all the actions that are used for the map tools.  Actions are exposed to the UI
to allow the user to take different actions based on the selected map tool.
"""
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from roam.api import GPS


class BaseAction(QAction):
    def __init__(self, icon, name, tool, parent=None):
        super(BaseAction, self).__init__(icon, name, parent)
        self.setCheckable(False)
        self.tool = tool
        self.isdefault = False
        self.ismaptool = False


class UndoAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(UndoAction, self).__init__(QIcon(":/icons/back"),
                                         "Undo",
                                         tool,
                                         parent)
        self.setObjectName("UndoAction")
        self.setText(self.tr("Undo"))


class EndCaptureAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(EndCaptureAction, self).__init__(QIcon(":/icons/stop-capture"),
                                               "End Capture",
                                               tool,
                                               parent)
        self.setObjectName("EndCaptureAction")
        self.setText(self.tr("End Capture"))

    def setEditing(self, editing):
        if editing:
            self.setText(self.tr("End Edit"))
        else:
            self.setText(self.tr("End Capture"))


class CaptureAction(BaseAction):
    def __init__(self, tool, geomtype, parent=None, text="Digitize"):
        self._defaulticon = QIcon(":/icons/capture-{}".format(geomtype))
        self._defaulttext = text
        super(CaptureAction, self).__init__(self._defaulticon,
                                            self._defaulttext,
                                            tool,
                                            parent)
        self.setObjectName("CaptureAction")
        self.setCheckable(True)
        self.isdefault = True
        self.ismaptool = True

    def setEditMode(self, enabled):
        if enabled:
            self.setText(self.tr("Edit"))
        else:
            self.setText(self._defaulttext)


class GPSTrackingAction(BaseAction):
    def __init__(self, tool, parent=None):
        super(GPSTrackingAction, self).__init__(QIcon(":/icons/record"),
                                                "Track",
                                                tool,
                                                parent)
        self.setObjectName("GPSTrackingAction")
        self.setCheckable(True)

    def set_text(self, tracking):
        if tracking:
            self.setText(self.tr("Tracking"))
        else:
            self.setText(self.tr("Track"))


class GPSCaptureAction(BaseAction):
    def __init__(self, tool, geomtype, parent=None):
        super(GPSCaptureAction, self).__init__(QIcon(":/icons/gpsadd-{}".format(geomtype)),
                                               "GPS Capture",
                                               tool,
                                               parent)
        self.setObjectName("GPSCaptureAction")
        self.setText(self.tr("GPS Point"))
        self.setEnabled(False)

        GPS.gpsfixed.connect(self.setstate)
        GPS.gpsdisconnected.connect(lambda: self.setEnabled(False))

    def setstate(self, fixed, *args):
        self.setEnabled(fixed)

