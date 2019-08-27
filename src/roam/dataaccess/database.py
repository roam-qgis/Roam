"""
Module for doing database access using the layer as the source.

Provides methods to run a query against a data source (mainly SQLITE) and return
the results as a dictionary.
"""
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel)
from qgis.core import QgsDataSourceUri
from roam.structs import OrderedDict
import roam.utils

import re


class DatabaseException(Exception):
    def __init__(self, msg, sql=None):
        super(DatabaseException, self).__init__(msg)
        self.msg = msg
        roam.utils.error(msg)
        roam.utils.info(sql)


class Database(object):
    def __init__(self, sqldatabase):
        self.db = sqldatabase
        self.form = None

    def close(self):
        self.db.close()

    @classmethod
    def fromLayer(cls, layer):
        source = layer.source()
        uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        if ".sqlite" in source:
            try:
                index = source.index("|")
                source = source[:index]
            except ValueError:
                pass
            if uri.database():
                source = uri.database()

            connectioninfo = {"type": "QSQLITE",
                              "database": source}
        else:
            uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
            connectioninfo = {
                "host": uri.host(),
                "database": uri.database(),
                "user": uri.username(),
                "password": uri.password()
            }
        connectioninfo["connectionname"] = layer.id()
        database = Database.connect(**connectioninfo)
        return database

    @classmethod
    def connect(cls, **connection):
        dbtype = connection.get('type', "QODBC")
        connectionname = connection.get("connectionname", hash(tuple(connection.items())))
        db = QSqlDatabase.database(connectionname)
        if not db.isValid():
            db = QSqlDatabase.addDatabase(dbtype, connectionname)

        if dbtype == "QSQLITE":
            db.setDatabaseName(connection['database'])
        else:
            if "constring" in connection:
                db.setDatabaseName(connection['constring'])
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

    def named_query(self, name, values=None):
        """
        Return a query based on the name given.  The query must be defined in the form
        settings under the query: block
        :param name: the name of the query to run
        :param values: A dict of keys and values to use in the query
        :return: A generator with the query results.
        """
        sql, values = self.form.get_query(name, values)
        return self.query(sql, **values)

    def exec_(self, sql, values=None):
        """
        Executes a query with no return data
        :param name:
        :param values:
        :return:
        """
        if not values:
            values = {}
        query = self._query(sql, **values)
        if query.exec_():
            return True
        else:
            if query.lastError().isValid():
                raise DatabaseException(query.lastError().text(), sql)

    def exec_query(self, name, values):
        """
        Executes a query with no return data
        :param name:
        :param values:
        :return:
        """
        sql, values = self.form.get_query(name, values)
        query = self._query(sql, **values)
        if query.exec_():
            return True

        if query.lastError().isValid():
            raise DatabaseException(query.lastError().text())

    def _query(self, querystring, **mappings):
        querystring = querystring.replace(r"\r\n", " ")
        query = QSqlQuery(self.db)
        query.prepare(querystring)
        for key, value in mappings.iteritems():
            bindvalue = ":{}".format(key)
            if re.search(r"{}\b".format(bindvalue), querystring):
                query.bindValue(bindvalue, value)
        return query

    def _recordToDict(self, record):
        """
            Create a normal Python dict out of a QSqlRecord
        """
        values = OrderedDict()
        for index in range(record.count()):
            name = record.fieldName(index)
            values[name] = record.value(index)
        return values

    def query(self, sql, **mappings):
        sql = sql.replace(r"\r\n", " ")
        query = self._query(sql, **mappings)
        if query.exec_():
            while query.next():
                yield self._recordToDict(query.record())

        if query.lastError().isValid():
            text = query.lastError().text()
            raise DatabaseException(text, sql)

    def querymodel(self, sql, **mappings):
        sql = sql.replace(r"\r\n", " ")
        query = self._query(sql, **mappings)
        if query.exec_():
            model = QSqlQueryModel()
            model.setQuery(query)
            return model
        else:
            raise DatabaseException(query.lastError().text(), sql)
