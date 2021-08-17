from collections import OrderedDict

from qgis.PyQt.QtCore import Qt, QEvent, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QMouseEvent, QKeySequence
from qgis.PyQt.QtWebKitWidgets import QWebPage
from qgis.PyQt.QtWidgets import QWidget, QListWidgetItem, QAction
from qgis.core import (QgsFeatureRequest, QgsGeometry, NULL, QgsFeature)
from string import Template

import roam.api.utils
from roam import templates
from roam import utils
from roam.api import RoamEvents, GPS
from roam.api.utils import layer_by_name, values_from_feature, install_touch_scroll
from roam.dataaccess import database
from roam.htmlviewer import updateTemplate, clear_image_cache
from roam.popupdialogs import PickActionDialog
from roam.ui.uifiles import (infodock_widget)

infotemplate = templates.get_template("info")
infoblocktemplate = templates.get_template("infoblock")
countblocktemplate = templates.get_template("countblock")


class NoFeature(Exception):
    """
    Exception raised  when no feature is found in the layer.
    """
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
        """
        Move to the next feature in the cursor
        :return: self
        """
        self.index += 1
        if self.index > len(self.features) - 1:
            self.index = 0
        return self

    def back(self):
        """
        Move to the previous feature in the cursor
        :return: self
        """
        self.index -= 1
        if self.index < 0:
            self.index = len(self.features) - 1
        return self

    @property
    def feature(self) -> QgsFeature:
        """
        The current active feature in the cursor.
        :return: The active QgsFeature
        """
        try:
            feature = self.features[self.index]
            rq = QgsFeatureRequest(feature.id())
            return next(self.layer.getFeatures(rq))
        except IndexError:
            raise NoFeature("No feature in selection at postion".format(self.index))
        except StopIteration:
            raise NoFeature("No feature with id {}".format(feature.id()))

    def __str__(self):
        return "{} of {}".format(self.index + 1, len(self.features))


