import flet as ft
from ui.components.boton import BotonPrimario
from ui.components.selector import Selector
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing

class CardProductoVenta(ft.Card):
    def __init__(self, producto, on_agregar):
        self.producto = producto
        self.on_agregar = on_agregar
        super().__init__(elevation=2, margin=5)

        # Presentación seleccionable (si tiene varias)
        presentaciones = producto.get('presentaciones', [])
        if presentaciones:
            self.selector_presentacion = Selector(
                opciones=[p['nombre'] for p in presentaciones],
                valor=presentaciones[0]['nombre'] if presentaciones else None,
                width=100,
                dense=True
            )
        else:
            self.selector_presentacion = ft.Text("Sin presentaciones", size=AppTypography.SMALL)

        self.btn_agregar = BotonPrimario(
            texto="Agregar",
            icono=ft.icons.ADD,
            on_click=self._agregar,
            width=80,
            height=32
        )

        contenido = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(producto.get('icono', ft.icons.INVENTORY_2_OUTLINED), size=32),
                        ft.Text(producto['nombre'], weight="bold", max_lines=1),
                    ],
                    spacing=4
                ),
                ft.Row([self.selector_presentacion], spacing=4),
                ft.Row(
                    [
                        ft.Text(f"Stock: {producto.get('stock_actual', 0)}", size=AppTypography.SMALL),
                        ft.Text(f"${producto.get('precio_venta', 0):.2f}", weight="bold"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row([self.btn_agregar], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=AppSpacing.SM,
            tight=True,
        )

        self.content = ft.Container(content=contenido, padding=AppSpacing.MD)

    def _agregar(self, e):
        # Obtener la presentación seleccionada
        if self.selector_presentacion.value:
            presentacion = next(
                (p for p in self.producto.get('presentaciones', []) if p['nombre'] == self.selector_presentacion.value),
                None
            )
        else:
            presentacion = None
        # Llamar al callback con el producto y la presentación
        self.on_agregar({
            **self.producto,
            'presentacion_seleccionada': presentacion
        })
        # Feedback visual rápido (cambiar texto del botón)
        self.btn_agregar.text = "✓ Agregado"
        self.btn_agregar.update()
        # Restaurar después de 500ms
        import asyncio
        async def restaurar():
            await asyncio.sleep(0.5)
            self.btn_agregar.text = "Agregar"
            self.btn_agregar.update()
        asyncio.create_task(restaurar())