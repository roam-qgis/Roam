import qgis.core
from qgis.PyQt.QtCore import QSize, Qt, QEvent
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel, QIcon
from qgis.PyQt.QtWidgets import QComboBox
from qgis.core import QgsProject, QgsExpression, QgsFeatureRequest

import roam.utils
from roam.api import RoamEvents, utils
from roam.biglist import BigList
from roam.editorwidgets.core import EditorWidget
from roam.editorwidgets.core.largeeditorwidgetbase import LargeEditorWidget


def nullconvert(value):
    if value == qgis.core.NULL:
        return None
    return value


class BigListWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(BigListWidget, self).__init__(*args, **kwargs)
        self.setObjectName("biglist")
        self.multi = False
        self.startState = []
        self.model = None

    def eventFilter(self, object, event):
        if event.type() in [QEvent.FocusIn, QEvent.MouseButtonPress]:
            RoamEvents.openkeyboard.emit()
        return False

    def createWidget(self, parent):
        return BigList(parent)

    def initWidget(self, widget, config, **kwargs):
        widget.itemselected.connect(self.selectitems)
        widget.closewidget.connect(self.canceled)
        widget.savewidget.connect(self.emit_finished)
        widget.search.installEventFilter(self)

    def canceled(self):
        if self.model:
            # Clear the model and reset the state
            for state in self.startState:
                item = self.model.item(state[0])
                item.setCheckState(state[1])

        self.emit_cancel()

    def selectitems(self):
        if not self.multi:
            self.emit_finished()

    def updatefromconfig(self):
        super(BigListWidget, self).updatefromconfig()
        model = self.config['model']
        self.model = model
        label = self.config['label']
        self.multi = self.config.get('multi', False)
        if not self.multi:
            self.widget.saveButton.hide()
        self.widget.setlabel(label)
        self.widget.setmodel(model)
        # HACK: This is a gross hack because we are sharing state between this model and the
        #       and the caller.
        self.startItems = []
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            self.startState.append((row, item.checkState()))

        self.endupdatefromconfig()

    def setvalue(self, value):
        self.widget.setcurrentindex(value)

    def value(self):
        return self.widget.currentindex()


