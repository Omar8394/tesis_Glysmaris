import flet as ft
from ui.components.boton import BotonPrimario
from ui.components.selector import Selector
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing

class CardProductoVenta(ft.Card):
    def __init__(self, producto, on_agregar):
        self.producto = producto
        self.on_agregar = on_agregar
        super().__init__(elevation=0, margin=0)  # Elevación plana moderna con borde custom

        # Presentación seleccionable
        presentaciones = producto.get('presentaciones', [])
        if presentaciones:
            self.selector_presentacion = Selector(
                opciones=[p['nombre'] for p in presentaciones],
                valor=presentaciones[0]['nombre'] if presentaciones else None,
                width=110,
                dense=True
            )
        else:
            self.selector_presentacion = ft.Text("Presentación única", size=AppTypography.SMALL, color="grey-600")

        self.btn_agregar = BotonPrimario(
            texto="Agregar",
            icono=ft.icons.ADD_ROUNDED,
            on_click=self._agregar,
            width=100,
            height=34
        )

        # Encabezado con Icono con Fondo Suave
        icono_prod = producto.get('icono', ft.icons.INVENTORY_2_OUTLINED)
        
        header = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icono_prod, size=22, color=ft.colors.PRIMARY),
                    bgcolor=ft.colors.PRIMARY_CONTAINER,
                    padding=8,
                    border_radius=8
                ),
                ft.Column(
                    [
                        ft.Text(producto['nombre'], weight="bold", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"Stock: {producto.get('stock_actual', 0)}", size=11, color="grey-700")
                    ],
                    spacing=1,
                    expand=True
                )
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START
        )

        contenido = ft.Column(
            [
                header,
                ft.Divider(height=1, color="grey-200"),
                ft.Row([self.selector_presentacion], alignment=ft.MainAxisAlignment.START),
                ft.Container(expand=True),  # Espaciador flexible
                ft.Row(
                    [
                        ft.Text(f"${producto.get('precio_venta', 0):.2f}", weight="bold", size=16, color=ft.colors.PRIMARY),
                        self.btn_agregar
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    cross_axis_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            spacing=AppSpacing.SM,
        )

        self.content = ft.Container(
            content=contenido,
            padding=AppSpacing.MD,
            border_radius=12,
            border=ft.border.all(1, "grey-300"),
            bgcolor="white",
        )

    def _agregar(self, e):
        if self.selector_presentacion.value:
            presentacion = next(
                (p for p in self.producto.get('presentaciones', []) if p['nombre'] == self.selector_presentacion.value),
                None
            )
        else:
            presentacion = None

        self.on_agregar({
            **self.producto,
            'presentacion_seleccionada': presentacion
        })

        # Animación de confirmación
        self.btn_agregar.text = "✓ Listo"
        self.btn_agregar.bgcolor = ft.colors.GREEN_600
        self.btn_agregar.update()

        import asyncio
        async def restaurar():
            await asyncio.sleep(0.6)
            self.btn_agregar.text = "Agregar"
            self.btn_agregar.bgcolor = None
            self.btn_agregar.update()
        asyncio.create_task(restaurar())