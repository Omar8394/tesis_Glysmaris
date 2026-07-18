"""
============================================================
Sistema La Dulce Tía

Archivo:
    login_layout.py

Responsabilidad:
    Layout reutilizable para la pantalla de inicio de sesión.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager

class LoginLayout(ft.Container):
    """
    Layout base para la pantalla de inicio de sesión.
    """

    def __init__(

        self,

        formulario,

        footer=None,

    ):

        super().__init__()

        self.expand = True

        tema = ThemeManager.theme

        contenido = ft.Container(

            expand=True,

            alignment=ft.alignment.center,

            content=formulario,

        )

        controles = [

            contenido,

        ]

        if footer:

            controles.append(

                ft.Container(

                    padding=AppSpacing.MD,

                    alignment=ft.alignment.center,

                    content=footer,

                )

            )

        self.content = ft.Column(

            controls=controles,

            expand=True,

            spacing=0,
        )

