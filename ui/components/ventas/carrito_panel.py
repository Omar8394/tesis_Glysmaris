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
        on_continuar_cobro,
    ):
        super().__init__(
            expand=True,
            spacing=AppSpacing.CONTROL_SPACING,
            # STRETCH: los hijos ocupan todo el ancho disponible de la
            # Column (eje transversal), sin tocar su alto (eje principal).
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self.on_cambiar_cantidad = on_cambiar_cantidad
        self.on_eliminar = on_eliminar
        self.on_continuar_cobro = on_continuar_cobro
        # La función de "agregados" por línea de carrito está oculta
        # temporalmente (ver fila_carrito.py); se reactivará junto con
        # on_abrir_agregados y activos_disponibles en una versión futura.

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
            height=45,
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
                )
                self.lista.controls.append(fila)

        # Actualizar resumen. Nota: mientras la función de "agregados" esté
        # oculta, este total (precio * cantidad) coincide exactamente con
        # VentasModule._calcular_total(); si se reactivan los agregados,
        # ambos cálculos deben volver a unificarse para no mostrar un total
        # distinto en el carrito y en el panel de pago.
        total = sum(
            float(item['producto'].get('precio_venta', 0) or 0) * item['cantidad']
            for item in carrito
        )
        descuento = 0  # por implementar
        self.resumen.actualizar(total, descuento)

        # Habilitar botón si hay productos
        self.btn_continuar.disabled = len(carrito) == 0
        self.update()

    def _continuar(self, e):
        self.on_continuar_cobro()