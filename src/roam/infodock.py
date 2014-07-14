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
from roam.api.utils import layer_by_name, values_from_feature

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
        self.layerList.setMinimumHeight(self.layerList.sizeHintForRow(0) + 20)
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
            selectname = self.project.selectlayer_name(form.layername)
            print selectname
            if selectname == layername:
                itemtext = "{} \n ({})".format(layername, form.label)
            else:
                itemtext = selectname
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

        info1, results = self.generate_info("info1", self.project, layer, feature.id(), feature)
        info2, _= self.generate_info("info2", self.project, layer, feature.id(), feature, lastresults=results[0])

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
        tools = self.project.layer_tools(layer)
        hasform = not form is None
        editattributes = 'edit_attributes' in tools and hasform
        editgeom = 'edit_geom' in tools and hasform
        self.editButton.setVisible(editattributes)
        self.editGeomButton.setVisible(editgeom)
        self.featureupdated.emit(layer, feature, cursor.features)


    def generate_info(self, infoblock, project, layer, mapkey, feature, lastresults=None):
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

        infoblockdef = project.info_query(infoblock, layer.name())
        isinfo1 = infoblock == "info1"
        if not infoblockdef:
            if isinfo1:
                infoblockdef = {}
                infoblockdef['type'] = 'feature'
            else:
                return None, []

        results = []
        error = None
        if infoblockdef['type'] == 'sql':
            try:
                queryresults = self.results_from_query(infoblockdef, layer, feature, mapkey, lastresults=lastresults)
                if isinfo1 and not queryresults:
                    # If there is no results from the query and we are a info 1 block we grab from the feature.
                    results.append(self.results_from_feature(feature))
                else:
                    results = queryresults
            except database.DatabaseException as ex:
                if not isinfo1:
                    error = "<b> Error: {} <b>".format(ex.msg)
                else:
                    results.append(self.results_from_feature(feature))

        elif infoblockdef['type'] == 'feature':
            results.append(self.results_from_feature(feature))
        else:
            return None, []

        blocks = []
        for result in results:
            fields = result.keys()
            attributes = result.values()
            rows = generate_rows(fields, attributes)
            blocks.append(updateTemplate(dict(ROWS=rows,
                                              HEADER=header), info_template))
        if error:
            return error, []

        return '<br>'.join(blocks), results

    def results_from_feature(self, feature):
        return values_from_feature(feature)

    def results_from_query(self, infoblockdef, layer, feature, mapkey, lastresults=None):
        def get_key():
            try:
                keycolumn = infoblockdef['mapping']['mapkey']
                if keycolumn == 'from_info1':
                    if 'mapkey' in lastresults:
                        mapkey = lastresults['mapkey']
                    else:
                        return []
                else:
                    mapkey = feature[keycolumn]
            except KeyError:
                mapkey = mapkey
            return mapkey

        def get_layer():
            connection = infoblockdef['connection']
            if isinstance(connection, dict):
                layer = layer_by_name(connection['layer'])
            elif connection == "from_layer":
                layer = layer
            else:
                raise NotImplementedError("{} is not a supported connection type".format(connection))
            return layer

        if not lastresults:
            lastresults = {}

        sql = infoblockdef['query']
        layer = get_layer()

        db = database.Database.fromLayer(layer)
        mapkey = get_key()
        results = db.query(sql, mapkey=mapkey)
        return list(results)

    def clearResults(self):
        self.layerList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.navwidget.hide()

def generate_rows(fields, attributes):
    data = OrderedDict()
    items = []
    for field, value in zip(fields, attributes):
        if field == 'mapkey':
            continue
        data[field.replace(" ", "_")] = value
        item = u"<tr><th>{0}</th> <td>${{{1}}}</td></tr>".format(field, field.replace(" ", "_"))
        items.append(item)
    rowtemple = Template(''.join(items))
    rowshtml = updateTemplate(data, rowtemple)
    return rowshtml

