"""
============================================================
Sistema La Dulce Tía

Archivo:
    repository.py

Responsabilidad:
    Clase base para repositorios.

    Proporciona helpers de conexión (cursor, commit, rollback).
    No impone métodos CRUD; eso lo hace CRUDRepository.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from abc import ABC


class Repository(ABC):
    """
    Clase base para todos los repositorios.
    Solo contiene helpers de conexión.
    """

    def __init__(self, conexion):
        self._conexion = conexion

    def _cursor(self):
        return self._conexion.cursor()

    def _commit(self):
        self._conexion.commit()

    def _rollback(self):
        self._conexion.rollback()

    def cerrar(self):
        self._conexion.close()