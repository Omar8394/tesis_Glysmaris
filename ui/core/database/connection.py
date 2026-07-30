"""
Gestor de conexiones a base de datos.
"""
import threading
import pymysql


class DatabaseManager:
    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        # ⚠️ Antes había un único self._connection compartido por TODOS
        # los threads (Flet dispara on_change/on_click en un thread pool).
        # pymysql no es thread-safe: dos threads escribiendo/leyendo al
        # mismo tiempo sobre el mismo socket corrompen la conversación
        # del protocolo (o pierden un commit). Con threading.local(),
        # cada thread tiene su propia conexión, sin tocar nada del resto
        # del código (Repository/CRUDRepository no se enteran del cambio).
        self._local = threading.local()

    def connect(self):
        conexion = getattr(self._local, "connection", None)
        if conexion is None or not conexion.open:
            conexion = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
            self._local.connection = conexion
        return conexion

    def cursor(self):
        return self.connect().cursor()

    def commit(self):
        self.connect().commit()

    def rollback(self):
        self.connect().rollback()

    def close(self):
        conexion = getattr(self._local, "connection", None)
        if conexion:
            conexion.close()
            self._local.connection = None