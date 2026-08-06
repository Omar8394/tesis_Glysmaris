# ui/modules/operaciones/ventas/ventas_module.py

from __future__ import annotations

import flet as ft

from ui.modules.base.module import Module
from ui.modules.operaciones.ventas.ventas import VentasView
from ui.core.services.factory import ServiceFactory
from ui.components.mensajes import MensajeSistema

# Traduce el texto que muestra PanelPago al valor exacto que espera el
# ENUM de VENTA_PAGOS.metodo_pago en la base de datos. Sin esto, la
# detección de pagos a crédito en VentaService/VentaRepository nunca
# coincide (compara contra 'credito' en minúsculas) y la venta falla
# o, peor, se guarda sin generar la cuenta por cobrar.
MAPA_METODOS_PAGO = {
    "Efectivo": "efectivo",
    "Débito": "debito",
    "Crédito": "credito",
    "Transferencia": "transferencia",
    "Pago móvil": "pago_movil",
}


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
        self.cliente_service = ServiceFactory.get_cliente_service()

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
            productos = self.venta_service.listar_productos_disponibles()
            # Depuración: imprimir los primeros productos con sus precios
            print(f"Productos obtenidos: {len(productos)}")
            for p in productos[:5]:
                print(f"ID: {p.get('id_producto')}, Nombre: {p.get('nombre')}, Precio: {p.get('precio_venta')} (tipo: {type(p.get('precio_venta'))})")
            return productos
        except Exception as e:
            print(f"Error al cargar productos: {e}")
            import traceback
            traceback.print_exc()
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
        """Agrega un producto al carrito (o incrementa cantidad si ya existe).

        Valida contra el stock disponible para no dejar que la falta de
        stock se descubra recién al finalizar la venta (donde de todos
        modos VentaRepository._consumir_stock_producto la vuelve a
        validar como última línea de defensa).
        """
        stock = producto.get('stock_actual', 0) or 0
        for item in self.carrito:
            if item['producto']['id_producto'] == producto['id_producto']:
                if item['cantidad'] + 1 > stock:
                    MensajeSistema.error(self.page, f"Solo hay {stock} unidades disponibles de {producto.get('nombre', 'este producto')}.")
                    return
                item['cantidad'] += 1
                self.view.actualizar_carrito(self.carrito)
                return
        if stock <= 0:
            MensajeSistema.error(self.page, f"{producto.get('nombre', 'Este producto')} no tiene stock disponible.")
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
            stock = self.carrito[index]['producto'].get('stock_actual', 0) or 0
            if nueva > stock:
                MensajeSistema.error(self.page, f"Solo hay {stock} unidades disponibles.")
                self.view.actualizar_carrito(self.carrito)
                return
            self.carrito[index]['cantidad'] = nueva
        self.view.actualizar_carrito(self.carrito)

    def eliminar_producto(self, index: int):
        """Elimina un producto del carrito."""
        del self.carrito[index]
        self.view.actualizar_carrito(self.carrito)

    # La función de "agregados" por producto (velas, toppers, empaques
    # personalizados) queda oculta temporalmente; se reactivará en una
    # versión futura junto con abrir_agregados() y el wiring en VentasView.

    def continuar_cobro(self):
        """Cambia al panel de pago con el total calculado."""
        total = self._calcular_total()
        self.view.mostrar_panel_pago(total)

    def finalizar_venta(self, datos: dict):
        """
        Finaliza la venta: persiste en base de datos vía VentaService
        (que valida el carrito, arma el detalle, descuenta stock FIFO,
        resuelve/crea el cliente y, si hay pago a crédito, genera la
        cuenta por cobrar correspondiente), y limpia el carrito si todo
        sale bien.

        `datos` llega desde PanelPago con la forma:
            {"pagos": {"Efectivo": 10.0, "Crédito": 5.0},
             "cliente": {"nombre": ..., "cedula": ..., "telefono": ...} | None,
             "fecha_vencimiento": "YYYY-MM-DD" | None}
        """
        datos_pago = datos.get("pagos", {})
        cliente = datos.get("cliente")
        fecha_vencimiento = datos.get("fecha_vencimiento")

        pagos = [
            {'metodo_pago': MAPA_METODOS_PAGO.get(metodo, metodo), 'monto': monto}
            for metodo, monto in datos_pago.items()
        ]

        resultado = self.venta_service.finalizar_venta(
            carrito=self.carrito,
            pagos=pagos,
            cliente=cliente,
            usuario=self.usuario,
            fecha_vencimiento=fecha_vencimiento,
        )

        if resultado.exito:
            MensajeSistema.exito(self.page, resultado.mensaje)
            self.carrito.clear()
            self.view.mostrar_carrito()
            self.view.actualizar_carrito(self.carrito)
            # El stock ya se descontó en la base de datos (FIFO, dentro de
            # la misma transacción de la venta); sin esto, las tarjetas
            # del catálogo se quedan mostrando el stock viejo hasta que
            # se recargue el módulo desde cero.
            self.productos_disponibles = self._cargar_productos()
            self.view.actualizar_catalogo(self.productos_disponibles)
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _calcular_total(self) -> float:
        """Calcula el total del carrito.

        precio_venta suele venir de la base de datos como decimal.Decimal
        (columna NUMERIC/DECIMAL). Python no permite mezclar float y
        Decimal en una misma operación aritmética, así que convertimos
        explícitamente a float antes de sumar.

        NOTA: la función de "agregados" (velas, toppers, empaques por
        línea de carrito) está oculta temporalmente; por eso este total
        no los suma. Debe volver a incluirlos aquí cuando se reactive esa
        función, y ese mismo cambio debe reflejarse en
        CarritoPanel.actualizar_carrito para que el total del carrito y
        el del panel de pago sigan coincidiendo.
        """
        total = 0.0
        for item in self.carrito:
            precio = float(item['producto'].get('precio_venta', 0) or 0)
            total += precio * item['cantidad']
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
            on_continuar_cobro=self.continuar_cobro,
            on_finalizar_venta=self.finalizar_venta,
            productos_disponibles=self.productos_disponibles,
            activos_disponibles=self.activos_disponibles,
            buscar_clientes=self.cliente_service.buscar,
        )
        return self.view