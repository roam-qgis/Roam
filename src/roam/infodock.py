import os

from string import Template
from collections import OrderedDict

from PyQt4.QtGui import ( QWidget, QIcon, QListWidgetItem)

from PyQt4.QtCore import (Qt, QUrl,
                          QEvent, pyqtSignal,
                          )

from PyQt4.QtWebKit import QWebPage

from qgis.core import (QgsExpression, QgsFeature, 
                       QgsMapLayer, QgsFeatureRequest)

from roam import utils
from roam.flickwidget import FlickCharm
from roam.htmlviewer import updateTemplate
from roam.ui.uifiles import (infodock_widget)
from roam.api import RoamEvents
from roam.dataaccess import database

import templates

htmlpath = os.path.join(os.path.dirname(__file__), "templates/info.html")

with open(htmlpath) as f:
    template = Template(f.read())


class NoFeature(Exception):
    pass


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
        return self

    def back(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.features) - 1
        return self

    @property
    def feature(self):
        try:
            feature = self.features[self.index]
            rq = QgsFeatureRequest(feature.id())
            return self.layer.getFeatures(rq).next()
        except IndexError:
            raise NoFeature("No feature in selection at postion".format(self.index))
        except StopIteration:
            raise NoFeature("No feature with id {}".format(feature.id()))

    def __str__(self):
        return "{} of {}".format(self.index + 1, len(self.features))


class InfoDock(infodock_widget, QWidget):
    featureupdated = pyqtSignal(object, object, list)
    resultscleared = pyqtSignal()

    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        self.forms = {}
        self.charm = FlickCharm()
        self.charm.activateOn(self.attributesView)
        self.layerList.currentRowChanged.connect(self.layerIndexChanged)
        self.attributesView.linkClicked.connect(RoamEvents.openurl.emit)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.grabGesture(Qt.SwipeGesture)
        self.setAttribute(Qt.WA_AcceptTouchEvents)
        self.editButton.pressed.connect(self.openform)
        self.editGeomButton.pressed.connect(self.editgeom)
        self.parent().installEventFilter(self)
        self.project = None

        RoamEvents.selectioncleared.connect(self.clearResults)
        RoamEvents.editgeometry_complete.connect(self.refreshcurrent)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self.resize(self.width(), self.parent().height())
            self.move(self.parent().width() - self.width(), 0)

        return super(InfoDock, self).eventFilter(object, event)

    def close(self):
        RoamEvents.selectioncleared.emit()
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
        RoamEvents.load_feature_form(cursor.form, cursor.feature, True)

    def editgeom(self):
        cursor = self.selection
        RoamEvents.editgeometry.emit(cursor.form, cursor.feature)

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

    def setResults(self, results, forms, project):
        lastrow = self.layerList.currentRow()
        if lastrow == -1:
            lastrow = 0

        self.clearResults()
        self.forms = forms
        self.project = project

        for layer, features in results.iteritems():
            if features:
                self._addResult(layer, features)

        self.layerList.setCurrentRow(lastrow)
        self.layerList.setMinimumWidth(self.layerList.sizeHintForColumn(0) + 20)
        self.navwidget.show()

    def show(self):
        if self.layerList.count() > 0:
            super(InfoDock, self).show()
        else:
            self.hide()

    def _addResult(self, layer, features):
        layername = layer.name()
        forms = self.forms.get(layername, [])
        if not forms:
            item = QListWidgetItem(QIcon(), layername, self.layerList)
            item.setData(Qt.UserRole, FeatureCursor(layer, features))
            return

        for form in forms:
            itemtext = "{} \n ({})".format(layername, form.label)
            icon = QIcon(form.icon)
            item = QListWidgetItem(icon, itemtext, self.layerList)
            item.setData(Qt.UserRole, FeatureCursor(layer, features, form))

    def refreshcurrent(self):
        self.update(self.selection)

    def update(self, cursor):
        if cursor is None:
            return

        try:
            feature = cursor.feature
        except NoFeature as ex:
            utils.warning(ex)
            return


        form = cursor.form
        layer = cursor.layer

        info1 = self.generate_info("info1", self.project, layer, feature.id(), feature)
        info2 = self.generate_info("info2", self.project, layer, feature.id(), feature)

        if form:
            name = "{}".format(layer.name(), form.label)
        else:
            name = layer.name()

        info = dict(TITLE=name,
                    INFO1=info1,
                    INFO2=info2)

        html = updateTemplate(info, template)

        self.countlabel.setText(str(cursor))
        self.attributesView.setHtml(html, templates.baseurl)
        self.editButton.setVisible(not form is None)
        self.editGeomButton.setVisible(not form is None)
        self.featureupdated.emit(layer, feature, cursor.features)


    def generate_info(self, infoblock, project, layer, mapkey, feature):
        if infoblock == "info1":
            header = "Record"
        else:
            header = "Related Record"

        info_template = Template("""
        <div class="panel panel-default">
          <div class="panel-heading text-left">
            <h2 class="panel-title" style="font-size:24px">${HEADER}</h2>
          </div>
          <div class="panel-body" style="padding:0px">
            <table class="table table-condensed">
                <col style="width: 35%;"/>
                <col style="width: 65%;"/>
            ${ROWS}
            </table>
            </div>
        </div>
        """)

        query = project.info_query(infoblock, layer.name())
        print query
        if not query and infoblock == "info1":
            query = {}
            query['type'] = 'feature'
        elif not query:
            return None

        results = []
        if query['type'] == 'sql':
            sql = query['query']
            print sql
            connection = query['connection']
            if connection == "from_layer":
                try:
                    db = database.Database.fromLayer(layer)
                    results = db.query(sql, mapkey=mapkey)
                except database.DatabaseException as ex:
                    return "<b> Error: {}<b>".format(ex.message)
            else:
                return None
        elif query['type'] == 'feature':
            fields = [field.name() for field in feature.fields()]
            attributes = feature.attributes()
            results.append(dict(zip(fields, attributes)))
        else:
            return None

        blocks = []
        try:
            for result in results:
                fields = result.keys()
                attributes = result.values()
                rows = generate_rows(fields, attributes)
                print rows
                blocks.append(updateTemplate(dict(ROWS=rows,
                                                  HEADER=header), info_template))
            return '<br>'.join(blocks)
        except database.DatabaseException as ex:
            return "<b> Error: {}<b>".format(ex.msg)

    def clearResults(self):
        self.layerList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.navwidget.hide()

def generate_rows(fields, attributes):
    data = OrderedDict()
    items = []
    for field, value in zip(fields, attributes):
        data[field] = value
        item = u"<tr><th>{0}</th> <td>${{{0}}}</td></tr>".format(field)
        items.append(item)
    rowtemple = Template(''.join(items))
    rowshtml = updateTemplate(data, rowtemple)
    return rowshtml

