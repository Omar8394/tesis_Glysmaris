from __future__ import annotations
from typing import Any, Dict, List, Optional
from ui.core.repositories.base.crud_repository import CRUDRepository


class ParametrosNegocioRepository(CRUDRepository):
    """
    Repositorio para PARAMETROS_NEGOCIO.

    A diferencia de otras tablas del sistema, esta es una tabla de
    configuración de fila única: no hay altas/bajas de "muchos"
    parámetros, solo un registro que se crea la primera vez y se
    actualiza después (mano de obra y horas de trabajo al mes).

    Se mantienen los métodos CRUD estándar (crear/actualizar/eliminar/
    obtener/listar) por compatibilidad con CRUDRepository, y además se
    exponen `obtener_actual()` y `guardar()` como la forma "natural" de
    trabajar con esta tabla desde ParametrosNegocioService.
    """

    def __init__(self, conexion):
        super().__init__(conexion)

    def _to_dict(self, parametros) -> Dict:
        return {
            "id_parametro": parametros.id_parametro,
            "costo_hora_trabajo": parametros.costo_hora_trabajo,
            "horas_trabajo_mes": parametros.horas_trabajo_mes,
            "fecha_actualizacion": parametros.fecha_actualizacion,
        }

    def _from_dict(self, data: Dict) -> Dict:
        return data

    def crear(self, datos: Dict[str, Any]) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PARAMETROS_NEGOCIO (costo_hora_trabajo, horas_trabajo_mes)
            VALUES (%s, %s)
        """, (
            datos.get("costo_hora_trabajo", 0.0),
            datos.get("horas_trabajo_mes", 0.0),
        ))
        self._commit()
        nuevo_id = cursor.lastrowid
        return self.obtener(nuevo_id)

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> bool:
        cursor = self._cursor()
        cursor.execute("""
            UPDATE PARAMETROS_NEGOCIO SET
                costo_hora_trabajo=%s,
                horas_trabajo_mes=%s,
                fecha_actualizacion=NOW()
            WHERE id_parametro=%s
        """, (
            datos.get("costo_hora_trabajo", 0.0),
            datos.get("horas_trabajo_mes", 0.0),
            identificador,
        ))
        self._commit()
        return cursor.rowcount > 0

    def eliminar(self, identificador: Any) -> bool:
        cursor = self._cursor()
        cursor.execute("DELETE FROM PARAMETROS_NEGOCIO WHERE id_parametro=%s", (identificador,))
        self._commit()
        return cursor.rowcount > 0

    def obtener(self, identificador: Any) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PARAMETROS_NEGOCIO WHERE id_parametro=%s", (identificador,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def listar(self) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PARAMETROS_NEGOCIO ORDER BY id_parametro")
        return [dict(row) for row in cursor.fetchall()]

    def buscar(self, texto: str) -> List[Dict]:
        """
        No aplica realmente a una tabla de configuración de fila
        única (no hay texto libre por el que buscar), pero se
        implementa para cumplir con la interfaz de CRUDRepository.
        Devuelve el registro actual sin filtrar.
        """
        return self.listar()

    # =====================================================
    # Métodos "naturales" para una tabla de fila única
    # =====================================================

    def obtener_actual(self) -> Optional[Dict]:
        """
        Devuelve el único registro de parámetros del negocio (el más
        reciente, por si alguna vez quedara más de uno). Si todavía no
        se cargó nada, devuelve None.
        """
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PARAMETROS_NEGOCIO ORDER BY id_parametro DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def guardar(self, datos: Dict[str, Any]) -> Optional[Dict]:
        """
        Crea el registro de parámetros si todavía no existe, o
        actualiza el existente. Es el punto de entrada que debería
        usar el servicio para no tener que preocuparse por si es la
        primera vez que se configura el negocio o no.
        """
        actual = self.obtener_actual()
        if actual:
            self.actualizar(actual["id_parametro"], datos)
            return self.obtener(actual["id_parametro"])
        return self.crear(datos)