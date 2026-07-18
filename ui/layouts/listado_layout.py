# ui/layouts/listado_layout.py

from __future__ import annotations
import flet as ft
from ui.core.spacing import AppSpacing


class ListadoLayout(ft.Container):
    """
    Layout para módulos que solo muestran una lista/tabla,
    sin panel de formulario fijo. El formulario se muestra
    reemplazando todo el contenido.
    """

    def __init__(
        self,
        toolbar: ft.Control,
        tabla: ft.Control,
        paginador: ft.Control | None = None,
        expand: bool = True,
    ):
        super().__init__()
        self.expand = expand
        self.padding = AppSpacing.MD

        controles = [toolbar, tabla]
        if paginador:
            controles.append(paginador)

        self.content = ft.Column(
            controls=controles,
            spacing=AppSpacing.SECTION_SPACING,
            expand=True,
        )