import sqlite3
import time
import os
import struct
from PyQt4.QtCore import Qt, QObject, pyqtSignal, QThread, QEvent
from PyQt4.QtGui import QWidget, QGridLayout, QLabel, QListWidgetItem, QStyledItemDelegate, QFontMetricsF, QTextOption
from PyQt4.uic import loadUiType

import roam.api.utils
from roam.flickwidget import FlickCharm
from roam.api.events import RoamEvents
from roam.api.plugins import Page


def resolve(name):
    f = os.path.join(os.path.dirname(__file__), name)
    return f


widget, base = loadUiType(resolve("search.ui"))


def make_rank_func(weights):
    # Taken from http://chipaca.com/post/16877190061/doing-full-text-search-in-sqlite-from-python
    def rank(matchinfo):
        # matchinfo is defined as returning 32-bit unsigned integers
        # in machine byte order
        # http://www.sqlite.org/fts3.html#matchinfo
        # and struct defaults to machine byte order
        matchinfo = struct.unpack("I"*(len(matchinfo)/4), matchinfo)
        it = iter(matchinfo[2:])
        return sum(x[0]*w/x[1]
                   for x, w in zip(zip(it, it, it), weights)
                   if x[1])

    return rank


class IndexBuilder(QObject):
    indexBuilt = pyqtSignal(object, float)
    finished = pyqtSignal()
    
    def __init__(self, indexpath, indexconfig):
        super(IndexBuilder, self).__init__()
        self.indexpath = indexpath
        self.indexconfig = indexconfig

    def build_index(self):
        dbpath = os.path.join(self.indexpath, "index.db")
        self.conn = sqlite3.connect(dbpath)
        c = self.conn.cursor()
        c.execute("DROP TABLE IF EXISTS search")
        c.execute("DROP TABLE IF EXISTS featureinfo")
        c.execute("CREATE TABLE featureinfo(id INTEGER PRIMARY KEY, layer, featureid)")

        def get_columns():
            columns = set()
            for config in self.indexconfig.itervalues():
                for c in config['columns']:
                    columns.add(c)
            return columns

        columns = ','.join(get_columns())
        print columns
        c.execute("CREATE VIRTUAL TABLE search USING fts4({})".format(columns))

        def get_features():
            count = 0
            for layername, config in self.indexconfig.iteritems():
                layer = roam.api.utils.layer_by_name(layername)
                for feature in layer.getFeatures():
                    data = {}
                    for field in config['columns']:
                        value = str(feature[field])
                        data[field] = "{}: {}".format(field, value)
                    fid = feature.id()
                    yield count, layer.name(), fid, data
                    count += 1

        start = time.time()
        for row in get_features():
            c.execute("INSERT INTO featureinfo(id, layer, featureid) VALUES(?, ?, ?)", (row[0], row[1], row[2]))
            data = row[3]
            # HACK
            fields = ",".join(data.keys())
            placeholders = "?," * (len(data.values()))
            placeholders = placeholders.strip(',')
            query = "INSERT INTO search(docid, {0}) VALUES({1}, {2})".format(fields, row[0], placeholders)
            c.execute(query, data.values())

        self.conn.commit()
        self.conn.close()
        self.indexBuilt.emit(dbpath, time.time() - start)
        self.quit()

    def quit(self):
        self.conn.close()
        self.finished.emit()


class SearchPlugin(widget, base, Page):
    title = "Search"
    icon = resolve("search.svg")

    def __init__(self, api, parent=None):
        super(SearchPlugin, self).__init__(parent)
        self.setupUi(self)
        self.api = api
        self.project = None
        self.dbpath = None
        self.flickcharm = FlickCharm()
        self.flickcharm.activateOn(self.resultsView)
        self.searchbox.textChanged.connect(self.search)
        self.searchbox.installEventFilter(self)
        self.resultsView.itemClicked.connect(self.jump_to)
        self.rebuildLabel.linkActivated.connect(self.rebuild_index)
        self.fuzzyCheck.stateChanged.connect(self.fuzzy_changed)
        self.indexbuilder = None
        self.indexthread = None

    def fuzzy_changed(self, state):
        self.search(self.searchbox.text())

    def index_built(self, dbpath, timing):
        self.dbpath = dbpath
        self.resultsView.clear()
        self.searchbox.setEnabled(True)
        print "Index built in: {} seconds".format(timing)

    def eventFilter(self, object, event):
        if event.type() == QEvent.FocusIn:
            RoamEvents.openkeyboard.emit()
        return False

    @property
    def db(self):
        db = sqlite3.connect(self.dbpath)
        db.create_function("rank", 1, make_rank_func((1., .1, 0, 0)))
        return db

    def project_loaded(self, project):
        self.project = project
        self.build_index(project)

    def rebuild_index(self):
        self.build_index(self.project)

    def build_index(self, project):
        self.searchbox.setEnabled(False)
        self.resultsView.setEnabled(False)
        self.resultsView.addItem("Just let me build the search index first....")

        self.indexthread = QThread()
        self.indexbuilder = IndexBuilder(project.folder, project.settings.get("search", {}))
        self.indexbuilder.moveToThread(self.indexthread)

        self.indexbuilder.indexBuilt.connect(self.index_built)
        self.indexbuilder.finished.connect(self.indexthread.quit)
        self.indexthread.started.connect(self.indexbuilder.build_index)
        self.indexthread.finished.connect(self.indexbuilder.quit)

        print "building index"
        self.indexthread.start()

    def search(self, text):
        db = self.db
        c = db.cursor()
        self.resultsView.clear()
        self.resultsView.setEnabled(False)
        if not text:
            return

        if self.fuzzyCheck.isChecked():
            search = "* ".join(text.split()) + "*"
        else:
            search = text
        query = c.execute("""SELECT layer, featureid, snippet(search, '[',']') as snippet
                            FROM search
                            JOIN featureinfo on search.docid = featureinfo.id
                            WHERE search match '{}' LIMIT 100""".format(search)).fetchall()
        for layer, featureid, snippet in query:
            item = QListWidgetItem()
            text = "{}\n {}".format(layer, snippet.replace('\n', ' '))
            item.setText(text)
            item.setData(Qt.UserRole, (layer, featureid, snippet))
            self.resultsView.addItem(item)

        self.resultsView.setEnabled(True)

        if self.resultsView.count() == 0:
            self.resultsView.addItem("No Results")
        db.close()

    def jump_to(self, item):
        data = item.data(32)
        layername, fid = data[0], data[1]
        layer = roam.api.utils.layer_by_name(layername)
        layer.select(fid)
        feature = layer.selectedFeatures()[0]
        self.api.mainwindow.canvas.zoomToSelected(layer)
        layer.removeSelection()
        self.api.mainwindow.showmap()
        RoamEvents.selectionchanged.emit({layer: [feature]})

