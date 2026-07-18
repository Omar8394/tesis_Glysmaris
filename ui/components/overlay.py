# ui/components/overlay.py

from __future__ import annotations
import flet as ft
from ui.core.radius import AppRadius
from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager


class Overlay(ft.Container):
    """
    Superposición modal que se coloca encima del contenido.
    Útil para mostrar formularios sin ocultar la vista principal.
    """

    def __init__(self, contenido: ft.Control = None, visible: bool = False):
        tema = ThemeManager.theme
        super().__init__(
            content=ft.Stack(
                [
                    ft.Container(
                        expand=True,
                        bgcolor="black54",  # Fondo semitransparente
                        on_click=self._cerrar_click,  # Cierra al hacer clic fuera
                    ),
                    ft.Container(
                        content=contenido,
                        alignment=ft.alignment.center,
                        padding=AppSpacing.MD,
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
            visible=visible,
            animate_opacity=100,
            opacity=0 if not visible else 1,
        )
        self._contenido = contenido

    def _cerrar_click(self, e):
        """Cierra el overlay al hacer clic en el fondo."""
        self.cerrar()

    def abrir(self, contenido: ft.Control = None):
        """Muestra el overlay con el contenido dado."""
        if contenido:
            self._contenido = contenido
            if len(self.content.controls) > 1:
                self.content.controls[1].content = contenido
        self.visible = True
        self.opacity = 1
        if self.page:
            self.update()

    def cerrar(self):
        """Oculta el overlay."""
        self.visible = False
        self.opacity = 0
        if self.page:
            self.update()