class InfoDock(infodock_widget, QWidget):
    featureupdated = pyqtSignal(object, object, list)
    resultscleared = pyqtSignal()
    activeLayerChanged = pyqtSignal(object)

    def __init__(self, parent):
        super(InfoDock, self).__init__(parent)
        self.setupUi(self)
        # TODO Doesn't currently work with webview. Loop back and fix this.
        install_touch_scroll(self.attributesView)

        self.forms = {}

        self.layerList.currentRowChanged.connect(self.layerIndexChanged)
        self.attributesView.linkClicked.connect(self.handle_link)
        self.attributesView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        action = self.attributesView.pageAction(QWebPage.Copy)
        action.setShortcut(QKeySequence.Copy)
        self.grabGesture(Qt.SwipeGesture)
        self.setAttribute(Qt.WA_AcceptTouchEvents)
        self.editButton.pressed.connect(self.openform)
        self.editGeomButton.pressed.connect(self.editgeom)
        self.parent().installEventFilter(self)
        self.project = None
        self.startwidth = self.width()
        self.expaned = False
        self.layerList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.expandAction = QAction(QIcon(":/icons/expand"), "Expand Panel", self)
        self.expandAction.triggered.connect(self.change_expanded_state)

        self.navigateAction = QAction(QIcon(":/icons/navigate"), "Navigate To..", self)
        self.navigateAction.triggered.connect(self._navigate_to_selection)

        self.moreActionsButton.pressed.connect(self._show_more_actions)
        self.navwidget.mousePressEvent = self._sink
        self.bottomWidget.mousePressEvent = self._sink
        self.navwidget.mouseReleaseEvent = self._sink
        self.bottomWidget.mouseReleaseEvent = self._sink
        self.navwidget.mouseMoveEvent = self._sink
        self.bottomWidget.mouseMoveEvent = self._sink
        self.deleteFeatureButton.pressed.connect(self.delete_feature)
        self.deleteFeatureButton.setCheckable(False)

        self.quickInspectButton.hide()
        self.quickInspectButton.pressed.connect(self.quick_inspect_feature)

        self.nextButton.pressed.connect(self.pagenext)
        self.prevButton.pressed.connect(self.pageback)

        RoamEvents.selectioncleared.connect(self.clearResults)
        RoamEvents.editgeometry_complete.connect(self.refreshcurrent)
        RoamEvents.editgeometry_invalid.connect(self.refreshcurrent)

    def _navigate_to_selection(self) -> None:
        """
        Set the GPS waypoint to the active feature
        """
        feature = self.selection.feature
        geom = feature.geometry()
        point = geom.centroid().asPoint()
        if GPS.waypoint == point:
            GPS.waypoint = None
        else:
            GPS.waypoint = point

    def _show_more_actions(self) -> None:
        """
        Show the more actions selector dialog.
        """
        dlg = PickActionDialog()
        self.navigateAction.setEnabled(GPS.isConnected)
        if not GPS.isConnected:
            self.navigateAction.setText("Navigate To.. (No GPS)")
        else:
            self.navigateAction.setText("Navigate To..")

        dlg.addactions([self.expandAction, self.navigateAction])
        dlg.exec_()

    def delete_feature(self) -> None:
        """
        Trigger the feature delete logic.
        Doesn't delete the feature here just fires the event to delete the feature.
        """
        cursor = self.selection
        RoamEvents.delete_feature(cursor.form, cursor.feature)

    def handle_link(self, url) -> None:
        """
        Handle any links that are fired
        :param url: The url that is clicked in the info dock
        :return:
        """
        if url.toString().endswith("/back"):
            self.pageback()
        elif url.toString().endswith("/next"):
            self.pagenext()
        else:
            RoamEvents.openurl.emit(url)

    def _sink(self, event) -> None:
        """
        Empty event sink to do nothing with the event.
        """
        return

    def change_expanded_state(self) -> None:
        """
        Expand or collapse the info panel view
        """
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

    def _expand(self) -> None:
        """
        Expand the info panel.
        """
        self.resize(self.parent().width() - 10, self.parent().height())
        self.move(10, 0)
        self.expaned = True
        self.expandAction.setText("Collapse Panel")

    def _collapse(self) -> None:
        """
        Collapse the info panel back to the samller state
        :return:
        """
        self.resize(self.startwidth, self.parent().height())
        self.move(self.parent().width() - self.startwidth, 0)
        self.expaned = False
        self.expandAction.setText("Expand Panel")

    def eventFilter(self, object, event):
        if event.type() == QEvent.Resize:
            self._collapse()

        return super(InfoDock, self).eventFilter(object, event)

    def close(self):
        """
        Close the info panel dock.
        :return:
        """
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
        """
        Return the active selection in the info panel.
        :return:
        """
        item = self.layerList.item(self.layerList.currentRow())
        if not item:
            return

        cursor = item.data(Qt.UserRole)
        return cursor

    def openform(self):
        """
        Fire the open feature form event to open the form for the current feature.
        :return:
        """
        cursor = self.selection
        tools = self.project.layer_tools(cursor.layer)
        if 'inspection' in tools:
            config = tools['inspection']
            form, feature = self.get_inspection_config(cursor.feature, config)
            editmode = False
        else:
            form = cursor.form
            feature = cursor.feature
            editmode = True

        RoamEvents.load_feature_form(form, feature, editmode)

    def quick_inspect_feature(self):
        """
        Quick inspect the current feature
        """
        cursor = self.selection
        tools = self.project.layer_tools(cursor.layer)
        config = tools['inspection']
        form, feature = self.get_inspection_config(cursor.feature, config)
        editmode = False
        form.suppressform = True
        RoamEvents.load_feature_form(form, feature, editmode)
        # Leaking state is leaking.  But this is what we have for now.
        form.suppressform = False

    def get_inspection_config(self, current_feature, config):
        """
        Returns the inspection form and a copy of the feature for the new form.
        :param current_feature: The current feature to be copied
        :param config: The tool config
        :return:
        """
        form = config['form']
        newform = self.project.form_by_name(form)
        if config.get('mode', "copy").lower() == 'copy':
            geom = current_feature.geometry()
            mappings = config.get('field_mapping', {})
            data = {}
            for fieldfrom, fieldto in mappings.items():
                data[fieldto] = current_feature[fieldfrom]

            newgeom = QgsGeometry(geom)
            newfeature = newform.new_feature(geometry=newgeom, data=data)

            return newform, newfeature
        else:
            raise NotImplementedError("Only copy mode supported currently")

    def editgeom(self) -> None:
        """
        Trigger the event to edit the geometry of the active feature.
        """
        cursor = self.selection
        RoamEvents.editgeometry.emit(cursor.form, cursor.feature)
        self.editGeomButton.setEnabled(False)
        self.deleteFeatureButton.setEnabled(False)

    def pageback(self) -> None:
        """
        Go back a page
        :return:
        """
        cursor = self.selection
        cursor.back()
        self.update(cursor)

    def pagenext(self) -> None:
        """
        Go to the next page.
        :return:
        """
        cursor = self.selection
        cursor.next()
        self.update(cursor)

    def layerIndexChanged(self, index) -> None:
        """
        Called when the selected layer item changes.

        Updates the panel with layer selection.
        :param index: The new index of the selected
        """
        item = self.layerList.item(index)
        if not item:
            return

        cursor = item.data(Qt.UserRole)
        self.update(cursor)
        self.activeLayerChanged.emit(cursor.layer)

    def setResults(self, results, forms, project) -> None:
        """
        Set the results for the info panel.
        :param results: Dict of layer and features for the selection.
        :param forms: The forms from the project.
        :param project: The active project.
        """
        lastrow = self.layerList.currentRow()
        if lastrow == -1:
            lastrow = 0

        self.clearResults()
        self.forms = forms
        self.project = project

        for layer, features in results.items():
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

    def show(self) -> None:
        """
        Show or hide the layer panel based on the results count.
        """
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

    def refreshcurrent(self) -> None:
        """
        Refresh the dock with the updated selection.
        """
        self.update(self.selection)

    def update(self, cursor) -> None:
        """
        Update the data in the dock with the given cursor data.
        :param cursor: The cursor holding a pointer to the data and feature for the active feature.
        """
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

        self.countLabel.setText(str(cursor))

        info1, results = self.generate_info("info1", self.project, layer, feature.id(), feature, countlabel=str(cursor))
        info2, _ = self.generate_info("info2", self.project, layer, feature.id(), feature, lastresults=results[0])

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
        hasform = form is not None
        editattributes = ('edit_attributes' in tools and hasform) or 'inspection' in tools
        editgeom = 'edit_geom' in tools and hasform
        deletefeature = 'delete' in tools and hasform
        self.deleteFeatureButton.setVisible(deletefeature)
        self.quickInspectButton.setVisible('inspection' in tools)
        self.editButton.setVisible(editattributes)
        feature = cursor.feature
        self.editGeomButton.setVisible(editgeom)
        self.editGeomButton.setEnabled(True)
        self.featureupdated.emit(layer, feature, cursor.features)

    def generate_info(self, infoblock, project, layer, mapkey, feature, countlabel=None, lastresults=None):
        """
        Generate a info block for the display.
        :param infoblock: The info block name to generate.
        :param project: The active Roam project.
        :param layer: The active layer.
        :param mapkey: The current map key of the selected feature.  Normally just the primary key column from QGIS.
        :param feature: The selected feature.
        :param countlabel: The label to use as the count header.
        :param lastresults: The results from another info block. Normally info1 passed to info2.
        :returns:
        """
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
        infotype = infoblockdef.get('type', 'feature')
        if infotype == 'sql':
            try:
                queryresults = self.results_from_query(infoblockdef, layer, feature, mapkey, lastresults=lastresults)
                if isinfo1 and not queryresults:
                    # If there is no results from the query and we are a info 1 block we grab from the feature.
                    results.append(results_from_feature(feature))
                else:
                    results = queryresults
            except database.DatabaseException as ex:
                RoamEvents.raisemessage("Query Error", ex.message, 3)
                utils.error(ex.message)
                if not isinfo1:
                    error = "<b> Error: {} <b>".format(ex.msg)
                else:
                    results.append(results_from_feature(feature))

        elif infotype == 'feature':
            featuredata = results_from_feature(feature)
            excludedfields = infoblockdef.get('hidden', [])
            for field in excludedfields:
                try:
                    del featuredata[field]
                except KeyError:
                    pass
            results.append(featuredata)
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
            rows = create_data_html(fields, attributes, imagepath=self.project.image_folder)
            try:
                caption = caption.format(**dict(zip(fields, attributes)))
            except KeyError:
                pass

            blocks.append(updateTemplate(dict(ROWS=rows,
                                              HEADER=caption,
                                              CONTROLS=countblock),
                                         infoblocktemplate))
        if error:
            return error, []

        return '<br>'.join(blocks), results

    def results_from_query(self, infoblockdef, layer, feature, mapkey, lastresults=None) -> list:
        """
        Return the resutls from running a database query to get the feature results.
        :param infoblockdef: The info block project config section.
        :param layer: The QgsVectorLayer to get the connection from.
        :param feature: The feature to pull the map key from.
        :param mapkey: The mapkey to use if not set in the info block config or found in the last results.
        :param lastresults: Results of another info results block. Normally info 1
        :return: List of query results from running the query on the layer.
        """

        def get_key() -> str:
            try:
                keycolumn = infoblockdef['mapping']['mapkey']
                if keycolumn == 'from_info1':
                    if 'mapkey' in lastresults:
                        return lastresults['mapkey']
                    else:
                        # TODO Umm wat? Why is this returning a list?
                        return []
                else:
                    return feature[keycolumn]
            except KeyError:
                return mapkey

        def get_layer() -> str:
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
        attributes = values_from_feature(feature, safe_names=True)
        attributes['mapkey'] = mapkey
        # Run the SQL text though the QGIS expression engine first.
        sql = roam.api.utils.replace_expression_placeholders(sql, feature)
        results = db.query(sql, **attributes)
        results = list(results)
        return results

    def clearResults(self) -> None:
        """
        Clear the results in the info panel.
        """
        self.layerList.clear()
        self.attributesView.setHtml('')
        self.editButton.setVisible(False)
        self.editGeomButton.setEnabled(True)
        self.editButton.setEnabled(True)
        self.deleteFeatureButton.setEnabled(True)
        self.navwidget.hide()


