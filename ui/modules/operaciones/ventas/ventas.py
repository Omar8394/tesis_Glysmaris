import flet as ft
from ui.components.tarjetas import TarjetaFormulario
from ui.core.spacing import AppSpacing
from ui.components.ventas.catalogo_panel import CatalogoPanel
from ui.components.ventas.carrito_panel import CarritoPanel
from ui.components.ventas.panel_pago import PanelPago

class VentasView(ft.Row):
    def __init__(
        self,
        on_agregar_producto,
        on_cambiar_cantidad,
        on_eliminar_producto,
        on_abrir_agregados,
        on_continuar_cobro,
        on_finalizar_venta,
        productos_disponibles,
        activos_disponibles
    ):
        super().__init__(expand=True, spacing=0)
        self.on_agregar_producto = on_agregar_producto
        self.on_cambiar_cantidad = on_cambiar_cantidad
        self.on_eliminar_producto = on_eliminar_producto
        self.on_abrir_agregados = on_abrir_agregados
        self.on_continuar_cobro = on_continuar_cobro
        self.on_finalizar_venta = on_finalizar_venta
        self.productos_disponibles = productos_disponibles
        self.activos_disponibles = activos_disponibles

        # Panel izquierdo (catálogo) – 70%
        self.catalogo = CatalogoPanel(
            productos=self.productos_disponibles,
            on_agregar=self.on_agregar_producto
        )

        # Panel derecho (carrito) – 30%
        self.carrito = CarritoPanel(
            on_cambiar_cantidad=self.on_cambiar_cantidad,
            on_eliminar=self.on_eliminar_producto,
            on_abrir_agregados=self.on_abrir_agregados,
            on_continuar_cobro=self.on_continuar_cobro,
            activos_disponibles=self.activos_disponibles
        )

        # Contenedor izquierdo con borde y padding
        izquierda = ft.Container(
            content=self.catalogo,
            expand=True,
            padding=AppSpacing.MD,
            border=ft.border.only(right=ft.border.BorderSide(1, "gray"))
        )

        # Contenedor derecho
        derecha = ft.Container(
            content=self.carrito,
            expand=False,
            width=400,
            padding=AppSpacing.MD,
        )

        self.controls = [izquierda, derecha]

    def actualizar_carrito(self, carrito):
        """Actualiza el carrito con la nueva lista de ítems."""
        self.carrito.actualizar_carrito(carrito)
        self.update()

    def mostrar_panel_pago(self, total):
        """Reemplaza el contenido del panel derecho por el panel de pago."""
        panel_pago = PanelPago(
            total=total,
            on_finalizar=self.on_finalizar_venta,
            on_volver=lambda: self.mostrar_carrito()
        )
        self.controls[1].content = panel_pago
        self.update()

    def mostrar_carrito(self):
        """Vuelve a mostrar el carrito (al cancelar pago)."""
        self.controls[1].content = self.carrito
        self.update()