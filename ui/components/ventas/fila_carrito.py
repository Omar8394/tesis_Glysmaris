import flet as ft
from ui.components.campo_texto import CampoTexto
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing
from ui.components.ventas.panel_agregados import PanelAgregados

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
        on_abrir_agregados,
        activos_disponibles
    ):
        self.index = index
        self.producto = producto
        self.cantidad = cantidad
        self.agregados = agregados
        self.personalizado = personalizado
        self.on_cantidad_changed = on_cantidad_changed
        self.on_eliminar = on_eliminar
        self.on_abrir_agregados = on_abrir_agregados
        self.activos_disponibles = activos_disponibles

        self.campo_cantidad = CampoTexto(
            value=str(self.cantidad),
            width=60,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._cambiar_cantidad
        )

        self.subtotal = ft.Text(f"${producto['precio_venta'] * cantidad:.2f}", weight="bold")

        self.btn_agregados = ft.TextButton(
            text="⚙ Agregados",
            on_click=self._toggle_agregados,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=AppTypography.SMALL))
        )
        if self.agregados:
            self.btn_agregados.text = f"⚙ Agregados ({len(self.agregados)})"

        # Contenedor de agregados (expandible)
        self.panel_agregados = PanelAgregados(
            index=self.index,
            agregados=self.agregados,
            activos_disponibles=self.activos_disponibles,
            on_agregar_agregado=self._agregar_agregado,
            on_quitar_agregado=self._quitar_agregado,
        )
        self.panel_agregados.visible = False

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
            ft.Row([self.btn_agregados], alignment=ft.MainAxisAlignment.END),
            self.panel_agregados,
        ])

    def _cambiar_cantidad(self, e):
        try:
            nueva = int(self.campo_cantidad.value or 0)
        except ValueError:
            nueva = 0
        self.on_cantidad_changed(self.index, nueva)

    def _toggle_agregados(self, e):
        self.panel_agregados.visible = not self.panel_agregados.visible
        self.update()

    def _agregar_agregado(self, agregado):
        # Agregar a la lista de agregados y notificar al módulo
        self.agregados.append(agregado)
        self.on_abrir_agregados(self.index)  # o un callback específico para actualizar
        # Actualizar el texto del botón
        self.btn_agregados.text = f"⚙ Agregados ({len(self.agregados)})"
        self.update()

    def _quitar_agregado(self, idx):
        del self.agregados[idx]
        self.on_abrir_agregados(self.index)
        self.btn_agregados.text = f"⚙ Agregados ({len(self.agregados)})" if self.agregados else "⚙ Agregados"
        self.update()