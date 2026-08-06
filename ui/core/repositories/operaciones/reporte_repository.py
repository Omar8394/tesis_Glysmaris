"""
============================================================
Sistema La Dulce Tía

Archivo:
    reporte_repository.py

Responsabilidad:
    Repositorio para la consulta de datos históricos
    utilizados en los reportes del sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ReporteRepository:
    """
    Repositorio de reportes. Solo consultas de lectura.

    Nota sobre el cursor: a diferencia de mysql-connector "puro", el
    DatabaseManager de este proyecto no acepta cursor(dictionary=True)
    (ver ingrediente_repository.py, que tampoco lo usa) — el cursor ya
    devuelve cada fila como diccionario por defecto, así que basta con
    self._conexion.cursor() sin argumentos.
    """

    def __init__(self, conexion):
        self._conexion = conexion

    def _cursor(self):
        return self._conexion.cursor()

    # ============================================================
    # 1. HISTORIAL DE INGREDIENTES (Lotes)
    # ============================================================
    def obtener_historial_ingredientes(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve los lotes de ingredientes con su stock actual,
        fechas de ingreso/caducidad y costo.
        Opcionalmente filtrado por rango de fechas de ingreso.
        """
        sql = """
            SELECT
                i.id_ingrediente,
                i.nombre_ingrediente,
                i.unidad_medida,
                l.id_lote,
                l.stock_inicial,
                l.stock_actual,
                l.costo_unitario,
                l.fecha_ingreso,
                l.fecha_caducidad
            FROM LOTES_INVENTARIO l
            JOIN INGREDIENTES i ON l.id_ingrediente = i.id_ingrediente
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            sql += " AND l.fecha_ingreso >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            sql += " AND l.fecha_ingreso <= %s"
            params.append(fecha_fin)
        sql += " ORDER BY l.fecha_ingreso DESC, i.nombre_ingrediente"

        cursor = self._cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    # ============================================================
    # 2. HISTORIAL DE VENTAS
    # ============================================================
    def obtener_historial_ventas(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve las ventas con su cabecera y total.
        Opcionalmente filtrado por fecha de venta.
        """
        sql = """
            SELECT
                v.id_venta,
                v.fecha_venta,
                v.cliente_nombre,
                v.cliente_cedula,
                v.subtotal,
                v.descuento,
                v.total,
                v.estado,
                v.usuario_registro,
                (SELECT COUNT(*) FROM DETALLE_VENTA dv WHERE dv.id_venta = v.id_venta) AS items
            FROM VENTAS v
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            sql += " AND DATE(v.fecha_venta) >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            sql += " AND DATE(v.fecha_venta) <= %s"
            params.append(fecha_fin)
        sql += " ORDER BY v.fecha_venta DESC"

        cursor = self._cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    # ============================================================
    # 3. HISTORIAL DE PRODUCCIÓN
    # ============================================================
    def obtener_historial_produccion(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve las órdenes de producción con resumen de detalles.
        Opcionalmente filtrado por fecha planificada.
        """
        sql = """
            SELECT
                o.id_orden,
                o.numero_orden,
                o.fecha_creacion,
                o.fecha_planificada,
                o.estado,
                o.prioridad,
                o.responsable,
                o.costo_estimado,
                o.costo_real,
                o.tiempo_estimado_minutos,
                o.tiempo_real_minutos,
                (SELECT COUNT(*) FROM PRODUCCION_DETALLE d WHERE d.id_orden = o.id_orden) AS total_productos,
                (SELECT SUM(d.cantidad_planificada) FROM PRODUCCION_DETALLE d WHERE d.id_orden = o.id_orden) AS cantidad_total
            FROM PRODUCCION_ORDENES o
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            sql += " AND DATE(o.fecha_planificada) >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            sql += " AND DATE(o.fecha_planificada) <= %s"
            params.append(fecha_fin)
        sql += " ORDER BY o.fecha_planificada DESC, o.fecha_creacion DESC"

        cursor = self._cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    # ============================================================
    # 4. HISTORIAL DE MERMAS
    # ============================================================
    def obtener_historial_mermas(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve las mermas registradas (de producción y de inventario).
        Opcionalmente filtrado por fecha de registro.
        """
        sql = """
            SELECT
                pm.id_merma,
                pm.cantidad,
                pm.unidad,
                pm.tipo_merma,
                pm.motivo,
                pm.nombre_recuperado,
                pm.costo_asociado,
                pm.fecha_registro,
                COALESCE(p.nombre_producto, pm.nombre_recuperado, '') AS producto_asociado
            FROM PRODUCCION_MERMAS pm
            LEFT JOIN PRODUCTOS p ON pm.id_producto = p.id_producto
            WHERE 1=1
        """
        params = []
        if fecha_inicio:
            sql += " AND DATE(pm.fecha_registro) >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            sql += " AND DATE(pm.fecha_registro) <= %s"
            params.append(fecha_fin)
        sql += " ORDER BY pm.fecha_registro DESC"

        cursor = self._cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()