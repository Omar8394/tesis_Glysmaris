"""
============================================================
Sistema La Dulce Tía

Archivo:
    toolbar.py

Responsabilidad:
    Barra superior reutilizable para módulos CRUD.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from ui.core.spacing import AppSpacing

@dataclass
class ToolbarItem:

    control: ft.Control

    expand: bool = False

class ToolbarGrupo(ft.Row):

    def __init__(

        self,

        *controles,

    ):

        super().__init__()

        self.spacing = AppSpacing.SM

        self.controls = list(controles)

class Toolbar(ft.Container):

    """
    Barra superior reutilizable.
    """
    def __init__(

        self,

        izquierda=None,

        centro=None,

        derecha=None,

    ):

        super().__init__()

        izquierda = izquierda or []

        centro = centro or []

        derecha = derecha or []


        self.content = ft.Row(

            [

                ft.Row(

                    izquierda,

                    spacing=AppSpacing.SM,

                    expand=True,

                ),

                ft.Row(

                    centro,

                    spacing=AppSpacing.SM,

                ),

                ft.Row(

                    derecha,

                    spacing=AppSpacing.SM,

                    alignment=ft.MainAxisAlignment.END,

                ),

            ],

            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,

        )

