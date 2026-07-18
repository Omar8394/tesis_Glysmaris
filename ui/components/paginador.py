"""
============================================================
Sistema La Dulce Tía

Archivo:
    paginador.py

Responsabilidad:
    Control de paginación reutilizable.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import math

import flet as ft

from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography
from ui.core.theme_manager import ThemeManager

class Paginador(ft.Row):

    """
    Componente reutilizable para paginar listas.
    """

    def __init__(

        self,

        on_change,

        elementos_por_pagina=20,

    ):

        super().__init__()

        self.tema = ThemeManager.theme

        self.on_change = on_change

        self.elementos_por_pagina = elementos_por_pagina

        self.total_registros = 0

        self.total_paginas = 1

        self.pagina_actual = 1

        self.btn_primero = ft.IconButton(

            icon=ft.icons.FIRST_PAGE,

            on_click=self._primera,

        )

        self.btn_anterior = ft.IconButton(

            icon=ft.icons.CHEVRON_LEFT,

            on_click=self._anterior,

        )

        self.lbl = ft.Text(

            weight=AppTypography.BOLD,

        )

        self.btn_siguiente = ft.IconButton(

            icon=ft.icons.CHEVRON_RIGHT,

            on_click=self._siguiente,

        )

        self.btn_ultimo = ft.IconButton(

            icon=ft.icons.LAST_PAGE,

            on_click=self._ultima,
        )

        self.spacing = AppSpacing.SM

        self.controls = [

            self.btn_primero,

            self.btn_anterior,

            self.lbl,

            self.btn_siguiente,

            self.btn_ultimo,

        ]

        self._actualizar_label()

    def establecer_total(
        self,
        total: int,
        actualizar: bool = True,
    ):
        self.total_registros = total
        self.total_paginas = max(
            1,
            math.ceil(total / self.elementos_por_pagina)
        )
        # ✅ Antes esto siempre volvía a la página 1 en cada carga, así que
        # avanzar de página nunca "pegaba" (cargar() llamaba a esto de nuevo
        # y te mandaba de vuelta al principio). Ahora solo se ajusta si la
        # página actual quedó fuera de rango (ej. se filtró y hay menos datos).
        if self.pagina_actual > self.total_paginas:
            self.pagina_actual = self.total_paginas
        if self.pagina_actual < 1:
            self.pagina_actual = 1
        self._actualizar_label()
        if actualizar:
            self._actualizar()

    def _actualizar(self):
        self._actualizar_label()
        self.update()  # <--- Solo se llama si actualizar=True
        if self.on_change:
            self.on_change(
                self.pagina_actual,
                self.elementos_por_pagina,
            )

    def _primera(self, e):

        self.pagina_actual = 1

        self._actualizar()


    def _ultima(self, e):

        self.pagina_actual = self.total_paginas

        self._actualizar()


    def _anterior(self, e):

        if self.pagina_actual > 1:

            self.pagina_actual -= 1

            self._actualizar()


    def _siguiente(self, e):

        if self.pagina_actual < self.total_paginas:

            self.pagina_actual += 1

            self._actualizar()

    def _actualizar_label(self):

        self.lbl.value = (

            f"Página "

            f"{self.pagina_actual}"

            f" de "

            f"{self.total_paginas}"

        )

    def obtener_pagina(self):

        return self.pagina_actual


    def reiniciar(self):

        self.pagina_actual = 1

        self._actualizar()

    def resetear_pagina_silencioso(self):
        """✅ Vuelve a la página 1 SIN disparar on_change ni update().
        Pensado para usarse justo antes de un cargar() explícito (ej. al
        buscar o cambiar un filtro), evitando disparar dos cargas de datos
        seguidas — una por este reseteo y otra por el cargar() posterior."""
        self.pagina_actual = 1
        self._actualizar_label()