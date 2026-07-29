"""
============================================================
Sistema La Dulce Tía

Archivo:
    estadisticas_repository.py

Responsabilidad:
    Acceso a datos para el módulo de Estadísticas y Analítica.

    Centraliza las consultas SQL de rendimiento de productos,
    minería de temporadas y reporte de mermas.

    No contiene reglas de negocio: sólo obtiene y da forma
    (agregaciones SQL) a los datos. La interpretación de esos
    datos (umbrales, clasificación alta/baja demanda, etc.)
    vive en EstadisticasService.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List

from ui.core.repositories.base.repository import Repository


class EstadisticasRepository(Repository):
    """
    Repositorio de sólo lectura para el módulo de Estadísticas.

    No hereda de CRUDRepository porque este módulo no gestiona
    una entidad propia (no hay crear/actualizar/eliminar):
    únicamente agrega datos ya existentes de VENTAS,
    DETALLE_VENTA, PRODUCTOS y PRODUCCION_MERMAS.
    """

    def __init__(self, conexion):
        super().__init__(conexion)

    # ------------------------------------------------------------------
    # Rendimiento de productos
    # ------------------------------------------------------------------
    def obtener_rendimiento_productos(
        self,
        dias: int = 30,
        limite: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve los productos más vendidos en el rango de días
        especificado, ordenados de mayor a menor unidades vendidas.
        """

        sql = """
            SELECT
                p.id_producto,
                p.nombre_producto,
                SUM(dv.cantidad) AS total_unidades,
                SUM(dv.subtotal) AS total_generado
            FROM DETALLE_VENTA dv
            JOIN VENTAS v ON v.id_venta = dv.id_venta
            JOIN PRODUCTOS p ON p.id_producto = dv.id_producto
            WHERE v.estado = 'completada'
              AND v.fecha_venta >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
            GROUP BY p.id_producto, p.nombre_producto
            ORDER BY total_unidades DESC
            LIMIT %s
        """

        cursor = self._conexion.cursor(dictionary=True)

        try:
            cursor.execute(sql, (dias, limite))
            return cursor.fetchall()
        finally:
            cursor.close()

    # ------------------------------------------------------------------
    # Minería de temporadas (datos crudos, sin clasificar)
    # ------------------------------------------------------------------
    def obtener_ventas_anuales_por_producto(self) -> List[Dict[str, Any]]:
        """
        Devuelve, por producto, las unidades vendidas en el mes
        actual junto con el total vendido en el último año.

        La clasificación de temporada (alta/baja demanda) es
        una regla de negocio y se calcula en el servicio, no aquí.
        """

        sql = """
            SELECT
                p.id_producto,
                p.nombre_producto,
                SUM(
                    CASE WHEN MONTH(v.fecha_venta) = MONTH(CURRENT_DATE)
                    THEN dv.cantidad ELSE 0 END
                ) AS ventas_mes_actual,
                SUM(dv.cantidad) AS ventas_totales_anio
            FROM DETALLE_VENTA dv
            JOIN VENTAS v ON v.id_venta = dv.id_venta
            JOIN PRODUCTOS p ON p.id_producto = dv.id_producto
            WHERE v.estado = 'completada'
              AND v.fecha_venta >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR)
            GROUP BY p.id_producto, p.nombre_producto
            HAVING ventas_totales_anio > 0
        """

        cursor = self._conexion.cursor(dictionary=True)

        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    # ------------------------------------------------------------------
    # Mermas
    # ------------------------------------------------------------------
    def obtener_reporte_mermas(self, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las pérdidas por producto/insumo con mayor costo
        asociado, agrupadas por motivo.
        """

        sql = """
            SELECT
                COALESCE(p.nombre_producto, pm.descripcion, 'Otro') AS item,
                pm.motivo,
                SUM(pm.cantidad) AS cantidad_perdida,
                SUM(pm.costo_asociado) AS costo_total_perdida
            FROM PRODUCCION_MERMAS pm
            LEFT JOIN PRODUCTOS p ON p.id_producto = pm.id_producto
            GROUP BY item, pm.motivo
            ORDER BY costo_total_perdida DESC
            LIMIT %s
        """

        cursor = self._conexion.cursor(dictionary=True)

        try:
            cursor.execute(sql, (limite,))
            return cursor.fetchall()
        finally:
            cursor.close()