class ListWidget(EditorWidget):
    widgettype = 'List'

    def __init__(self, *args, **kwargs):
        super(ListWidget, self).__init__(*args, **kwargs)
        self.listmodel = QStandardItemModel()
        self._bindvalue = None

    def createWidget(self, parent):
        return QComboBox(parent)

    def _buildfromlist(self, widget, listconfig):
        items = listconfig['items']
        for item in items:
            parts = item.split(';')
            data = parts[0]
            try:
                desc = parts[1]
            except IndexError:
                desc = data

            try:
                path = parts[2]
                path = path.strip()
                icon = QIcon(path)
            except:
                icon = QIcon()

            item = QStandardItem(desc)
            item.setData(data, Qt.UserRole)
            item.setIcon(icon)
            self.listmodel.appendRow(item)

    def _buildfromlayer(self, widget, layerconfig):
        layername = layerconfig['layer']
        keyfield = layerconfig['key']
        valuefield = layerconfig['value']
        filterexp = layerconfig.get('filter', None)

        try:
            layer = utils.layer_by_name(layername)
        except IndexError:
            roam.utils.warning("Can't find layer {} in project".format(layername))
            return

        keyfieldindex = layer.fields().lookupField(keyfield)
        valuefieldindex = layer.fields().lookupField(valuefield)
        if keyfieldindex == -1 or valuefieldindex == -1:
            roam.utils.warning(f"Can't find key or value column for widget "
                               f"Id: {self.id} "
                               f"Layer: {layername} "
                               f"Key: {keyfield} - {keyfieldindex} "
                               f"Value: {valuefield} - {valuefieldindex} ")
            return

        if self.allownulls:
            item = QStandardItem('(no selection)')
            item.setData(None, Qt.UserRole)
            self.listmodel.appendRow(item)

        fields = [keyfieldindex, valuefieldindex]
        iconfieldindex = layer.fields().lookupField('icon')
        if iconfieldindex > -1:
            fields.append("icon")

        if not filterexp and valuefieldindex == keyfieldindex and iconfieldindex == -1:
            values = layer.uniqueValues(keyfieldindex)
            values = sorted(values)
            for value in values:
                value = nullconvert(value)
                item = QStandardItem(value)
                item.setData(value, Qt.UserRole)
                self.listmodel.appendRow(item)
            return

        features = roam.api.utils.search_layer(layer, filterexp, fields, with_geometry=False)
        # Sort the fields based on value field
        features = sorted(features, key=lambda f: f[valuefield])
        for feature in features:
            keyvalue = nullconvert(feature[keyfieldindex])
            valuvalue = nullconvert(feature[valuefield])
            try:
                path = feature["icon"]
                icon = QIcon(path)
            except KeyError:
                icon = QIcon()

            item = QStandardItem(keyvalue)
            item.setData(str(valuvalue), Qt.UserRole)
            item.setIcon(icon)
            self.listmodel.appendRow(item)

    def initWidget(self, widget, config):
        if widget.isEditable():
            widget.editTextChanged.connect(self.emitvaluechanged)

        widget.currentIndexChanged.connect(self.emitvaluechanged)
        widget.setModel(self.listmodel)
        widget.showPopup = self.showpopup
        widget.setIconSize(QSize(24, 24))
        widget.setStyleSheet(
            "QComboBox::drop-down {border-width: 0px;} QComboBox::down-arrow {image: url(noimg); border-width: 0px;}")
        widget.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)

    def showpopup(self):
        if self.listmodel.rowCount() == 0:
            return

        self.largewidgetrequest.emit(BigListWidget, self.widget.currentIndex(),
                                     self._biglistitem, dict(model=self.listmodel,
                                                             label=self.labeltext))

    def updatefromconfig(self):
        super(ListWidget, self).updatefromconfig()

        self.listmodel.clear()
        if 'list' in self.config:
            listconfig = self.config['list']
            self._buildfromlist(self.widget, listconfig)
        elif 'layer' in self.config:
            layerconfig = self.config['layer']
            self._buildfromlayer(self.widget, layerconfig)

        super(ListWidget, self).endupdatefromconfig()

    @property
    def allownulls(self):
        return self.config.get('allownull', False)

    def validate(self, *args):
        if (not self.widget.currentText() == '' and not self.widget.currentText() == "(no selection)"):
            return True
        else:
            return False

    def _biglistitem(self, index):
        self.widget.setCurrentIndex(index.row())

    def setvalue(self, value):
        self._bindvalue = value
        index = self.widget.findData(value)
        self.widget.setCurrentIndex(index)
        if index == -1 and self.widget.isEditable():
            if value is None and not self.config['allownull']:
                return

            self.widget.addItem(str(value))
            index = self.widget.count() - 1
            self.widget.setCurrentIndex(index)

    def value(self):
        index = self.widget.currentIndex()
        value = self.widget.itemData(index)
        text = self.widget.currentText()
        if value is None and self.widget.isEditable() and not text == '(no selection)':
            return self.widget.currentText()

        return value


class MultiList(ListWidget):
    widgettype = 'MultiList'

    def __init__(self, *args, **kwargs):
        super(MultiList, self).__init__(*args)
        self.multi = True

    def updatefromconfig(self):
        super(MultiList, self).updatefromconfig()

        for row in range(self.listmodel.rowCount()):
            item = self.listmodel.item(row)
            item.setEditable(False)
            item.setCheckable(True)
            item.setCheckState(Qt.Unchecked)

    def showpopup(self, *args):
        if self.widget.count() == 0:
            return

        self.largewidgetrequest.emit(BigListWidget, self.widget.currentIndex(),
                                     self._biglistitem, dict(model=self.listmodel,
                                                             label=self.labeltext,
                                                             multi=True))

    def initWidget(self, widget, config):
        widget.setEditable(True)
        self.widget.lineEdit().textChanged.connect(self.emitvaluechanged)
        widget.setModel(self.listmodel)
        widget.focusInEvent = self.showpopup
        widget.setIconSize(QSize(24, 24))
        widget.setStyleSheet(
            "QComboBox::drop-down {border-width: 0px;} QComboBox::down-arrow {image: url(noimg); border-width: 0px;}")

    def _biglistitem(self, index):
        value = self.value()
        self.widget.lineEdit().setText(value)
        # self.widget.setEdit(self.value())

    def setvalue(self, value):
        value = nullconvert(value)
        if not value:
            self.widget.lineEdit().setText(None)
            return

        values = value.split(';')

        for splitvalue in values:
            try:
                matched = self.listmodel.match(self.listmodel.index(0, 0),
                                               Qt.UserRole,
                                               splitvalue)[0]
            except IndexError:
                continue

            item = self.listmodel.itemFromIndex(matched)
            item.setCheckState(Qt.Checked)

        self.widget.lineEdit().setText(value)

    def value(self):
        items = []
        for row in range(self.listmodel.rowCount()):
            item = self.listmodel.item(row)
            if item.checkState() == Qt.Checked:
                value = item.data(Qt.UserRole)
                if value is None:
                    continue
                items.append(value)

        return ';'.join(items)
