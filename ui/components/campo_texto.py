"""
============================================================
Sistema La Dulce Tía

Archivo:
    campo_texto.py

Responsabilidad:
    Campo de texto reutilizable para toda la aplicación.
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.radius import AppRadius
from ui.core.sizes import AppSize
from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography


class CampoTexto(ft.TextField):

    """
    Campo de texto oficial del sistema.
    """

    def __init__(

        self,

        etiqueta="",

        hint="",

        icono=None,

        width=None,

        expand=False,

        password=False,

        multiline=False,

        read_only=False,

        value="",

        on_change=None,

        keyboard_type=None,

        error_text=None,

    ):

        tema = ThemeManager.theme

        super().__init__(

            label=etiqueta,

            hint_text=hint,

            prefix_icon=icono,

            value=value,

            password=password,

            # ✅ Flet ya trae el ícono de "ojo abierto/cerrado" nativo para
            # alternar la visibilidad de la contraseña — no hace falta
            # construirlo a mano con un suffix_icon + on_click propio.
            # Se activa automáticamente cuando el campo es de contraseña.
            can_reveal_password=password,

            multiline=multiline,

            read_only=read_only,

            on_change=on_change,

            keyboard_type=keyboard_type,

            width=width or AppSize.FIELD_MEDIUM,

            height=None,

            expand=expand,

            border_radius=AppRadius.TEXTFIELD,

            text_size=AppTypography.INPUT_SIZE,

            bgcolor=tema.surface,

            color=tema.text,

            border_color=tema.border,

            focused_border_color=tema.primary,

            cursor_color=tema.primary,

            error_text=error_text,

        )

        self.text_style = ft.TextStyle(

            size=AppTypography.INPUT_SIZE,

            font_family=AppTypography.FONT_FAMILY,

            weight=AppTypography.NORMAL,

        )