"""
============================================================
Sistema La Dulce Tía

Archivo:
    selector.py

Responsabilidad:
    Dropdown reutilizable para toda la aplicación.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.radius import AppRadius
from ui.core.sizes import AppSize
from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography


class Selector(ft.Dropdown):
    """
    Selector oficial del sistema.

    Todos los Dropdown del sistema deberán utilizar
    este componente.
    """

    def __init__(
        self,
        etiqueta: str = "",
        opciones=None,
        valor=None,
        icono=None,
        hint="Seleccione...",
        width=None,
        expand=False,
        disabled=False,
        on_change=None,
        error_text=None
    ):

        tema = ThemeManager.theme

        opciones = opciones or []

        super().__init__(

            label=etiqueta,

            value=valor,

            hint_text=hint,

            prefix_icon=icono,

            options=[
                ft.dropdown.Option(opcion)
                for opcion in opciones
            ],

            width=width or AppSize.DROPDOWN_MEDIUM,

            height=AppSize.FIELD_HEIGHT,

            expand=expand,

            disabled=disabled,

            on_change=on_change,

            border_radius=AppRadius.DROPDOWN,

            text_size=AppTypography.INPUT_SIZE,

            bgcolor=tema.surface,

            color=tema.text,

            border_color=tema.border,

            focused_border_color=tema.primary,

            content_padding=ft.padding.symmetric(horizontal=12, vertical=4),

            error_text=error_text,
            
        ) 

        self.text_style = ft.TextStyle(

            size=AppTypography.INPUT_SIZE,

            weight=AppTypography.NORMAL,

            font_family=AppTypography.FONT_FAMILY,

            height=1.2,

        )

    # --------------------------------------------------------
    # Métodos auxiliares
    # --------------------------------------------------------

    def establecer_opciones(self, opciones):
        """
        Reemplaza todas las opciones.
        """

        self.options = [
            ft.dropdown.Option(opcion)
            for opcion in opciones
        ]

    def limpiar(self):
        """
        Limpia la selección.
        """

        self.value = None