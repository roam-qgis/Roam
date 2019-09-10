import os
import sqlite3
import uuid

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from roam.editorwidgets.core import EditorWidget, createwidget, widgetwrapper


class MultiImageWidget(EditorWidget):
    widgettype = 'MultiImage'

    def __init__(self, *args, **kwargs):
        super(MultiImageWidget, self).__init__(*args, **kwargs)
        self.widgets = []
        self.linkid = None
        self.modified = True

    def createWidget(self, parent=None):
        widget = QWidget(parent)
        return widget

    def initWidget(self, widget, config):
        if not widget.layout():
            widget.setLayout(QVBoxLayout())
            widget.layout().setContentsMargins(0, 0, 0, 0)

        dbconfig = config['dboptions']
        for i in range(dbconfig['maximages']):
            innerwidget = createwidget("Image")
            wrapper = widgetwrapper("Image", innerwidget, config, self.layer, self.label, self.field, self.context)
            wrapper.largewidgetrequest.connect(self.largewidgetrequest.emit)
            wrapper.photo_id = None
            wrapper.photo_number = i
            widget.layout().addWidget(innerwidget)
            self.widgets.append((innerwidget, wrapper))

    def setvalue(self, value):
        """
        The multi image widget will take the ID to lookup in the external DB.
        """
        import uuid

        if not value:
            self.linkid = str(uuid.uuid4())
        else:
            self.linkid = value

        table = self.DBConfig['table']
        db = self.DB()
        photos = db.execute("""
        SELECT photo_id, photo
        FROM '{0}'
        WHERE linkid = '{1}'
        ORDER BY photo_number
        """.format(table, self.linkid))
        for count, row in enumerate(photos):
            try:
                widget, wrapper = self.widgets[count]
                data = row[1]
                photo_id = row[0]
                wrapper.photo_id = photo_id
                wrapper.setvalue(data)
            except IndexError:
                break

        db.close()

    def value(self):
        """
        The current ID of the image link.
        """
        if not self.linkid:
            self.linkid = str(uuid.uuid4())

        return self.linkid

    def updatePhoto(self, db, photo_id, photo):
        table = self.DBConfig['table']
        sql = """UPDATE '{0}' SET photo = '{2}',
                                  timestamp = '{4}'
                                  WHERE photo_id = '{3}'
                                  AND linkid = '{1}'""".format(table,
                                                               self.linkid,
                                                               photo,
                                                               photo_id,
                                                               QDateTime.currentDateTime().toLocalTime().toString())
        db.execute(sql)

    def DB(self):
        dbconfig = self.config['dboptions']
        dbpath = dbconfig['dbpath']
        dbpath = os.path.join(self.config['context']['project'].datafolder(), dbpath)
        table = dbconfig['table']
        db = sqlite3.connect(dbpath)
        db.enable_load_extension(True)
        db.load_extension("spatialite4.dll")
        return db

    @property
    def DBConfig(self):
        dbconfig = self.config['dboptions']
        return dbconfig

    def insertPhoto(self, db, photo_id, photo, number):
        table = self.DBConfig['table']
        linkcode = self.DBConfig['linkcode']
        date = QDateTime.currentDateTime().toLocalTime().toString()
        sql = "INSERT INTO '{0}' (linkid, photo, photo_id, timestamp, photo_number, linkname) VALUES ('{1}', '{2}', '{3}', '{4}', {5}, '{6}')".format(
            table, self.linkid, photo, photo_id, date, number, linkcode)
        db.execute(sql)

    def save(self):
        """
        Save the images inside this widget to the linked DB.
        """
        db = self.DB()
        for widget, wrapper in self.widgets:
            value = wrapper.value()
            if not wrapper.modified:
                continue

            if wrapper.photo_id is None:
                if value:
                    wrapper.photo_id = str(uuid.uuid4())
                    self.insertPhoto(db, wrapper.photo_id, value, wrapper.photo_number)
            else:
                if not value:
                    value = ''
                self.updatePhoto(db, wrapper.photo_id, value)
        db.commit()
        db.close()
        return True