def create_data_html(fields, attributes, **kwargs) -> str:
    """
    Generate the html data for the info panel.
    :param fields: The fields to use in the data table.
    :param attributes: The attributes to use in the table.
    :param kwargs:
    :return: The generated html data that can be used in the info dock.
    """
    data = OrderedDict()
    items = []
    count = 0
    for field, value in zip(fields, attributes):
        if field == 'mapkey':
            continue
        name = "field_" + str(count)
        if value == NULL:
            value = ""
        data[name] = value
        if isinstance(value, str) and (
                value.lower().endswith('.jpg') or value.lower().endswith('.jpeg') or value.lower().endswith('.png')):
            item = u"<tr><td><a href=""${{{0}}}""><img width=""100%"" src=""${{{0}}}"" /></a></td></tr>".format(name)
        else:
            item = u"<tr><th>{0}</th> <td>${{{1}}}</td></tr>".format(field, name)
        items.append(item)
        count += 1
    rowtemple = Template(''.join(items))
    rowshtml = updateTemplate(data, rowtemple, **kwargs)
    return rowshtml


def results_from_feature(feature: QgsFeature) -> OrderedDict:
    """
    Create a dictionary based on the given feature.
    :param feature: The feature to generate
    :return: A dict with fields and attributes mapped
    """
    attributes = feature.attributes()
    fields = [field.name().lower() for field in feature.fields()]
    return OrderedDict(zip(fields, attributes))
