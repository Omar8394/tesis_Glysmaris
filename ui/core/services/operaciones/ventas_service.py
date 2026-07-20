# ui/core/services/operaciones/venta_service.py
"""
============================================================
Sistema La Dulce Tía — VentaService
Orquesta la venta: valida carrito, arma el detalle,
delega la persistencia transaccional al repositorio.
============================================================
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from ui.core.services.base.crud_service import CRUDService
from ui.core.services.base.service_result import ServiceResult


class VentaService(CRUDService):

    def __init__(self, repository):
        super().__init__()
        self._repo = repository

    # ------------------------------------------------------------
    def listar_productos_disponibles(self) -> List[Dict]:
        return self._repo.listar_productos_disponibles()

    # ------------------------------------------------------------
    def finalizar_venta(
        self,
        carrito: List[Dict[str, Any]],
        pagos: List[Dict[str, Any]],
        cliente: Optional[Dict[str, Any]] = None,
        usuario: Optional[str] = None,
    ) -> ServiceResult:
        cliente = cliente or {}

        valido, mensaje = self._validar_carrito(carrito)
        if not valido:
            return ServiceResult.error(mensaje)

        items = []
        subtotal_general = 0.0
        for item in carrito:
            producto = item['producto']
            cantidad = item['cantidad']
            precio_unitario = producto.get('precio_venta', 0)
            subtotal_producto = precio_unitario * cantidad

            agregados = []
            for agg in item.get('agregados', []):
                sub_agg = agg.get('costo', 0)
                agregados.append({
                    'id_activo': agg['id_activo'],
                    'nombre_activo': agg['nombre'],
                    'cantidad': agg.get('cantidad', 1),
                    'costo_unitario': sub_agg / agg.get('cantidad', 1) if agg.get('cantidad') else sub_agg,
                    'subtotal': sub_agg,
                })
                subtotal_producto += sub_agg

            items.append({
                'id_producto': producto['id_producto'],
                'nombre_producto': producto['nombre_producto'] if 'nombre_producto' in producto else producto.get('nombre'),
                'categoria': producto.get('categoria'),
                'presentacion': (producto.get('presentacion_seleccionada') or {}).get('nombre'),
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal_producto,
                'agregados': agregados,
            })
            subtotal_general += subtotal_producto

        pagos_validos, mensaje_pago = self._validar_pagos(pagos, subtotal_general)
        if not pagos_validos:
            return ServiceResult.error(mensaje_pago)

        cabecera = {
            'cliente_nombre': cliente.get('nombre'),
            'cliente_cedula': cliente.get('cedula'),
            'cliente_telefono': cliente.get('telefono'),
            'subtotal': subtotal_general,
            'descuento': 0,
            'total': subtotal_general,
            'observaciones': cliente.get('observaciones'),
            'usuario_registro': usuario,
        }

        try:
            id_venta = self._repo.crear_venta_completa(cabecera, items, pagos)
            return ServiceResult.ok("Venta registrada correctamente.", datos={'id_venta': id_venta})
        except ValueError as e:
            # Stock insuficiente, etc.
            return ServiceResult.error(str(e))
        except Exception as e:
            return ServiceResult.error(f"No se pudo registrar la venta: {e}")

    # ------------------------------------------------------------
    def obtener_ranking(
        self, fecha_inicio=None, fecha_fin=None, limite=10, orden="DESC"
    ) -> List[Dict]:
        return self._repo.ranking_productos(fecha_inicio, fecha_fin, limite, orden)

    def obtener_mas_vendidos(self, fecha_inicio=None, fecha_fin=None, limite=10):
        return self.obtener_ranking(fecha_inicio, fecha_fin, limite, orden="DESC")

    def obtener_menos_vendidos(self, fecha_inicio=None, fecha_fin=None, limite=10):
        return self.obtener_ranking(fecha_inicio, fecha_fin, limite, orden="ASC")

    # ------------------------------------------------------------
    def _validar_carrito(self, carrito):
        if not carrito:
            return False, "El carrito está vacío."
        for item in carrito:
            if item.get('cantidad', 0) <= 0:
                return False, "Hay productos con cantidad inválida."
        return True, ""

    def _validar_pagos(self, pagos, total):
        if not pagos:
            return False, "Debes registrar al menos un método de pago."
        suma = sum(p.get('monto', 0) for p in pagos)
        if suma < total - 0.01:
            return False, "El monto pagado no cubre el total de la venta."
        return True, ""

    # ------------------------------------------------------------
    # Contrato CRUDService
    # ------------------------------------------------------------
    def crear(self, datos): return self._repo.crear(datos)
    def actualizar(self, identificador, datos): return self._repo.actualizar(identificador, datos)
    def eliminar(self, identificador): return self._repo.eliminar(identificador)
    def obtener(self, identificador): return self._repo.obtener(identificador)
    def listar(self): return self._repo.listar()
    def buscar(self, texto): return self._repo.buscar(texto)
    def validar(self, datos): return True, ""