"""
============================================================
Sistema La Dulce Tía

Archivo:
    crud_view.py

Responsabilidad:
    Vista base reutilizable para todos los módulos CRUD.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography

class EncabezadoCRUD(ft.Container):
    """
    Encabezado del módulo.
    """

    def __init__(

        self,

        titulo,

        icono,

    ):

        tema = ThemeManager.theme

        super().__init__()

        self.padding = AppSpacing.MD

        self.content = ft.Row(

            [

                ft.Icon(

                    icono,

                    size=30,

                    color=tema.primary,

                ),

                ft.Text(

                    titulo,

                    size=24,

                    weight=AppTypography.BOLD,

                ),

            ],

            spacing=10,

        )

class PanelFormulario(ft.Container):
    """
    Panel derecho.
    """

    def __init__(

        self,

        contenido,

    ):

        super().__init__()

        self.expand = True

        self.padding = AppSpacing.LG

        self.content = contenido

class PanelHistorial(ft.Container):
    """
    Panel izquierdo.
    """

    def __init__(

        self,

        contenido,

        width=420,

    ):

        super().__init__()

        self.width = width

        self.padding = AppSpacing.LG

        self.content = contenido

class ContenidoCRUD(ft.Row):

    def __init__(

        self,

        historial,

        formulario,

    ):

        super().__init__()

        self.expand = True

        self.spacing = 0

        self.controls = [

            historial,

            formulario,

        ]

class CRUDView(ft.Column):
    """
    Vista base para cualquier módulo CRUD.
    """
    def __init__(

        self,

        titulo,

        icono,

        toolbar,

        historial,

        formulario,

        paginador=None,

    ):

        super().__init__()

        self.expand = True

        self.spacing = 0

        encabezado = EncabezadoCRUD(

            titulo,

            icono,

        )

        cuerpo = ContenidoCRUD(

            PanelHistorial(historial),

            PanelFormulario(formulario),

        )

        self.controls = [

            encabezado,

            toolbar,

            cuerpo,

        ]

        if paginador:

            self.controls.append(

                ft.Container(

                    padding=10,

                    alignment=ft.alignment.center,

                    content=paginador,

                )

            )

