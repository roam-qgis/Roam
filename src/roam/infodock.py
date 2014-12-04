import os

from string import Template
from collections import OrderedDict

from PyQt4.QtGui import ( QWidget, QIcon, QListWidgetItem, QMouseEvent, QApplication)

from PyQt4.QtCore import (Qt, QUrl,
                          QEvent, pyqtSignal
                          )

from PyQt4.QtWebKit import QWebPage

from qgis.core import (QgsExpression, QgsFeature,
                       QgsMapLayer, QgsFeatureRequest)

from roam import utils
from roam.flickwidget import FlickCharm
from roam.htmlviewer import updateTemplate, clear_image_cache
from roam.ui.uifiles import (infodock_widget)
from roam.api import RoamEvents
from roam.dataaccess import database
from roam.api.utils import layer_by_name, values_from_feature


import templates

infotemplate = templates.get_template("info")
infoblocktemplate = templates.get_template("infoblock")
countblocktemplate = templates.get_template("countblock")


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
        self.attributesView.linkClicked.connect(self.handle_link)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.grabGesture(Qt.SwipeGesture)
        self.setAttribute(Qt.WA_AcceptTouchEvents)
        self.editButton.pressed.connect(self.openform)
        self.editGeomButton.pressed.connect(self.editgeom)
        self.parent().installEventFilter(self)
        self.project = None
        self.startwidth = self.width()
        self.expaned = False

        self.expandButton.pressed.connect(self.change_expanded_state)
        self.navwidget.mousePressEvent = self._sink
        self.bottomWidget.mousePressEvent = self._sink
        self.navwidget.mouseReleaseEvent = self._sink
        self.bottomWidget.mouseReleaseEvent = self._sink
        self.navwidget.mouseMoveEvent = self._sink
        self.bottomWidget.mouseMoveEvent = self._sink

        RoamEvents.selectioncleared.connect(self.clearResults)
        RoamEvents.editgeometry_complete.connect(self.refreshcurrent)

    def handle_link(self, url):
        if url.toString().endswith("/back"):
            self.pageback()
        elif url.toString().endswith("/next"):
            self.pagenext()
        else:
            RoamEvents.openurl.emit(url)

    def _sink(self, event):
        return

    def change_expanded_state(self):
        if self.expaned:
            self._collapse()
        else:
            self._expand()

    def mousePressEvent(self, event):
        pos = self.mapToParent(event.pos())
        newevent = QMouseEvent(event.type(), pos, event.button(), event.buttons(), event.modifiers())
        self.parent().mousePressEvent(newevent)

    def mouseReleaseEvent(self, event):
        pos = self.mapToParent(event.pos())
        newevent = QMouseEvent(event.type(), pos, event.button(), event.buttons(), event.modifiers())
        self.parent().mouseReleaseEvent(newevent)

    def mouseMoveEvent(self, event):
        pos = self.mapToParent(event.pos())
        newevent = QMouseEvent(event.type(), pos, event.button(), event.buttons(), event.modifiers())
        self.parent().mouseMoveEvent(newevent)

    def _expand(self):
        self.resize(self.parent().width() - 10, self.parent().height())
        self.move(10, 0)
        self.expaned = True

    def _collapse(self):
        self.resize(self.startwidth, self.parent().height())
        self.move(self.parent().width() - self.startwidth, 0)
        self.expaned = False

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self._collapse()

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
        size = 0
        for n in range(self.layerList.count()):
            size += self.layerList.sizeHintForRow(n)
        self.layerList.setMinimumHeight(size)
        self.layerList.setMaximumHeight(size)
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
            utils.exception(ex)
            return


        form = cursor.form
        layer = cursor.layer

        clear_image_cache()

        info1, results = self.generate_info("info1", self.project, layer, feature.id(), feature, countlabel=str(cursor))
        info2, _= self.generate_info("info2", self.project, layer, feature.id(), feature, lastresults=results[0])

        if form:
            name = "{}".format(layer.name(), form.label)
        else:
            name = layer.name()

        info = dict(TITLE=name,
                    INFO1=info1,
                    INFO2=info2)

        html = updateTemplate(info, infotemplate)

        self.attributesView.setHtml(html, templates.baseurl)
        tools = self.project.layer_tools(layer)
        hasform = not form is None
        editattributes = 'edit_attributes' in tools and hasform
        editgeom = 'edit_geom' in tools and hasform
        self.editButton.setVisible(editattributes)
        self.editGeomButton.setVisible(editgeom)
        self.featureupdated.emit(layer, feature, cursor.features)

    def generate_info(self, infoblock, project, layer, mapkey, feature, countlabel=None, lastresults=None):
        infoblockdef = project.info_query(infoblock, layer.name())
        isinfo1 = infoblock == "info1"

        if not infoblockdef:
            if isinfo1:
                infoblockdef = {}
                infoblockdef['type'] = 'feature'
            else:
                return None, []

        if isinfo1:
            caption = infoblockdef.get('caption', "Record")
        else:
            caption = infoblockdef.get('caption', "Related Record")

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
        for count, result in enumerate(results, start=1):
            if isinfo1 and count == 1:
                countblock = countblocktemplate.substitute(count=countlabel)
            else:
                countblock = ''

            fields = result.keys()
            attributes = result.values()
            rows = generate_rows(fields, attributes, imagepath=self.project.image_folder)
            blocks.append(updateTemplate(dict(ROWS=rows,
                                              HEADER=caption,
                                              CONTROLS=countblock),
                                         infoblocktemplate))
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
                        return lastresults['mapkey']
                    else:
                        return []
                else:
                    return feature[keycolumn]
            except KeyError:
                return mapkey

        def get_layer():
            connection = infoblockdef.get('connection', "from_layer")
            if isinstance(connection, dict):
                return layer_by_name(connection['layer'])
            elif connection == "from_layer":
                return layer
            else:
                raise NotImplementedError("{} is not a supported connection type".format(connection))

        if not lastresults:
            lastresults = {}

        sql = infoblockdef['query']
        layer = get_layer()

        db = database.Database.fromLayer(layer)
        mapkey = get_key()
        attributes = values_from_feature(feature)
        results = db.query(sql, mapkey=mapkey, **attributes)
        results = list(results)
        return results

    def clearResults(self):
        self.layerList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.navwidget.hide()

def generate_rows(fields, attributes, **kwargs):
    data = OrderedDict()
    items = []
    for field, value in zip(fields, attributes):
        if field == 'mapkey':
            continue
        data[field.replace(" ", "_")] = value
        item = u"<tr><th>{0}</th> <td>${{{1}}}</td></tr>".format(field, field.replace(" ", "_"))
        items.append(item)
    rowtemple = Template(''.join(items))
    rowshtml = updateTemplate(data, rowtemple, **kwargs)
    return rowshtml

