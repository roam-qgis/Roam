from PyQt4.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel)
from PyQt4.QtCore import Qt
from qgis.core import QgsDataSourceURI
from roam.structs import OrderedDict
import roam.utils

class DatabaseException(Exception):
    def __init__(self, msg):
        self.msg = msg
        roam.utils.error(msg)

class Database(object):
    def __init__(self, sqldatabase):
        self.db = sqldatabase

    @classmethod
    def fromLayer(cls, layer):
        uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
        connectioninfo = {
            "host": uri.host(),
            "database": uri.database(),
            "user": uri.username(),
            "password": uri.password()}
        database = Database.connect(**connectioninfo)
        return database

    @classmethod
    def connect(cls, **connection):
        dbtype = connection.get('type', "QODBC")
        db = QSqlDatabase.addDatabase(dbtype)
        if dbtype == "QSQLITE":
            db.setDatabaseName(connection['database'])
        else:
            constring = "driver={driver};server={host};database={database};uid={user};pwd={password}"
            connection["driver"] = "{SQL Server}"
            constring = constring.format(**connection)
            db.setHostName(connection['host'])
            db.setDatabaseName(constring)
            db.setUserName(connection['user'])
            db.setPassword(connection['password'])

        if not db.open():
            raise DatabaseException(db.lastError().text())
        return Database(db)

    def _query(self, querystring, **mappings):
        query = QSqlQuery(self.db)
        query.prepare(querystring)
        for key, value in mappings.iteritems():
            query.bindValue(":{}".format(key), value)
        return query

    def _recordToDict(self, record):
        """
            Create a normal Python dict out of a QSqlRecord
        """
        values = OrderedDict()
        for index in range(record.count()):
            name = record.fieldName(index)
            values[name] = record.value(index)
        roam.utils.log(values)
        return values

    def query(self, sql, **mappings):
        query = self._query(sql, **mappings)
        if query.exec_():
            while query.next():
                yield self._recordToDict(query.record())

        if query.lastError().isValid():
            print query.lastError().text()
            raise DatabaseException(query.lastError().text())

    def querymodel(self, sql, **mappings):
        query = self._query(sql, **mappings)
        if query.exec_():
            model = QSqlQueryModel()
            model.setQuery(query)
            return model
        else:
           raise DatabaseException(query.lastError().text()) 