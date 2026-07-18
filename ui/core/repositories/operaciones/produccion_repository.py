"""
============================================================
Sistema La Dulce Tía

Archivo:
    produccion_repository.py

Responsabilidad:
    Repositorio para el módulo de producción.
    Implementa todos los métodos abstractos de CRUDRepository.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, date

from ui.core.repositories.base.crud_repository import CRUDRepository


class ProduccionRepository(CRUDRepository):
    """Repositorio para operaciones de producción."""

    def __init__(self, conexion):
        super().__init__(conexion)

    # =========================================================
    # MÉTODOS OBLIGATORIOS DE CRUDRepository
    # =========================================================

    def crear(self, datos: Dict[str, Any]) -> Any:
        """Crea una nueva orden (implementación de CRUDRepository)."""
        return self.crear_orden(datos)

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> bool:
        """Actualiza una orden existente."""
        return self.actualizar_orden(identificador, datos)

    def eliminar(self, identificador: Any) -> bool:
        """Elimina una orden."""
        return self.eliminar_orden(identificador)

    def obtener(self, identificador: Any) -> Optional[Dict]:
        """Obtiene una orden por su ID."""
        return self.obtener_orden(identificador)

    def listar(self) -> List[Dict]:
        """Lista todas las órdenes."""
        return self.listar_ordenes()

    def buscar(self, texto: str) -> List[Dict]:
        """Busca órdenes por texto."""
        return self.listar_ordenes({"buscar": texto})

    # =========================================================
    # MÉTODOS ESPECÍFICOS DE PRODUCCIÓN
    # =========================================================

    def crear_orden(self, datos: Dict[str, Any]) -> int:
        """Inserta una nueva orden y devuelve su ID."""
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_ORDENES
                (numero_orden, fecha_planificada, hora_estimada,
                 prioridad, responsable, estado, notas,
                 costo_estimado, tiempo_estimado_minutos,
                 creado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos["numero_orden"],
            datos["fecha_planificada"],
            datos.get("hora_estimada"),
            datos.get("prioridad", "media"),
            datos.get("responsable", ""),
            datos.get("estado", "pendiente"),
            datos.get("notas", ""),
            datos.get("costo_estimado", 0.0),
            datos.get("tiempo_estimado_minutos", 0),
            datos.get("creado_por", ""),
        ))
        self._commit()
        return cursor.lastrowid

    def actualizar_orden(self, id_orden: int, datos: Dict[str, Any]) -> bool:
        cursor = self._cursor()
        cursor.execute("""
            UPDATE PRODUCCION_ORDENES SET
                fecha_planificada = %s,
                hora_estimada = %s,
                prioridad = %s,
                responsable = %s,
                estado = %s,
                notas = %s,
                costo_estimado = %s,
                costo_real = %s,
                tiempo_estimado_minutos = %s,
                tiempo_real_minutos = %s,
                fecha_inicio = %s,
                fecha_fin = %s
            WHERE id_orden = %s
        """, (
            datos.get("fecha_planificada"),
            datos.get("hora_estimada"),
            datos.get("prioridad"),
            datos.get("responsable"),
            datos.get("estado"),
            datos.get("notas"),
            datos.get("costo_estimado", 0.0),
            datos.get("costo_real", 0.0),
            datos.get("tiempo_estimado_minutos", 0),
            datos.get("tiempo_real_minutos", 0),
            datos.get("fecha_inicio"),
            datos.get("fecha_fin"),
            id_orden,
        ))
        self._commit()
        return cursor.rowcount > 0

    def obtener_orden(self, id_orden: int) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PRODUCCION_ORDENES WHERE id_orden = %s", (id_orden,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def listar_ordenes(self, filtros: Optional[Dict] = None) -> List[Dict]:
        query = "SELECT * FROM PRODUCCION_ORDENES WHERE 1=1"
        params = []

        if filtros:
            if "estado" in filtros and filtros["estado"] != "Todos":
                query += " AND estado = %s"
                params.append(filtros["estado"])
            if "prioridad" in filtros and filtros["prioridad"] != "todas":
                query += " AND prioridad = %s"
                params.append(filtros["prioridad"])
            if "buscar" in filtros:
                query += " AND (numero_orden LIKE %s OR responsable LIKE %s)"
                term = f"%{filtros['buscar']}%"
                params.extend([term, term])

        query += " ORDER BY fecha_creacion DESC"

        cursor = self._cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def eliminar_orden(self, id_orden: int) -> bool:
        cursor = self._cursor()
        cursor.execute("DELETE FROM PRODUCCION_ORDENES WHERE id_orden = %s", (id_orden,))
        self._commit()
        return cursor.rowcount > 0

    def actualizar_estado_orden(self, id_orden: int, nuevo_estado: str) -> bool:
        cursor = self._cursor()
        # Obtener estado anterior
        orden = self.obtener_orden(id_orden)
        if not orden:
            return False
        estado_anterior = orden["estado"]

        cursor.execute(
            "UPDATE PRODUCCION_ORDENES SET estado = %s WHERE id_orden = %s",
            (nuevo_estado, id_orden)
        )
        self._commit()

        # Registrar historial si cambió
        if cursor.rowcount > 0 and estado_anterior != nuevo_estado:
            self._crear_historial_estado(id_orden, estado_anterior, nuevo_estado)

        return cursor.rowcount > 0

    def _crear_historial_estado(self, id_orden: int, estado_anterior: str, estado_nuevo: str):
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_HISTORIAL_ESTADOS
                (id_orden, estado_anterior, estado_nuevo)
            VALUES (%s, %s, %s)
        """, (id_orden, estado_anterior, estado_nuevo))
        self._commit()

    # --- Detalles ---

    def crear_detalle(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_DETALLE
                (id_orden, id_producto, id_presentacion,
                 cantidad_planificada, cantidad_obtenida,
                 precio_final, modificaciones, costo_calculado,
                 disponible_venta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos["id_orden"],
            datos["id_producto"],
            datos.get("id_presentacion"),
            datos.get("cantidad_planificada", 1),
            datos.get("cantidad_obtenida", 0),
            datos.get("precio_final", 0.0),
            datos.get("modificaciones", ""),
            datos.get("costo_calculado", 0.0),
            datos.get("disponible_venta", True),
        ))
        self._commit()
        return cursor.lastrowid

    def listar_detalles_por_orden(self, id_orden: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PRODUCCION_DETALLE WHERE id_orden = %s", (id_orden,))
        return [dict(row) for row in cursor.fetchall()]

    def actualizar_detalle(self, id_detalle: int, datos: Dict[str, Any]) -> bool:
        cursor = self._cursor()
        cursor.execute("""
            UPDATE PRODUCCION_DETALLE SET
                cantidad_planificada = %s,
                cantidad_obtenida = %s,
                precio_final = %s,
                modificaciones = %s,
                costo_calculado = %s,
                disponible_venta = %s,
                rendimiento_porcentaje = %s
            WHERE id_detalle = %s
        """, (
            datos.get("cantidad_planificada"),
            datos.get("cantidad_obtenida", 0),
            datos.get("precio_final", 0.0),
            datos.get("modificaciones", ""),
            datos.get("costo_calculado", 0.0),
            datos.get("disponible_venta", True),
            datos.get("rendimiento_porcentaje", 0.0),
            id_detalle,
        ))
        self._commit()
        return cursor.rowcount > 0

    # --- Mermas ---

    def crear_merma(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_MERMAS
                (id_orden, id_detalle, id_producto, cantidad,
                 tipo_merma, motivo, descripcion, costo_asociado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos["id_orden"],
            datos.get("id_detalle"),
            datos.get("id_producto"),
            datos["cantidad"],
            datos["tipo_merma"],
            datos["motivo"],
            datos.get("descripcion", ""),
            datos.get("costo_asociado", 0.0),
        ))
        self._commit()
        return cursor.lastrowid

    def listar_mermas_por_orden(self, id_orden: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PRODUCCION_MERMAS WHERE id_orden = %s", (id_orden,))
        return [dict(row) for row in cursor.fetchall()]

    # --- Subproductos ---

    def crear_subproducto(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_SUBPRODUCTOS
                (id_merma, id_detalle, id_producto_subproducto,
                 cantidad, unidad)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            datos["id_merma"],
            datos.get("id_detalle"),
            datos["id_producto_subproducto"],
            datos["cantidad"],
            datos.get("unidad", ""),
        ))
        self._commit()
        return cursor.lastrowid

    # --- Reservas ---

    def crear_reserva_ingrediente(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_INGREDIENTES_RESERVADOS
                (id_orden, id_detalle, id_producto, id_ingrediente,
                 id_lote, cantidad_reservada, cantidad_consumida, cantidad_devuelta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos["id_orden"],
            datos["id_detalle"],
            datos["id_producto"],
            datos["id_ingrediente"],
            datos.get("id_lote"),
            datos["cantidad_reservada"],
            datos.get("cantidad_consumida", 0.0),
            datos.get("cantidad_devuelta", 0.0),
        ))
        self._commit()
        return cursor.lastrowid

    def listar_reservas_ingredientes_por_orden(self, id_orden: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PRODUCCION_INGREDIENTES_RESERVADOS WHERE id_orden = %s", (id_orden,))
        return [dict(row) for row in cursor.fetchall()]

    def crear_reserva_activo(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_ACTIVOS_RESERVADOS
                (id_orden, id_detalle, id_producto, id_activo,
                 cantidad_reservada, cantidad_consumida)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datos["id_orden"],
            datos["id_detalle"],
            datos["id_producto"],
            datos["id_activo"],
            datos["cantidad_reservada"],
            datos.get("cantidad_consumida", 0.0),
        ))
        self._commit()
        return cursor.lastrowid

    def listar_reservas_activos_por_orden(self, id_orden: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PRODUCCION_ACTIVOS_RESERVADOS WHERE id_orden = %s", (id_orden,))
        return [dict(row) for row in cursor.fetchall()]

    # --- Costos ---

    def crear_costo(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_COSTOS
                (id_orden, id_detalle, tipo, descripcion,
                 valor_estimado, valor_real)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datos["id_orden"],
            datos.get("id_detalle"),
            datos["tipo"],
            datos["descripcion"],
            datos.get("valor_estimado", 0.0),
            datos.get("valor_real", 0.0),
        ))
        self._commit()
        return cursor.lastrowid

    def listar_costos_por_orden(self, id_orden: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PRODUCCION_COSTOS WHERE id_orden = %s", (id_orden,))
        return [dict(row) for row in cursor.fetchall()]

    # --- Análisis ---

    def crear_analisis(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO PRODUCCION_ANALISIS
                (id_orden, id_producto, cantidad_solicitada,
                 cantidad_posible, resultado)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            datos["id_orden"],
            datos["id_producto"],
            datos["cantidad_solicitada"],
            datos["cantidad_posible"],
            datos["resultado"],
        ))
        self._commit()
        return cursor.lastrowid

    def crear_faltante(self, datos: Dict[str, Any]) -> int:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO ANALISIS_FALTANTES
                (id_analisis, id_ingrediente, id_activo,
                 necesario, disponible, faltante)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datos["id_analisis"],
            datos.get("id_ingrediente"),
            datos.get("id_activo"),
            datos["necesario"],
            datos["disponible"],
            datos["faltante"],
        ))
        self._commit()
        return cursor.lastrowid

    def listar_analisis_por_orden(self, id_orden: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM PRODUCCION_ANALISIS WHERE id_orden = %s", (id_orden,))
        return [dict(row) for row in cursor.fetchall()]

    # --- Historial ---

    def listar_historial_por_orden(self, id_orden: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("""
            SELECT * FROM PRODUCCION_HISTORIAL_ESTADOS
            WHERE id_orden = %s
            ORDER BY fecha_cambio ASC
        """, (id_orden,))
        return [dict(row) for row in cursor.fetchall()]

    # --- Útiles ---

    def obtener_ultimo_numero_orden(self) -> Optional[str]:
        cursor = self._cursor()
        cursor.execute("""
            SELECT numero_orden FROM PRODUCCION_ORDENES
            ORDER BY id_orden DESC LIMIT 1
        """)
        row = cursor.fetchone()
        return row[0] if row else None

    def contar_ordenes_por_estado(self, estado: str) -> int:
        cursor = self._cursor()
        cursor.execute("SELECT COUNT(*) FROM PRODUCCION_ORDENES WHERE estado = %s", (estado,))
        return cursor.fetchone()[0]