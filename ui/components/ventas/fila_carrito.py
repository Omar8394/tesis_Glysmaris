import flet as ft
from ui.components.campo_texto import CampoTexto
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing

# NOTA: la función de "agregados" (velas, toppers, empaques personalizados
# por línea de carrito) se OCULTA temporalmente. El componente
# ui.components.ventas.panel_agregados.PanelAgregados se conserva en el
# proyecto para reactivarla en una versión futura, pero esta fila ya no
# lo instancia ni lo referencia.

class FilaCarrito(ft.Container):
    def __init__(
        self,
        index,
        producto,
        cantidad,
        agregados,
        personalizado,
        on_cantidad_changed,
        on_eliminar,
    ):
        self.index = index
        self.producto = producto
        self.cantidad = cantidad
        self.agregados = agregados
        self.personalizado = personalizado
        self.on_cantidad_changed = on_cantidad_changed
        self.on_eliminar = on_eliminar

        self.campo_cantidad = CampoTexto(
            value=str(self.cantidad),
            width=60,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._cambiar_cantidad,
        )

        self.subtotal = ft.Text(f"${producto['precio_venta'] * cantidad:.2f}", weight="bold")

        super().__init__(padding=AppSpacing.SM, border=ft.border.only(bottom=ft.border.BorderSide(1, "gray")))

        self.content = ft.Column([
            ft.Row([
                ft.Text(producto['nombre'], expand=True, weight="bold", max_lines=1),
                self.campo_cantidad,
                self.subtotal,
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    icon_color="red",
                    tooltip="Eliminar",
                    on_click=lambda e: self.on_eliminar(self.index)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ])

    def _cambiar_cantidad(self, e):
        texto = (self.campo_cantidad.value or "").strip()

        # Mientras el campo está vacío o en 0 (por ejemplo, a mitad de
        # borrar un dígito para escribir uno nuevo) NO se notifica al
        # carrito. Si lo hiciéramos, on_cantidad_changed vería 0 y
        # eliminaría la fila del carrito antes de que el usuario termine
        # de corregir el número. Para eliminar un producto está el botón
        # de la ❌; el campo de cantidad ya no borra por sí solo.
        if texto == "":
            return

        try:
            nueva = int(texto)
        except ValueError:
            return

        if nueva <= 0:
            return

        self.cantidad = nueva
        self.on_cantidad_changed(self.index, nueva)