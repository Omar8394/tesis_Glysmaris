"""
============================================================
Sistema La Dulce Tía

Repositorio de Recetas

Responsabilidad:
    Acceso a datos de RECETAS y RECETA_INGREDIENTES.

    Hereda de CRUDRepository y usa la conexión inyectada.
    No contiene lógica de negocio.
============================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ui.core.repositories.base.crud_repository import CRUDRepository


class RecetasRepository(CRUDRepository):
    """
    Repositorio para operaciones con recetas y sus ingredientes.
    """

    def __init__(self, conexion):
        super().__init__(conexion)

    # ============================================================
    # MÉTODOS CRUD OBLIGATORIOS (abstractos)
    # ============================================================

    def crear(self, datos: Dict[str, Any]) -> int:
        query = """
            INSERT INTO RECETAS
            (nombre_receta, tipo_receta, descripcion, costo_ingredientes,
             rendimiento_cantidad, rendimiento_unidad, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            datos["nombre"],
            datos["tipo"],
            datos.get("descripcion", ""),
            datos.get("costo_ingredientes", 0),
            datos.get("rendimiento_cantidad", 1),
            datos.get("rendimiento_unidad", "unidad"),
            datetime.now(),
        )
        cursor = self._cursor()
        cursor.execute(query, valores)
        self._commit()
        return cursor.lastrowid

    def actualizar(self, identificador: int, datos: Dict[str, Any]) -> bool:
        query = """
            UPDATE RECETAS
            SET nombre_receta=%s, tipo_receta=%s, descripcion=%s, costo_ingredientes=%s,
                rendimiento_cantidad=%s, rendimiento_unidad=%s
            WHERE id_receta=%s
        """
        valores = (
            datos["nombre"],
            datos["tipo"],
            datos.get("descripcion", ""),
            datos.get("costo_ingredientes", 0),
            datos.get("rendimiento_cantidad", 1),
            datos.get("rendimiento_unidad", "unidad"),
            identificador,
        )
        cursor = self._cursor()
        cursor.execute(query, valores)
        self._commit()
        return cursor.rowcount > 0

    def eliminar(self, identificador: int) -> bool:
        cursor = self._cursor()
        # Desvincular productos
        cursor.execute(
            "UPDATE PRODUCTOS SET receta_id = NULL WHERE receta_id = %s",
            (identificador,),
        )
        cursor.execute("DELETE FROM RECETAS WHERE id_receta = %s", (identificador,))
        self._commit()
        return cursor.rowcount > 0

    def obtener(self, identificador: int) -> Optional[Dict]:
        query = "SELECT * FROM RECETAS WHERE id_receta = %s"
        cursor = self._cursor()
        cursor.execute(query, (identificador,))
        return cursor.fetchone()

    def listar(self) -> List[Dict]:
        query = """
            SELECT id_receta, nombre_receta, tipo_receta, descripcion, costo_ingredientes,
                   rendimiento_cantidad, rendimiento_unidad, fecha_creacion
            FROM RECETAS
            ORDER BY nombre_receta
        """
        cursor = self._cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def buscar(self, texto: str) -> List[Dict]:
        query = """
            SELECT id_receta, nombre_receta, tipo_receta, descripcion, costo_ingredientes,
                   rendimiento_cantidad, rendimiento_unidad, fecha_creacion
            FROM RECETAS
            WHERE LOWER(nombre_receta) LIKE LOWER(%s)
            ORDER BY nombre_receta
        """
        cursor = self._cursor()
        cursor.execute(query, (f"{texto}%",))
        return cursor.fetchall()

    # ============================================================
    # MÉTODOS ESPECÍFICOS DE RECETAS
    # ============================================================

    def actualizar_costo(self, id_receta: int, costo: float) -> bool:
        """
        Actualiza únicamente el costo de ingredientes de una receta,
        sin tocar nombre/tipo/descripción. Usado para refrescar el costo
        cuando cambia el precio de un ingrediente en el inventario.
        """
        query = "UPDATE RECETAS SET costo_ingredientes = %s WHERE id_receta = %s"
        cursor = self._cursor()
        cursor.execute(query, (costo, id_receta))
        self._commit()
        return cursor.rowcount > 0

    def obtener_por_tipo(self, tipo: str) -> List[Dict]:
        query = """
            SELECT id_receta, nombre_receta, costo_ingredientes
            FROM RECETAS
            WHERE tipo_receta = %s
            ORDER BY nombre_receta
        """
        cursor = self._cursor()
        cursor.execute(query, (tipo,))
        return cursor.fetchall()

    def obtener_ingredientes(self, id_receta: int) -> List[Dict]:
        """
        Devuelve los ingredientes de una receta con sus cantidades y unidades.
        NOTA: NO incluye costo_unitario porque esa columna está en LOTES_INVENTARIO.
        """
        query = """
            SELECT
                i.id_ingrediente,
                i.nombre_ingrediente,
                i.unidad_medida,
                ri.cantidad_necesaria,
                ri.unidad
            FROM RECETA_INGREDIENTES ri
            INNER JOIN INGREDIENTES i ON i.id_ingrediente = ri.id_ingrediente
            WHERE ri.id_receta = %s
        """
        cursor = self._cursor()
        cursor.execute(query, (id_receta,))
        return cursor.fetchall()

    def reemplazar_ingredientes(self, id_receta: int, ingredientes: List[Dict]) -> bool:
        """
        Reemplaza todos los ingredientes de una receta por la lista proporcionada.
        Cada elemento debe tener: id_ingrediente, cantidad, unidad.
        """
        cursor = self._cursor()

        # Eliminar ingredientes actuales
        cursor.execute(
            "DELETE FROM RECETA_INGREDIENTES WHERE id_receta = %s",
            (id_receta,),
        )

        # Insertar los nuevos
        for ing in ingredientes:
            cursor.execute(
                """
                INSERT INTO RECETA_INGREDIENTES
                (id_receta, id_ingrediente, cantidad_necesaria, unidad)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    id_receta,
                    ing["id_ingrediente"],
                    ing["cantidad"],
                    ing["unidad"],
                ),
            )

        self._commit()
        return True