"""
============================================================
Sistema La Dulce Tía

Archivo:
    cuenta_cobrar_service.py

Responsabilidad:
    Reglas de negocio de cuentas por cobrar: registrar deudas
    generadas por ventas a crédito y administrar sus abonos.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ui.core.services.base.crud_service import CRUDService
from ui.core.repositories.operaciones.cuenta_cobrar_repository import CuentaPorCobrarRepository


class CuentaPorCobrarService(CRUDService):
    """
    Servicio de cuentas por cobrar (deudas de ventas a crédito).
    """

    def __init__(self, repositorio: CuentaPorCobrarRepository):
        super().__init__()
        self._repositorio = repositorio

    def validar(self, datos: Dict[str, Any]) -> tuple[bool, str]:
        if not datos.get("id_venta"):
            return False, "La cuenta por cobrar debe estar asociada a una venta."

        monto_total = datos.get("monto_total") or 0
        if monto_total <= 0:
            return False, "El monto a crédito debe ser mayor a cero."

        return True, ""

    def crear(self, datos: Dict[str, Any]) -> tuple[bool, str]:
        """
        Se llama desde VentaService, dentro de la misma transacción
        de la venta, cuando en VENTA_PAGOS hay una fila con
        metodo_pago = 'credito'. `datos` espera:
            id_venta, id_cliente (puede ser None), monto_total,
            fecha_venta, fecha_vencimiento (opcional), observaciones
        """
        valido, mensaje = self.validar(datos)
        if not valido:
            return False, mensaje

        id_cuenta = self._repositorio.crear(datos)
        return True, f"Deuda registrada (#{id_cuenta})."

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> tuple[bool, str]:
        actualizado = self._repositorio.actualizar(identificador, datos)
        if not actualizado:
            return False, "No se encontró la cuenta por cobrar."
        return True, "Cuenta por cobrar actualizada."

    def eliminar(self, identificador: Any) -> tuple[bool, str]:
        anulado = self._repositorio.eliminar(identificador)
        if not anulado:
            return False, "No se encontró la cuenta por cobrar."
        return True, "Cuenta por cobrar anulada."

    def obtener(self, identificador: Any) -> Optional[Dict]:
        return self._repositorio.obtener(identificador)

    def listar(self) -> List[Dict]:
        return self._repositorio.listar()

    def buscar(self, texto: str) -> List[Dict]:
        return self._repositorio.buscar(texto)

    def listar_deudas_pendientes(self) -> List[Dict]:
        """
        Lo que se muestra en la pantalla de 'Cuentas por Cobrar':
        todo lo que todavía se debe.
        """
        return self._repositorio.listar_pendientes()

    def listar_por_cliente(self, id_cliente: Any) -> List[Dict]:
        return self._repositorio.listar_por_cliente(id_cliente)

    def total_por_cobrar(self) -> float:
        return self._repositorio.total_por_cobrar()

    def abonar(
        self,
        id_cuenta: Any,
        monto: float,
        metodo_pago: str,
        referencia: str = "",
        observaciones: str = "",
        usuario_registro: str = "",
    ) -> tuple[bool, str]:
        """
        Registra un pago parcial (o total) sobre una deuda existente.
        """
        cuenta = self._repositorio.obtener(id_cuenta)
        if cuenta is None:
            return False, "La cuenta por cobrar no existe."

        if cuenta["estado"] in ("pagada", "anulada"):
            return False, "Esta cuenta ya no tiene saldo pendiente."

        if monto <= 0:
            return False, "El monto del abono debe ser mayor a cero."

        if monto > float(cuenta["monto_pendiente"]):
            return False, (
                f"El abono (${monto:.2f}) supera el saldo pendiente "
                f"(${float(cuenta['monto_pendiente']):.2f})."
            )

        self._repositorio.registrar_abono(
            id_cuenta=id_cuenta,
            monto=monto,
            metodo_pago=metodo_pago,
            referencia=referencia or None,
            observaciones=observaciones or None,
            usuario_registro=usuario_registro or None,
        )
        return True, "Abono registrado."

    def historial_abonos(self, id_cuenta: Any) -> List[Dict]:
        return self._repositorio.listar_abonos(id_cuenta)