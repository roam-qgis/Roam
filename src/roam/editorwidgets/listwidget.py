from PyQt4.QtGui import QComboBox, QStandardItem, QStandardItemModel, QIcon, QListView
from PyQt4.QtCore import QSize, Qt
from qgis.core import QgsMessageLog, QgsMapLayerRegistry, QgsExpression, QgsFeatureRequest
import qgis.core

import roam.utils
from roam.editorwidgets.core import EditorWidget, registerwidgets, LargeEditorWidget
from roam.biglist import BigList


def nullconvert(value):
    if value == qgis.core.NULL:
        return None
    return value


class BigListWidget(LargeEditorWidget):
    def __init__(self, *args, **kwargs):
        super(BigListWidget, self).__init__(*args, **kwargs)
        self.multi = False

    def createWidget(self, parent):
        return BigList(parent)

    def initWidget(self, widget):
        widget.itemselected.connect(self.selectitems)
        widget.closewidget.connect(self.cancel)
        widget.savewidget.connect(self.emitfished)

    def selectitems(self):
        if not self.multi:
            self.emitfished()

    def updatefromconfig(self):
        super(BigListWidget, self).updatefromconfig()
        model = self.config['model']
        label = self.config['label']
        self.multi = self.config.get('multi', False)
        self.widget.setlabel(label)
        self.widget.setmodel(model)
        self.endupdatefromconfig()

    def setvalue(self, value):
        self.widget.setcurrentindex(value)

    def value(self):
        return self.widget.currentindex()


class ListWidget(EditorWidget):
    widgettype = 'List'
    def __init__(self, *args):
        super(ListWidget, self).__init__(*args)
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
            layer = QgsMapLayerRegistry.instance().mapLayersByName(layername)[0]
        except IndexError:
            roam.utils.warning("Can't find layer {} in project".format(layername))
            return

        keyfieldindex = layer.fieldNameIndex(keyfield)
        valuefieldindex = layer.fieldNameIndex(valuefield)
        if keyfieldindex == -1 or valuefieldindex == -1:
            roam.utils.warning("Can't find key or value column")
            return

        if self.allownulls:
            item = QStandardItem('(no selection)')
            item.setData(None, Qt.UserRole)
            self.listmodel.appendRow(item)

        if not filterexp and valuefieldindex == keyfieldindex:
            values = layer.uniqueValues(keyfieldindex)
            for value in values:
                value = nullconvert(value)
                item = QStandardItem(value)
                item.setData(value, Qt.UserRole)
                self.listmodel.appendRow(item)
            return

        attributes = {keyfieldindex, valuefieldindex}
        flags = QgsFeatureRequest.NoGeometry

        iconfieldindex =  layer.fieldNameIndex('icon')
        if iconfieldindex > -1:
            attributes.add(iconfieldindex)

        expression = None
        if filterexp:
            expression = QgsExpression(filterexp)
            expression.prepare(layer.pendingFields())
            if expression.hasParserError():
                roam.utils.warning("Expression has parser error: {}".format(expression.parserErrorString()))
                return

            if expression.needsGeometry():
                flags = QgsFeatureRequest.NoFlags

            for field in expression.referencedColumns():
                index = layer.fieldNameIndex(field)
                attributes.add(index)

        request = QgsFeatureRequest().setFlags(flags).setSubsetOfAttributes(list(attributes))
        for feature in layer.getFeatures(request):
            if expression and not expression.evaluate(feature):
                continue

            keyvalue = nullconvert(feature[keyfieldindex])
            valuvalue = nullconvert(feature[valuefield])
            try:
                path = feature[iconfieldindex]
                icon = QIcon(path)
            except KeyError:
                icon = QIcon()

            item = QStandardItem(unicode(keyvalue))
            item.setData(unicode(valuvalue), Qt.UserRole)
            item.setIcon(icon)
            self.listmodel.appendRow(item)

    def initWidget(self, widget):
        if widget.isEditable():
            widget.editTextChanged.connect(self.validate)

        widget.currentIndexChanged.connect(self.validate)
        widget.setModel(self.listmodel)
        widget.showPopup = self.showpopup
        widget.setIconSize(QSize(24,24))

    def showpopup(self):
        if self.widget.count() == 0:
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
        if (not self.allownulls and (not self.widget.currentText() or
            self.widget.currentText() == "(no selection)")):
            self.raisevalidationupdate(False)
        else:
            self.raisevalidationupdate(True)

        self.emitvaluechanged()

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
    def __init__(self, *args):
        super(MultiList, self).__init__(*args)
        self.multi = True

    def updatefromconfig(self):
        super(MultiList, self).updatefromconfig()

        for row in xrange(self.listmodel.rowCount()):
            item = self.listmodel.item(row)
            item.setEditable(False)
            item.setCheckable(True)
            item.setCheckState(Qt.Unchecked)

    def showpopup(self):
        if self.widget.count() == 0:
            return

        self.largewidgetrequest.emit(BigListWidget, self.widget.currentIndex(),
                                     self._biglistitem, dict(model=self.listmodel,
                                                             label=self.labeltext,
                                                             multi=True))
    def initWidget(self, widget):
        widget.setEditable(True)
        widget.setModel(self.listmodel)
        widget.showPopup = self.showpopup
        widget.setIconSize(QSize(24,24))

    def _biglistitem(self, index):
        value = self.value()
        self.widget.lineEdit().setText(value)
        #self.widget.setEdit(self.value())

    def setvalue(self, value):
        value = nullconvert(value)
        if not value:
            self.widget.lineEdit().setText(value)
            return

        values = value.split(';')

        for splitvalue in values:
            try:
                matched = self.listmodel.match(self.listmodel.index(0,0),
                                               Qt.UserRole,
                                               splitvalue)[0]
            except IndexError:
                continue

            item = self.listmodel.itemFromIndex(matched)
            item.setCheckState(Qt.Checked)
        self.widget.lineEdit().setText(value)

    def value(self):
        items = []
        for row in xrange(self.listmodel.rowCount()):
            item = self.listmodel.item(row)
            if item.checkState() == Qt.Checked:
                value = item.data(Qt.UserRole)
                items.append(value)

        return ';'.join(items)
