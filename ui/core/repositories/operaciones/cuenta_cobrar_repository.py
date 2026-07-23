"""
============================================================
Sistema La Dulce Tía

Archivo:
    cuenta_cobrar_repository.py

Responsabilidad:
    Acceso a datos de deudas por cobrar (ventas a crédito) y
    sus abonos. Solo persistencia, sin reglas de negocio.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ui.core.repositories.base.crud_repository import CRUDRepository


class CuentaPorCobrarRepository(CRUDRepository):
    """
    Repositorio de cuentas por cobrar.
    """

    def crear(self, datos: Dict[str, Any]) -> Any:
        cursor = self._cursor()
        cursor.execute(
            """
            INSERT INTO CUENTAS_POR_COBRAR
                (id_venta, id_cliente, monto_total, monto_abonado,
                 monto_pendiente, estado, fecha_venta,
                 fecha_vencimiento, observaciones)
            VALUES
                (%(id_venta)s, %(id_cliente)s, %(monto_total)s, 0,
                 %(monto_total)s, 'pendiente', %(fecha_venta)s,
                 %(fecha_vencimiento)s, %(observaciones)s)
            """,
            {
                "id_venta": datos["id_venta"],
                "id_cliente": datos.get("id_cliente"),
                "monto_total": datos["monto_total"],
                "fecha_venta": datos["fecha_venta"],
                "fecha_vencimiento": datos.get("fecha_vencimiento"),
                "observaciones": datos.get("observaciones"),
            },
        )
        self._commit()
        return cursor.lastrowid

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> bool:
        # El monto solo se mueve a través de registrar_abono(); acá
        # solo se ajustan datos administrativos de la cuenta.
        cursor = self._cursor()
        cursor.execute(
            """
            UPDATE CUENTAS_POR_COBRAR
            SET fecha_vencimiento = %(fecha_vencimiento)s,
                observaciones = %(observaciones)s
            WHERE id_cuenta = %(id_cuenta)s
            """,
            {
                "id_cuenta": identificador,
                "fecha_vencimiento": datos.get("fecha_vencimiento"),
                "observaciones": datos.get("observaciones"),
            },
        )
        self._commit()
        return cursor.rowcount > 0

    def eliminar(self, identificador: Any) -> bool:
        # No se borra: se anula (ej. si se anula la venta original).
        # Conserva el historial de abonos ya hechos.
        cursor = self._cursor()
        cursor.execute(
            "UPDATE CUENTAS_POR_COBRAR SET estado = 'anulada' WHERE id_cuenta = %s",
            (identificador,),
        )
        self._commit()
        return cursor.rowcount > 0

    def obtener(self, identificador: Any) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM CUENTAS_POR_COBRAR WHERE id_cuenta = %s",
            (identificador,),
        )
        return cursor.fetchone()

    def listar(self) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM CUENTAS_POR_COBRAR ORDER BY fecha_venta DESC"
        )
        return cursor.fetchall()

    def buscar(self, texto: str) -> List[Dict]:
        cursor = self._cursor()
        patron = f"%{texto}%"
        cursor.execute(
            """
            SELECT cc.*
            FROM CUENTAS_POR_COBRAR cc
            LEFT JOIN CLIENTES cl ON cl.id_cliente = cc.id_cliente
            WHERE cl.nombre LIKE %s OR cl.cedula LIKE %s
            ORDER BY cc.fecha_venta DESC
            """,
            (patron, patron),
        )
        return cursor.fetchall()

    def listar_pendientes(self) -> List[Dict]:
        """
        Deudas activas (pendiente o parcial): lo que realmente
        queda por cobrar. Es la consulta para la pantalla principal
        del módulo.
        """
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT cc.*, cl.nombre AS cliente_nombre, cl.telefono AS cliente_telefono
            FROM CUENTAS_POR_COBRAR cc
            LEFT JOIN CLIENTES cl ON cl.id_cliente = cc.id_cliente
            WHERE cc.estado IN ('pendiente', 'parcial')
            ORDER BY cc.fecha_venta ASC
            """
        )
        return cursor.fetchall()

    def listar_por_cliente(self, id_cliente: Any) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT * FROM CUENTAS_POR_COBRAR
            WHERE id_cliente = %s
            ORDER BY fecha_venta DESC
            """,
            (id_cliente,),
        )
        return cursor.fetchall()

    def registrar_abono(
        self,
        id_cuenta: Any,
        monto: float,
        metodo_pago: str,
        referencia: Optional[str] = None,
        observaciones: Optional[str] = None,
        usuario_registro: Optional[str] = None,
    ) -> Dict:
        """
        Inserta el abono y actualiza monto_abonado / monto_pendiente /
        estado de la cuenta en una sola transacción.
        """
        cursor = self._cursor()
        try:
            cursor.execute(
                """
                INSERT INTO ABONOS_CUENTA
                    (id_cuenta, monto, metodo_pago, referencia,
                     observaciones, usuario_registro)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (id_cuenta, monto, metodo_pago, referencia,
                 observaciones, usuario_registro),
            )

            cursor.execute(
                """
                UPDATE CUENTAS_POR_COBRAR
                SET monto_abonado = monto_abonado + %s,
                    monto_pendiente = monto_pendiente - %s,
                    estado = CASE
                        WHEN monto_pendiente - %s <= 0 THEN 'pagada'
                        ELSE 'parcial'
                    END
                WHERE id_cuenta = %s
                """,
                (monto, monto, monto, id_cuenta),
            )

            self._commit()
        except Exception:
            self._rollback()
            raise

        return self.obtener(id_cuenta)

    def listar_abonos(self, id_cuenta: Any) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM ABONOS_CUENTA WHERE id_cuenta = %s ORDER BY fecha_abono",
            (id_cuenta,),
        )
        return cursor.fetchall()

    def total_por_cobrar(self) -> float:
        """
        Suma de todo lo pendiente en el negocio, para un dashboard
        o resumen del módulo de Mi Negocio.
        """
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(monto_pendiente), 0) AS total
            FROM CUENTAS_POR_COBRAR
            WHERE estado IN ('pendiente', 'parcial')
            """
        )
        fila = cursor.fetchone()
        return float(fila["total"]) if fila else 0.0
