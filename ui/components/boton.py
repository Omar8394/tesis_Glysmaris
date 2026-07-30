from __future__ import annotations

import flet as ft

from ui.core.theme_manager import ThemeManager
from ui.core.radius import AppRadius
from ui.core.sizes import AppSize
from ui.core.typography import AppTypography


class BotonPrimario(ft.ElevatedButton):
    """
    Botón principal del sistema.
    """

    def __init__(
        self,
        texto: str,
        icono=None,
        on_click=None,
        expand: bool = False,
        width=None,
        disabled=False,
        height=AppSize.BUTTON_HEIGHT,
    ):
        tema = ThemeManager.theme

        # Construir contenido con texto e icono
        self._texto_control = ft.Text(
            texto,
            size=AppTypography.BUTTON_SIZE,
            weight=AppTypography.SEMIBOLD,
            font_family=AppTypography.FONT_FAMILY,
            color=tema.button_text,
        )
        contenido = ft.Row(
            [
                ft.Icon(icono, color=tema.button_text) if icono else ft.Container(),
                self._texto_control,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )

        super().__init__(
            on_click=on_click,
            expand=expand,
            disabled=disabled,
            width=width or AppSize.BUTTON_MEDIUM_WIDTH,
            height=height,
            bgcolor=tema.primary,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=AppRadius.BUTTON),
            ),
            content=contenido,
        )

    @property
    def text(self) -> str:
        """Texto visible del botón (el Text real dentro del content)."""
        return self._texto_control.value

    @text.setter
    def text(self, value: str):
        # ft.ElevatedButton asigna internamente self.text = None durante su
        # propio __init__ (aunque no le pasemos ese parámetro). Como "text"
        # ahora es nuestra propiedad, esa asignación pasaría por aquí y
        # borraría el texto real que ya armamos en self._texto_control.
        # La ignoramos para no pisar el valor construido.
        if value is None:
            return
        self._texto_control.value = value


class BotonSecundario(BotonPrimario):
    """
    Botón secundario.
    """

    def __init__(
        self,
        texto,
        icono=None,
        on_click=None,
        expand=False,
        width=None,
        height=AppSize.BUTTON_HEIGHT,
    ):
        super().__init__(
            texto=texto,
            icono=icono,
            on_click=on_click,
            expand=expand,
            width=width,
            height=height,
        )
        tema = ThemeManager.theme
        self.bgcolor = tema.surface
        # Ajustar el color del texto en el contenido
        if self.content and isinstance(self.content, ft.Row):
            for child in self.content.controls:
                if isinstance(child, ft.Text):
                    child.color = tema.text
                elif isinstance(child, ft.Icon):
                    child.color = tema.text

class BotonPeligro(BotonPrimario):
    """
    Botón utilizado para eliminar.
    """

    def __init__(
        self,
        texto,
        icono=None,
        on_click=None,
        expand=False,
        width=None,
    ):
        super().__init__(
            texto,
            icono,
            on_click,
            expand,
            width,
        )
        self.bgcolor = ThemeManager.theme.error
        # Ajustar color del texto e icono a blanco
        if self.content and isinstance(self.content, ft.Row):
            for child in self.content.controls:
                if isinstance(child, ft.Text):
                    child.color = "white"
                elif isinstance(child, ft.Icon):
                    child.color = "white"


class BotonEnlace(ft.TextButton):
    """
    Botón de texto simple (tipo link), sin fondo sólido. Para acciones
    secundarias/discretas, ej. "¿Olvidaste tu contraseña?".
    """

    def __init__(
        self,
        texto: str,
        on_click=None,
        expand: bool = False,
    ):
        tema = ThemeManager.theme

        super().__init__(
            on_click=on_click,
            expand=expand,
            content=ft.Text(
                texto,
                size=AppTypography.BODY,
                weight=AppTypography.NORMAL,
                font_family=AppTypography.FONT_FAMILY,
                color=tema.primary,
            ),
        )