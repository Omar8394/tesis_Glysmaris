"""
============================================================
Sistema La Dulce Tía

Archivo:
    crud_layout.py

Responsabilidad:
    Layout reutilizable para módulos CRUD.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager

class CRUDLayout(ft.Container):
    """
    Distribución visual estándar para módulos CRUD.
    """
    def __init__(

        self,

        encabezado,

        toolbar,

        historial,

        formulario,

        paginador=None,

    ):

        super().__init__()

        self.expand = True

        self.tema = ThemeManager.theme

        panel_historial = ft.Container(

            width=430,

            padding=AppSpacing.MD,

            content=historial,

        )

        panel_formulario = ft.Container(

            expand=True,

            padding=AppSpacing.LG,

            content=formulario,

        )

        cuerpo = ft.Row(

            [

                panel_historial,

                panel_formulario,

            ],

            expand=True,

            spacing=0,

        )

        controles = [

            encabezado,

            toolbar,

            cuerpo,

        ]

        if paginador:

            controles.append(

                ft.Container(

                    padding=AppSpacing.MD,

                    alignment=ft.alignment.center,

                    content=paginador,

                )

            )

        self.content = ft.Column(

            controles,

            expand=True,

            spacing=AppSpacing.SM,

        )

