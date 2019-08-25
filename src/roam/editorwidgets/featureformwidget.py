import functools

from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QToolBar, QWidget, QSizePolicy, QLabel, QIcon, QAction

from roam.popupdialogs import PickActionDialog
from roam.popupdialogs import DeleteFeatureDialog
from roam.editorwidgets.core import LargeEditorWidget
from roam.flickwidget import FlickCharm
from roam.api import featureform, RoamEvents
from roam.ui.ui_featureformwidget import Ui_Form


class FeatureFormWidget(Ui_Form, QWidget):
    # Raise the cancel event, takes a reason and a level
    canceled = pyqtSignal(str, int)
    featuresaved = pyqtSignal()
    featuredeleted = pyqtSignal()

    def __init__(self, parent=None):
        super(FeatureFormWidget, self).__init__(parent)
        self.setupUi(self)

        toolbar = QToolBar()
        size = QSize(48, 48)
        toolbar.setIconSize(size)
        style = Qt.ToolButtonTextUnderIcon
        toolbar.setToolButtonStyle(style)
        self.actionDelete = toolbar.addAction(QIcon(":/icons/delete"), "Delete")
        self.actionDelete.triggered.connect(self.delete_feature)

        label = '<b style="color:red">*</b> Required fields'
        self.missingfieldsLabel = QLabel(label)
        self.missingfieldsLabel.hide()
        self.missingfieldaction = toolbar.addWidget(self.missingfieldsLabel)

        titlespacer = QWidget()
        titlespacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(titlespacer)
        self.titlellabel = QLabel(label)
        self.titlellabel.setProperty("headerlabel", True)
        self.titlelabelaction = toolbar.addWidget(self.titlellabel)

        spacer = QWidget()
        spacer2 = QWidget()
        spacer2.setMinimumWidth(40)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        toolbar.addWidget(spacer)
        self.actionCancel = toolbar.addAction(QIcon(":/icons/cancel"), "Cancel")
        toolbar.addWidget(spacer2)
        self.actionSave = toolbar.addAction(QIcon(":/icons/save"), "Save")
        self.actionSave.triggered.connect(self.save_feature)

        self.layout().setContentsMargins(0,3, 0, 3)
        self.layout().insertWidget(0, toolbar)
        self.actiontoolbar = QToolBar()
        self.actiontoolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.actiontoolbar.addWidget(spacer)
        self.layout().insertWidget(1, self.actiontoolbar)

        self.flickwidget = FlickCharm()
        self.flickwidget.activateOn(self.scrollArea)

        self.featureform = None
        self.values = {}
        self.config = {}
        self.feature = None

    def set_featureform(self, featureform):
        """
        Note: There can only be one feature form.  If you need to show another one make a new FeatureFormWidget
        """
        self.featureform = featureform
        self.titlellabel.setText(self.featureform.windowTitle())
        self.featureform.formvalidation.connect(self._update_validation)
        self.featureform.helprequest.connect(functools.partial(RoamEvents.helprequest.emit, self))
        self.featureform.showlargewidget.connect(RoamEvents.show_widget.emit)
        self.featureform.enablesave.connect(self.actionSave.setEnabled)
        self.featureform.enablesave.connect(self.actionSave.setVisible)
        self.featureform.rejected.connect(self.canceled.emit)
        self.featureform.accepted.connect(self.featuresaved)

        actions = self.featureform.form_actions()
        if actions:
            for action in actions:
                self.actiontoolbar.addAction(action)
        else:
            self.actiontoolbar.hide()

        self.featureform.setContentsMargins(0,0,0,0)
        self.featureformarea.layout().addWidget(self.featureform)

    def delete_feature(self):
        try:
            msg = self.featureform.deletemessage
        except AttributeError:
            msg = 'Do you really want to delete this feature?'

        box = DeleteFeatureDialog(msg)

        if not box.exec_():
            return

        try:
            self.featureform.delete()
        except featureform.DeleteFeatureException as ex:
            RoamEvents.raisemessage(*ex.error)

        self.featureform.featuredeleted(self.feature)
        self.featuredeleted.emit()

    def feature_saved(self):
        self.featuresaved.emit()
        RoamEvents.featuresaved.emit()

    def save_feature(self):
        try:
            self.featureform.save()
        except featureform.MissingValuesException as ex:
            RoamEvents.raisemessage(*ex.error)
            return
        except featureform.FeatureSaveException as ex:
            RoamEvents.raisemessage(*ex.error)

        self.feature_saved()

    def set_config(self, config):
        self.config = config
        editmode = config['editmode']
        allowsave = config.get('allowsave', True)
        self.feature = config.get('feature', None)
        tools = config.get('tools', [])
        candelete = True
        if tools:
            candelete = "delete" in tools
        self.featureform.feature = self.feature
        self.featureform.editingmode = editmode
        self.actionDelete.setVisible(editmode and candelete)
        self.actionSave.setEnabled(allowsave)

    def _update_validation(self, passed):
        # Show the error if there is missing fields
        self.missingfieldaction.setVisible(not passed)

    def bind_values(self, values):
        self.values = values
        self.featureform.bindvalues(values)

    def after_load(self):
        self.featureform.loaded()

    def before_load(self):
        self.featureform.load(self.config['feature'], self.config['layers'], self.values)


class FeatureFormWidgetEditor(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        LargeEditorWidget.__init__(self, *args, **kwargs)

    def createWidget(self, parent=None):
        config = self.initconfig
        form = config['form']
        defaults = config.get('defaults', {})
        canvas = config.get('canvas', None)
        formwidget = FeatureFormWidget()
        editmode = config['editmode']
        featureform = form.create_featureform(config['feature'], defaults=defaults, canvas=canvas, editmode=editmode)
        formwidget.set_featureform(featureform)
        return formwidget

    def initWidget(self, widget, config):
        widget.actionCancel.triggered.connect(functools.partial(self.cancelform, showDialog=True))
        widget.canceled.connect(self.cancelform)
        widget.featuresaved.connect(self.emit_finished)
        widget.featuredeleted.connect(self.emit_finished)

    def cancelform(self, *args, **kwargs):
        showDialog = kwargs.get("showDialog", False)
        if showDialog:
            dlg = PickActionDialog(msg="Discard form changes?")
            self.expandAction = QAction(QIcon(":/icons/expand"), "Expand Panel", self)
            discardaction = QAction("Discard", self, triggered=self._cancel_form)
            discardaction.setObjectName("discard")
            noaction = QAction("No", self)

            dlg.addactions([noaction, discardaction])
            dlg.exec_()
        else:
            self._cancel_form(*args)

    def _cancel_form(self, *args):
        self.emit_cancel(*args)

    def updatefromconfig(self):
        self.widget.set_config(self.config)

    def before_load(self):
        self.widget.before_load()

    def value(self):
        values, savedvalues = self.widget.featureform.getvalues()
        return values

    def setvalue(self, value):
        self.widget.bind_values(value)

    def after_load(self):
        self.widget.after_load()

    def save(self):
        self.widget.save_feature()
