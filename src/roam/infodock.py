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

    HACK: This could be a lot nicer and cleaner but it works
    for now
    """
    def __init__(self, layer, features, form=None, index=0):
        self.layer = layer
        self.features = features
        self.index = index
        self.form = form

    def next(self):
        self.index += 1
        if self.index > len(self.features) - 1:
            self.index = 0
        print self.index, len(self.features)
        return self

    def back(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.features) - 1
        return self

    @property
    def feature(self):
        try:
            return self.features[self.index]
        except IndexError:
            return None

    def __str__(self):
        return "{} of {}".format(self.index + 1, len(self.features))

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
        self.update(cursor)

    def setResults(self, results, forms):
        self.clearResults()
        self.forms = forms
        for layer, features in results.iteritems():
            if features:
                self._addResult(layer, features)

        self.layerList.setCurrentRow(0)
        self.layerList.setMinimumWidth(self.layerList.sizeHintForColumn(0) + 20)
        self.navwidget.show()

    def _addResult(self, layer, features):
        layername = layer.name()
        forms = self.forms.get(layername, [])
        if not forms:
            item = QListWidgetItem(QIcon(), layername, self.layerList)
            item.setData(Qt.UserRole, FeatureCursor(layer, features))
            return

        for form in forms:
            itemtext = "{} ({})".format(layername, form.label)
            icon = QIcon(form.icon)
            item = QListWidgetItem(icon, itemtext, self.layerList)
            item.setData(Qt.UserRole, FeatureCursor(layer, features, form))

    def update(self, cursor):
        global image
        images = {}
        feature = cursor.feature
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
            name = "{}".format(layer.name(), form.label)
        else:
            name = layer.name()

        info = dict(TITLE=name,
                    ROWS=rowshtml)

        html = updateTemplate(info, template)
        base = os.path.dirname(os.path.abspath(__file__))
        baseurl = QUrl.fromLocalFile(base + '\\')

        if form:
            displaytext = form.settings.get('display', None)
            display = QgsExpression.replaceExpressionText(displaytext, cursor.feature, layer )
        else:
            display = str(feature[0])

        self.countlabel.setText(str(cursor))
        self.displaylabel.setText(display)
        self.attributesView.setHtml(html, baseurl)
        self.editButton.setVisible(not form is None)
        self.featureupdated.emit(layer, cursor.feature, cursor.features)

    def clearResults(self):
        self.layerList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.resultscleared.emit()
        self.navwidget.hide()

