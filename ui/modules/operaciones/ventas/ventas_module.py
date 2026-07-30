# ui/modules/operaciones/ventas/ventas_module.py

from __future__ import annotations

import flet as ft

from ui.modules.base.module import Module
from ui.modules.operaciones.ventas.ventas import VentasView
from ui.core.services.factory import ServiceFactory
from ui.components.mensajes import MensajeSistema


class VentasModule(Module):
    """
    Módulo de Ventas.
    Contiene toda la lógica del carrito, agregados, cobro y finalización.
    """

    def __init__(self, page: ft.Page, content_area: ft.Container):
        # Llamamos al constructor base con page y usuario (sin usuario)
        super().__init__(page, usuario=None)
        self.content_area = content_area
        self.venta_service = ServiceFactory.get_venta_service()
        self.activo_service = ServiceFactory.get_activo_service()
        # Si tienes cliente_service, descomenta la siguiente línea
        # self.cliente_service = ServiceFactory.get_cliente_service()

        # Estado del carrito
        self.carrito = []  # cada item: {producto, cantidad, agregados, personalizado}

        # La vista se construirá en construir()
        self.view = None

        # Datos iniciales (se cargan al construir)
        self.productos_disponibles = []
        self.activos_disponibles = []

    # ------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------
    def cargar(self):
        """Recarga los datos (se llama desde el dashboard al cambiar de módulo)."""
        self.productos_disponibles = self._cargar_productos()
        self.activos_disponibles = self._cargar_activos()
        # Si la vista ya existe, actualizamos el catálogo y el carrito
        if self.view:
            self.view.actualizar_catalogo(self.productos_disponibles)
            self.view.actualizar_carrito(self.carrito)

    def _cargar_productos(self) -> list:
        """Obtiene productos ya finalizados en producción y con stock vendible."""
        try:
            return self.venta_service.listar_productos_disponibles()
        except Exception:
            return []

    def _cargar_activos(self) -> list:
        """Obtiene activos que pueden usarse como agregados (ej: velas, toppers, empaques)."""
        try:
            # Asumimos que existe un método en activo_service para listar agregados
            resultado = self.activo_service.listar_agregados()
            return resultado.datos if resultado.exito else []
        except Exception:
            return []

    # ------------------------------------------------------------
    # Callbacks para la vista
    # ------------------------------------------------------------
    def agregar_producto(self, producto: dict):
        """Agrega un producto al carrito (o incrementa cantidad si ya existe)."""
        for item in self.carrito:
            if item['producto']['id_producto'] == producto['id_producto']:
                item['cantidad'] += 1
                self.view.actualizar_carrito(self.carrito)
                return
        self.carrito.append({
            'producto': producto,
            'cantidad': 1,
            'agregados': [],
            'personalizado': False,
        })
        self.view.actualizar_carrito(self.carrito)

    def cambiar_cantidad(self, index: int, nueva: int):
        """Cambia la cantidad de un producto en el carrito. Si es 0, lo elimina."""
        if nueva <= 0:
            del self.carrito[index]
        else:
            self.carrito[index]['cantidad'] = nueva
        self.view.actualizar_carrito(self.carrito)

    def eliminar_producto(self, index: int):
        """Elimina un producto del carrito."""
        del self.carrito[index]
        self.view.actualizar_carrito(self.carrito)

    def abrir_agregados(self, index: int):
        """Muestra el panel de agregados para el producto en el índice dado."""
        # Delegamos a la vista para que expanda la fila correspondiente
        self.view.mostrar_panel_agregados(index)

    def continuar_cobro(self):
        """Cambia al panel de pago con el total calculado."""
        total = self._calcular_total()
        self.view.mostrar_panel_pago(total)

    def finalizar_venta(self, datos_pago: dict):
        """
        Finaliza la venta: persiste en base de datos vía VentaService
        (que valida el carrito, arma el detalle y descuenta stock FIFO),
        y limpia el carrito si todo sale bien.
        """
        pagos = [
            {'metodo_pago': metodo, 'monto': monto}
            for metodo, monto in datos_pago.items()
        ]

        resultado = self.venta_service.finalizar_venta(
            carrito=self.carrito,
            pagos=pagos,
            cliente=None,
            usuario=self.usuario,
        )

        if resultado.exito:
            MensajeSistema.exito(self.page, resultado.mensaje)
            self.carrito.clear()
            self.view.mostrar_carrito()
            self.view.actualizar_carrito(self.carrito)
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _calcular_total(self) -> float:
        """Calcula el total del carrito (productos + agregados).

        precio_venta / costo suelen venir de la base de datos como
        decimal.Decimal (columnas NUMERIC/DECIMAL). Python no permite
        mezclar float y Decimal en una misma operación aritmética, así
        que convertimos explícitamente a float antes de sumar.
        """
        total = 0.0
        for item in self.carrito:
            precio = float(item['producto'].get('precio_venta', 0) or 0)
            total += precio * item['cantidad']
            for agg in item.get('agregados', []):
                # agg['costo'] ya es el costo total de esa línea (costo_unitario * cantidad),
                # calculado en PanelAgregados._agregar — no volver a multiplicar por cantidad aquí.
                costo = float(agg.get('costo', 0) or 0)
                total += costo
        return total

    # ------------------------------------------------------------
    # Construcción de la vista (obligatorio para Module)
    # ------------------------------------------------------------
    def construir(self) -> ft.Control:
        # Cargar datos antes de construir
        self.productos_disponibles = self._cargar_productos()
        self.activos_disponibles = self._cargar_activos()

        self.view = VentasView(
            on_agregar_producto=self.agregar_producto,
            on_cambiar_cantidad=self.cambiar_cantidad,
            on_eliminar_producto=self.eliminar_producto,
            on_abrir_agregados=self.abrir_agregados,
            on_continuar_cobro=self.continuar_cobro,
            on_finalizar_venta=self.finalizar_venta,
            productos_disponibles=self.productos_disponibles,
            activos_disponibles=self.activos_disponibles,
        )
        return self.view