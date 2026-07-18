"""
============================================================
Sistema La Dulce Tía

Archivo:
    factory.py

Responsabilidad:
    Fábrica de conexiones a bases de datos.
    Centraliza la creación de DatabaseManager para cada base de datos.
============================================================
"""

"""
Fábrica que proporciona instancias de DatabaseManager según la base de datos.
"""
from ui.core.database.connection import DatabaseManager
from ui.core.database.config import DB_HOST, DB_USER, DB_PASSWORD, DB_SEGURIDAD, DB_OPERACIONES

class DatabaseFactory:
    _instances = {}

    @classmethod
    def get_seguridad(cls) -> DatabaseManager:
        if "seguridad" not in cls._instances:
            cls._instances["seguridad"] = DatabaseManager(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_SEGURIDAD,
            )
        return cls._instances["seguridad"]

    @classmethod
    def get_operaciones(cls) -> DatabaseManager:
        if "operaciones" not in cls._instances:
            cls._instances["operaciones"] = DatabaseManager(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_OPERACIONES,
            )
        return cls._instances["operaciones"]