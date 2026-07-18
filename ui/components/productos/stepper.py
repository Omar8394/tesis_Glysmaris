"""
============================================================
Sistema La Dulce Tía

Archivo:
    stepper.py

Responsabilidad:
    Indicador visual de progreso tipo "Stepper horizontal",
    reutilizable en cualquier asistente (wizard) del sistema.

    No conoce el contenido de los pasos: solo recibe una lista
    de títulos y cuál es el paso activo.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography


class Stepper(ft.Row):
    """
    Stepper horizontal reutilizable.
    """

    def __init__(

        self,

        pasos: list[str],

        paso_actual: int = 0,

    ):

        super().__init__()

        self.tema = ThemeManager.theme

        self.pasos = pasos

        self.paso_actual = paso_actual

        self.alignment = ft.MainAxisAlignment.CENTER

        self.controls = self._crear_controles()

    # --------------------------------------------------

    def _crear_controles(self):

        controles = []

        for indice, titulo in enumerate(self.pasos):

            completado = indice < self.paso_actual

            activo = indice == self.paso_actual

            if completado:

                color_circulo = self.tema.success

                contenido_circulo = ft.Icon(ft.icons.CHECK, color="white", size=16)

            elif activo:

                color_circulo = self.tema.primary

                contenido_circulo = ft.Text(

                    str(indice + 1),

                    color="white",

                    weight=AppTypography.BOLD,

                )

            else:

                color_circulo = self.tema.border

                contenido_circulo = ft.Text(

                    str(indice + 1),

                    color=self.tema.text_secondary,

                )

            circulo = ft.Container(

                width=32,

                height=32,

                border_radius=16,

                bgcolor=color_circulo,

                alignment=ft.alignment.center,

                content=contenido_circulo,

            )

            texto = ft.Text(

                titulo,

                size=AppTypography.SMALL,

                weight=AppTypography.BOLD if activo else AppTypography.NORMAL,

                color=self.tema.primary if activo else self.tema.text_secondary,

            )

            controles.append(

                ft.Column(

                    [circulo, texto],

                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,

                    spacing=4,

                )

            )

            if indice < len(self.pasos) - 1:

                controles.append(

                    ft.Container(

                        width=40,

                        height=2,

                        bgcolor=self.tema.success if completado else self.tema.border,

                        margin=ft.margin.only(top=16),

                    )

                )

        return controles

    # --------------------------------------------------

    def ir_a(self, paso_actual: int):
        """Actualiza el paso activo sin recrear el componente."""

        self.paso_actual = paso_actual

        self.controls = self._crear_controles()

        if self.page:
            self.update()
