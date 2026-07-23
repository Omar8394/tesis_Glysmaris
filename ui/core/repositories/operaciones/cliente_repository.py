"""
============================================================
Sistema La Dulce Tía

Archivo:
    cliente_repository.py

Responsabilidad:
    Acceso a datos de la tabla CLIENTES.
    Solo persistencia, sin reglas de negocio.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ui.core.repositories.base.crud_repository import CRUDRepository


class ClienteRepository(CRUDRepository):
    """
    Repositorio de clientes.
    """

    def crear(self, datos: Dict[str, Any]) -> Any:
        cursor = self._cursor()
        cursor.execute(
            """
            INSERT INTO CLIENTES (nombre, cedula, telefono, direccion, observaciones)
            VALUES (%(nombre)s, %(cedula)s, %(telefono)s, %(direccion)s, %(observaciones)s)
            """,
            {
                "nombre": datos.get("nombre"),
                "cedula": datos.get("cedula"),
                "telefono": datos.get("telefono"),
                "direccion": datos.get("direccion"),
                "observaciones": datos.get("observaciones"),
            },
        )
        self._commit()
        return cursor.lastrowid

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> bool:
        cursor = self._cursor()
        cursor.execute(
            """
            UPDATE CLIENTES
            SET nombre = %(nombre)s,
                cedula = %(cedula)s,
                telefono = %(telefono)s,
                direccion = %(direccion)s,
                observaciones = %(observaciones)s
            WHERE id_cliente = %(id_cliente)s
            """,
            {
                "id_cliente": identificador,
                "nombre": datos.get("nombre"),
                "cedula": datos.get("cedula"),
                "telefono": datos.get("telefono"),
                "direccion": datos.get("direccion"),
                "observaciones": datos.get("observaciones"),
            },
        )
        self._commit()
        return cursor.rowcount > 0

    def eliminar(self, identificador: Any) -> bool:
        # No se borra físicamente: un cliente puede tener ventas o
        # deudas asociadas (VENTAS.id_cliente, CUENTAS_POR_COBRAR.id_cliente).
        # Se desactiva para conservar el historial.
        cursor = self._cursor()
        cursor.execute(
            "UPDATE CLIENTES SET activo = FALSE WHERE id_cliente = %s",
            (identificador,),
        )
        self._commit()
        return cursor.rowcount > 0

    def obtener(self, identificador: Any) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM CLIENTES WHERE id_cliente = %s",
            (identificador,),
        )
        return cursor.fetchone()

    def listar(self) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM CLIENTES WHERE activo = TRUE ORDER BY nombre"
        )
        return cursor.fetchall()

    def buscar(self, texto: str) -> List[Dict]:
        cursor = self._cursor()
        patron = f"%{texto}%"
        cursor.execute(
            """
            SELECT * FROM CLIENTES
            WHERE activo = TRUE
              AND (nombre LIKE %s OR cedula LIKE %s OR telefono LIKE %s)
            ORDER BY nombre
            """,
            (patron, patron, patron),
        )
        return cursor.fetchall()

    def obtener_por_cedula(self, cedula: str) -> Optional[Dict]:
        """
        Usado para evitar duplicar un cliente que ya existe
        cuando se captura desde el módulo de Ventas.
        """
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM CLIENTES WHERE cedula = %s",
            (cedula,),
        )
        return cursor.fetchone()
