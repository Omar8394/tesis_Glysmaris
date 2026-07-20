# ui/core/repositories/operaciones/venta_repository.py
"""
============================================================
Sistema La Dulce Tía — VentaRepository
Acceso a datos de ventas: cabecera, detalle, pagos,
consumo de lotes de producción y agregados (activos).
============================================================
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from ui.core.repositories.base.crud_repository import CRUDRepository


class VentaRepository(CRUDRepository):

    # ------------------------------------------------------------
    # Catálogo disponible para vender (agregado por producto)
    # ------------------------------------------------------------
    def listar_productos_disponibles(self) -> List[Dict]:
        """
        Stock vendible real = suma de (cantidad_obtenida - cantidad_vendida)
        de los lotes de producción finalizados y marcados disponible_venta.
        """
        cursor = self._cursor()
        cursor.execute("""
            SELECT
                p.id_producto,
                p.nombre_producto AS nombre,
                p.categoria,
                p.precio_venta,
                SUM(pd.cantidad_obtenida - pd.cantidad_vendida) AS stock_actual
            FROM PRODUCCION_DETALLE pd
            JOIN PRODUCCION_ORDENES po ON po.id_orden = pd.id_orden
            JOIN PRODUCTOS p ON p.id_producto = pd.id_producto
            WHERE pd.disponible_venta = TRUE
              AND po.estado = 'finalizada'
              AND (pd.cantidad_obtenida - pd.cantidad_vendida) > 0
              AND p.activo = TRUE
            GROUP BY p.id_producto, p.nombre_producto, p.categoria, p.precio_venta
            HAVING stock_actual > 0
        """)
        return cursor.fetchall()

    def obtener_lotes_disponibles(self, id_producto: int) -> List[Dict]:
        """Lotes con stock, ordenados FIFO (más antiguo primero)."""
        cursor = self._cursor()
        cursor.execute("""
            SELECT pd.id_detalle, pd.id_orden,
                   (pd.cantidad_obtenida - pd.cantidad_vendida) AS disponible
            FROM PRODUCCION_DETALLE pd
            JOIN PRODUCCION_ORDENES po ON po.id_orden = pd.id_orden
            WHERE pd.id_producto = %s
              AND pd.disponible_venta = TRUE
              AND po.estado = 'finalizada'
              AND (pd.cantidad_obtenida - pd.cantidad_vendida) > 0
            ORDER BY po.fecha_fin ASC, pd.id_detalle ASC
        """, (id_producto,))
        return cursor.fetchall()

    # ------------------------------------------------------------
    # Registro transaccional de la venta
    # ------------------------------------------------------------
    def crear_venta_completa(
        self,
        cabecera: Dict[str, Any],
        items: List[Dict[str, Any]],
        pagos: List[Dict[str, Any]],
    ) -> int:
        """
        cabecera: cliente_nombre, cliente_cedula, cliente_telefono,
                   subtotal, descuento, total, observaciones, usuario_registro
        items:    id_producto, nombre_producto, categoria, presentacion,
                   cantidad, precio_unitario, subtotal,
                   agregados: [{id_activo, nombre_activo, cantidad, costo_unitario, subtotal}]
        pagos:    metodo_pago, monto, referencia
        """
        cursor = self._cursor()
        try:
            cursor.execute("""
                INSERT INTO VENTAS
                    (cliente_nombre, cliente_cedula, cliente_telefono,
                     subtotal, descuento, total, observaciones, usuario_registro)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                cabecera.get('cliente_nombre'),
                cabecera.get('cliente_cedula'),
                cabecera.get('cliente_telefono'),
                cabecera['subtotal'],
                cabecera.get('descuento', 0),
                cabecera['total'],
                cabecera.get('observaciones'),
                cabecera.get('usuario_registro'),
            ))
            id_venta = cursor.lastrowid

            for item in items:
                cursor.execute("""
                    INSERT INTO DETALLE_VENTA
                        (id_venta, id_producto, nombre_producto, categoria,
                         presentacion, cantidad, precio_unitario, subtotal)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    id_venta, item['id_producto'], item['nombre_producto'],
                    item.get('categoria'), item.get('presentacion'),
                    item['cantidad'], item['precio_unitario'], item['subtotal'],
                ))
                id_detalle_venta = cursor.lastrowid

                self._consumir_stock_producto(
                    cursor, id_detalle_venta, item['id_producto'], item['cantidad']
                )

                for agg in item.get('agregados', []):
                    cursor.execute("""
                        INSERT INTO DETALLE_VENTA_AGREGADOS
                            (id_detalle_venta, id_activo, nombre_activo,
                             cantidad, costo_unitario, subtotal)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (
                        id_detalle_venta, agg['id_activo'], agg['nombre_activo'],
                        agg['cantidad'], agg['costo_unitario'], agg['subtotal'],
                    ))
                    cursor.execute("""
                        UPDATE ACTIVOS
                        SET stock_actual = stock_actual - %s
                        WHERE id_activo = %s AND stock_actual IS NOT NULL
                    """, (agg['cantidad'], agg['id_activo']))

            for pago in pagos:
                cursor.execute("""
                    INSERT INTO VENTA_PAGOS (id_venta, metodo_pago, monto, referencia)
                    VALUES (%s,%s,%s,%s)
                """, (id_venta, pago['metodo_pago'], pago['monto'], pago.get('referencia')))

            self._commit()
            return id_venta
        except Exception:
            self._rollback()
            raise

    def _consumir_stock_producto(self, cursor, id_detalle_venta, id_producto, cantidad):
        """Descuenta `cantidad` de los lotes disponibles siguiendo FIFO,
        registrando de dónde salió cada porción en VENTA_CONSUMO_PRODUCCION."""
        restante = cantidad
        cursor.execute("""
            SELECT pd.id_detalle,
                   (pd.cantidad_obtenida - pd.cantidad_vendida) AS disponible
            FROM PRODUCCION_DETALLE pd
            JOIN PRODUCCION_ORDENES po ON po.id_orden = pd.id_orden
            WHERE pd.id_producto = %s
              AND pd.disponible_venta = TRUE
              AND po.estado = 'finalizada'
              AND (pd.cantidad_obtenida - pd.cantidad_vendida) > 0
            ORDER BY po.fecha_fin ASC, pd.id_detalle ASC
            FOR UPDATE
        """, (id_producto,))
        lotes = cursor.fetchall()

        for lote in lotes:
            if restante <= 0:
                break
            tomar = min(restante, lote['disponible'])
            cursor.execute("""
                UPDATE PRODUCCION_DETALLE
                SET cantidad_vendida = cantidad_vendida + %s
                WHERE id_detalle = %s
            """, (tomar, lote['id_detalle']))
            cursor.execute("""
                INSERT INTO VENTA_CONSUMO_PRODUCCION
                    (id_detalle_venta, id_detalle_produccion, cantidad)
                VALUES (%s,%s,%s)
            """, (id_detalle_venta, lote['id_detalle'], tomar))
            restante -= tomar

        if restante > 0:
            raise ValueError(
                f"Stock insuficiente para el producto {id_producto} "
                f"(faltan {restante} unidades)."
            )

    # ------------------------------------------------------------
    # Estadísticas: ranking de productos
    # ------------------------------------------------------------
    def ranking_productos(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        limite: int = 10,
        orden: str = "DESC",
    ) -> List[Dict]:
        orden_sql = "DESC" if orden.upper() == "DESC" else "ASC"
        filtros = ["v.estado = 'completada'"]
        params: List[Any] = []
        if fecha_inicio:
            filtros.append("v.fecha_venta >= %s")
            params.append(fecha_inicio)
        if fecha_fin:
            filtros.append("v.fecha_venta <= %s")
            params.append(fecha_fin)
        where = " AND ".join(filtros)

        cursor = self._cursor()
        cursor.execute(f"""
            SELECT
                dv.id_producto,
                dv.nombre_producto,
                dv.categoria,
                SUM(dv.cantidad) AS unidades_vendidas,
                SUM(dv.subtotal) AS ingresos,
                COUNT(DISTINCT dv.id_venta) AS numero_ventas
            FROM DETALLE_VENTA dv
            JOIN VENTAS v ON v.id_venta = dv.id_venta
            WHERE {where}
            GROUP BY dv.id_producto, dv.nombre_producto, dv.categoria
            ORDER BY unidades_vendidas {orden_sql}
            LIMIT %s
        """, (*params, limite))
        return cursor.fetchall()

    # ------------------------------------------------------------
    # CRUD estándar (requerido por CRUDRepository)
    # ------------------------------------------------------------
    def crear(self, datos: Dict[str, Any]) -> Any:
        # Prefiere crear_venta_completa(); esto queda para compatibilidad de interfaz.
        return self.crear_venta_completa(
            datos.get('cabecera', {}), datos.get('items', []), datos.get('pagos', [])
        )

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> bool:
        cursor = self._cursor()
        cursor.execute(
            "UPDATE VENTAS SET estado = %s, observaciones = %s WHERE id_venta = %s",
            (datos.get('estado', 'anulada'), datos.get('observaciones'), identificador),
        )
        self._commit()
        return cursor.rowcount > 0

    def eliminar(self, identificador: Any) -> bool:
        # No se eliminan ventas: se anulan (ver actualizar()).
        return self.actualizar(identificador, {'estado': 'anulada'})

    def obtener(self, identificador: Any) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM VENTAS WHERE id_venta = %s", (identificador,))
        venta = cursor.fetchone()
        if not venta:
            return None
        cursor.execute(
            "SELECT * FROM DETALLE_VENTA WHERE id_venta = %s", (identificador,)
        )
        venta['detalle'] = cursor.fetchall()
        cursor.execute(
            "SELECT * FROM VENTA_PAGOS WHERE id_venta = %s", (identificador,)
        )
        venta['pagos'] = cursor.fetchall()
        return venta

    def listar(self) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM VENTAS ORDER BY fecha_venta DESC LIMIT 200"
        )
        return cursor.fetchall()

    def buscar(self, texto: str) -> List[Dict]:
        cursor = self._cursor()
        like = f"%{texto}%"
        cursor.execute("""
            SELECT * FROM VENTAS
            WHERE cliente_nombre LIKE %s OR cliente_cedula LIKE %s
            ORDER BY fecha_venta DESC
        """, (like, like))
        return cursor.fetchall()