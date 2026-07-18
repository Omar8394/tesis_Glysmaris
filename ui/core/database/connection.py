"""
Gestor de conexiones a base de datos.
"""
import pymysql

class DatabaseManager:
    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self._connection = None

    def connect(self):
        if self._connection is None:
            self._connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
        return self._connection

    def cursor(self):
        return self.connect().cursor()

    def commit(self):
        self.connect().commit()

    def rollback(self):
        self.connect().rollback()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None