# ui/layouts/dashboard_layout.py

from __future__ import annotations
import flet as ft
from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager


class DashboardLayout(ft.Container):
    """
    Layout principal del sistema con sidebar y área de contenido.
    """

    def __init__(
        self,
        sidebar: ft.Control,
        contenido: ft.Control,
        topbar: ft.Control | None = None,
        footer: ft.Control | None = None,
    ):
        super().__init__()
        self.expand = True
        self.tema = ThemeManager.theme

        controles = []

        if topbar:
            controles.append(topbar)

        # Row principal: sidebar + contenido
        row = ft.Row(
            [
                sidebar,
                ft.Container(
                    expand=True,
                    padding=AppSpacing.MD,
                    content=contenido,
                ),
            ],
            expand=True,
            spacing=0,
        )
        controles.append(row)

        if footer:
            controles.append(footer)

        self.content = ft.Column(
            controls=controles,
            expand=True,
            spacing=0,
        )