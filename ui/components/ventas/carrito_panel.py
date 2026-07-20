import flet as ft
from ui.components.boton import BotonPrimario
from ui.components.ventas.fila_carrito import FilaCarrito
from ui.components.ventas.resume_venta import ResumenVenta
from ui.core.spacing import AppSpacing

class CarritoPanel(ft.Column):
    def __init__(
        self,
        on_cambiar_cantidad,
        on_eliminar,
        on_abrir_agregados,
        on_continuar_cobro,
        activos_disponibles
    ):
        super().__init__(expand=True, spacing=AppSpacing.CONTROL_SPACING)
        self.on_cambiar_cantidad = on_cambiar_cantidad
        self.on_eliminar = on_eliminar
        self.on_abrir_agregados = on_abrir_agregados
        self.on_continuar_cobro = on_continuar_cobro
        self.activos_disponibles = activos_disponibles

        # Lista de filas (scroll)
        self.lista = ft.Column(spacing=AppSpacing.SM, scroll=ft.ScrollMode.AUTO, expand=True)
        self.lista.controls.append(ft.Text("Agrega productos para comenzar", color="gray"))

        # Resumen (fijo abajo)
        self.resumen = ResumenVenta(total=0, descuento=0)

        # Botón continuar
        self.btn_continuar = BotonPrimario(
            texto="Continuar al cobro",
            icono=ft.icons.PAYMENT,
            on_click=self._continuar,
            expand=True,
            width=None,
            disabled=True  # Se habilita cuando hay productos
        )

        self.controls = [
            ft.Text("Carrito", weight="bold", size=20),
            self.lista,
            ft.Divider(),
            self.resumen,
            self.btn_continuar,
        ]

    def actualizar_carrito(self, carrito):
        """Recibe la lista de ítems del módulo y refresca la vista."""
        self.lista.controls.clear()
        if not carrito:
            self.lista.controls.append(ft.Text("Agrega productos para comenzar", color="gray"))
        else:
            for idx, item in enumerate(carrito):
                fila = FilaCarrito(
                    index=idx,
                    producto=item['producto'],
                    cantidad=item['cantidad'],
                    agregados=item.get('agregados', []),
                    personalizado=item.get('personalizado', False),
                    on_cantidad_changed=self.on_cambiar_cantidad,
                    on_eliminar=self.on_eliminar,
                    on_abrir_agregados=self.on_abrir_agregados,
                    activos_disponibles=self.activos_disponibles
                )
                self.lista.controls.append(fila)

        # Actualizar resumen
        total = sum(item['producto']['precio_venta'] * item['cantidad'] for item in carrito)
        descuento = 0  # por implementar
        self.resumen.actualizar(total, descuento)

        # Habilitar botón si hay productos
        self.btn_continuar.disabled = len(carrito) == 0
        self.update()

    def _continuar(self, e):
        self.on_continuar_cobro()