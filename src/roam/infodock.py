import os
import collections

from string import Template
from collections import OrderedDict

from PyQt4.QtGui import (QImageReader, QWidget, QFrame, QDialog, QIcon, QSortFilterProxyModel,QListWidgetItem)

from PyQt4.QtCore import (Qt, QUrl, 
                          QDate,
                          QDateTime, QTime,
                          QPoint, QSize,
                          QEvent, pyqtSignal,
                          )

from PyQt4.QtWebKit import QWebPage

from qgis.core import (QgsExpression, QgsFeature, 
                       QgsMapLayer)

from roam import utils
from roam.flickwidget import FlickCharm
from roam.htmlviewer import updateTemplate, openimage
from roam.uifiles import (infodock_widget, infodock_base)

import pkgutil
htmlpath = os.path.join(os.path.dirname(__file__), "info.html")

with open(htmlpath) as f:
    template = Template(f.read())

class FeatureCursor(object):
    """
    A feature cursor that keeps track of the current feature
    and handles wrapping to the start and end of the list
    """
    def __init__(self, layer, features, form=None, position=0):
        self.layer = layer
        self.features = features
        self.position = position
        self.form = form

    def next(self):
        if self.position == len(self.features):
            self.position = 0
        else:
            self.position += 1
        return self

    def back(self):
        if self.position == 0:
            self.position = len(self.features)
        else:
            self.position -= 1
        return self

    @property
    def feature(self):
        try:
            return self.features[self.position]
        except IndexError:
            return None

    def __str__(self):
        return "{} of {}".format(self.position, len(self.features))

class InfoDock(infodock_widget, QWidget):
    requestopenform = pyqtSignal(object, QgsFeature)
    featureupdated = pyqtSignal(object, object, list)
    resultscleared = pyqtSignal()

    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        self.forms = {}
        self.charm = FlickCharm()
        self.charm.activateOn(self.attributesView)
        self.layerList.currentRowChanged.connect(self.layerIndexChanged)
        self.attributesView.linkClicked.connect(openimage)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.grabGesture(Qt.SwipeGesture)
        self.setAttribute(Qt.WA_AcceptTouchEvents)
        self.editButton.pressed.connect(self.openform)
        self.parent().installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            width = self.parent().width() * 40 / 100
            self.resize(width, self.parent().height())
            self.move(self.parent().width() - self.width() -1, 1)

        return object.eventFilter(object, event)

    def close(self):
        self.clearResults()
        super(InfoDock, self).close()

    def event(self, event):
        if event.type() == QEvent.Gesture:
            gesture = event.gesture(Qt.SwipeGesture)
            if gesture:
                self.pagenext()
        return QWidget.event(self, event)

    @property
    def selection(self):
        item = self.layerList.item(self.layerList.currentRow())
        if not item:
            return

        cursor = item.data(Qt.UserRole)
        return cursor

    def openform(self):
        cursor = self.selection
        self.requestopenform.emit(cursor.form, cursor.feature)

    def pageback(self):
        cursor = self.selection
        cursor.back()
        self.update(cursor)

    def pagenext(self):
        cursor = self.selection
        cursor.next()
        self.update(cursor)

    def layerIndexChanged(self, index):
        item = self.layerList.item(index)
        if not item:
            return

        cursor = item.data(Qt.UserRole)
        self.countlabel.setText(str(cursor))
        self.update(cursor)

    def setResults(self, results, forms):
        self.clearResults()
        self.forms = forms
        for layer, features in results.iteritems():
            if features:
                self._addResult(layer, features)

        self.layerList.setCurrentRow(0)
        self.layerList.setMinimumWidth(self.layerList.sizeHintForColumn(0) + 20)

    def _addResult(self, layer, features):
        name = layer.name()
        forms = self.forms.get(name, [])
        if not forms:
            item = QListWidgetItem(QIcon(), name, self.layerList)
            item.setData(Qt.UserRole, FeatureCursor(layer, features))
            return

        for form in forms:
            print form.label
            name = "{} ({})".format(name, form.label)
            icon = QIcon(form.icon)
            item = QListWidgetItem(icon, name, self.layerList)
            item.setData(Qt.UserRole, FeatureCursor(layer, features, form))

    def update(self, cursor):
        global image
        images = {}
        fields = [field.name() for field in feature.fields()]
        data = OrderedDict()

        items = []
        for field, value in zip(fields, feature.attributes()):
            data[field] = value
            item = "<tr><th>{0}</th> <td>${{{0}}}</td></tr>".format(field)
            items.append(item)
        rowtemple = Template(''.join(items))
        rowshtml = updateTemplate(data, rowtemple)

        form = cursor.form
        layer = cursor.layer
        if form:
            name = "{}({})".format(layer.name(), form.label)
        else:
            name = layer.name()

        info = dict(TITLE=name,
                    ROWS=rowshtml)

        html = updateTemplate(info, template)
        base = os.path.dirname(os.path.abspath(__file__))
        baseurl = QUrl.fromLocalFile(base + '\\')

        displaytext = form.settings.get('display', None)
        display = QgsExpression.replaceExpressionText(displaytext, cursor.feature, layer )
        self.attributesView.setHtml(html, baseurl)
        self.editButton.setVisible(not form is None)
        self.featureupdated.emit(layer, cursor.feature, cursor.features)

    def clearResults(self):
        self.layerList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.resultscleared.emit()

