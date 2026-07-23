"""
============================================================
Sistema La Dulce Tía

Archivo:
    cliente_service.py

Responsabilidad:
    Reglas de negocio para la gestión de clientes.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ui.core.services.base.crud_service import CRUDService
from ui.core.repositories.cliente_repository import ClienteRepository


class ClienteService(CRUDService):
    """
    Servicio de clientes.
    """

    def __init__(self, repositorio: ClienteRepository):
        super().__init__()
        self._repositorio = repositorio

    def validar(self, datos: Dict[str, Any]) -> tuple[bool, str]:
        nombre = (datos.get("nombre") or "").strip()
        if not nombre:
            return False, "El nombre del cliente es obligatorio."

        cedula = (datos.get("cedula") or "").strip()
        if cedula:
            existente = self._repositorio.obtener_por_cedula(cedula)
            if existente and existente["id_cliente"] != datos.get("id_cliente"):
                return False, "Ya existe un cliente registrado con esa cédula."

        return True, ""

    def crear(self, datos: Dict[str, Any]) -> tuple[bool, str]:
        valido, mensaje = self.validar(datos)
        if not valido:
            return False, mensaje

        id_cliente = self._repositorio.crear(datos)
        return True, f"Cliente registrado (#{id_cliente})."

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> tuple[bool, str]:
        datos_validacion = {**datos, "id_cliente": identificador}
        valido, mensaje = self.validar(datos_validacion)
        if not valido:
            return False, mensaje

        actualizado = self._repositorio.actualizar(identificador, datos)
        if not actualizado:
            return False, "No se encontró el cliente a actualizar."
        return True, "Cliente actualizado."

    def eliminar(self, identificador: Any) -> tuple[bool, str]:
        eliminado = self._repositorio.eliminar(identificador)
        if not eliminado:
            return False, "No se encontró el cliente a eliminar."
        return True, "Cliente desactivado."

    def obtener(self, identificador: Any) -> Optional[Dict]:
        return self._repositorio.obtener(identificador)

    def listar(self) -> List[Dict]:
        return self._repositorio.listar()

    def buscar(self, texto: str) -> List[Dict]:
        return self._repositorio.buscar(texto)

    def obtener_o_crear_por_cedula(
        self,
        cedula: str,
        nombre: str,
        telefono: str = "",
    ) -> Dict:
        """
        Punto de integración con el módulo de Ventas: si al registrar
        una venta a crédito el cliente ya existe por cédula, lo
        reutiliza; si no, lo crea al vuelo con los datos capturados
        en la venta.
        """
        cedula = (cedula or "").strip()
        if cedula:
            existente = self._repositorio.obtener_por_cedula(cedula)
            if existente:
                return existente

        id_cliente = self._repositorio.crear(
            {
                "nombre": nombre,
                "cedula": cedula or None,
                "telefono": telefono,
                "direccion": None,
                "observaciones": None,
            }
        )
        return self._repositorio.obtener(id_cliente)
