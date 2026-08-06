"""
============================================================
Sistema La Dulce Tía

Archivo:
    selector_fecha.py

Responsabilidad:
    Selector de fecha reutilizable para todo el sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from datetime import datetime, date

import flet as ft

from ui.components.campo_texto import CampoTexto
from ui.core.icons import AppIcons


def _a_date(valor):
    """Normaliza date/datetime/string ISO a un objeto date, o None."""
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue
    return None


class SelectorFecha(ft.Row):
    """
    Campo de fecha con calendario integrado.

    El usuario no escribe la fecha manualmente.
    """

    def __init__(

        self,

        page: ft.Page,

        etiqueta="Fecha",

        formato="%d/%m/%Y",

        width=220,

        primera_fecha=None,

        ultima_fecha=None,

        on_change=None,

    ):

        super().__init__()

        self.page = page

        self.formato = formato

        self.on_change = on_change

        # ✅ Guardamos el date real por separado del texto mostrado. Antes
        # obtener() devolvía el texto formateado ("10/07/2026"), que al
        # mandarse tal cual a una columna DATE de MySQL no se guarda
        # correctamente (MySQL espera 'YYYY-MM-DD').
        self._valor: date | None = None

        self.campo = CampoTexto(

            etiqueta=etiqueta,

            width=width,

            read_only=True,

            expand=True,

        )

        self.boton = ft.IconButton(

            icon=AppIcons.CALENDAR,

            tooltip="Seleccionar fecha",

            on_click=self._abrir_calendario,

        )

        self.date_picker = ft.DatePicker(

            first_date=primera_fecha,

            last_date=ultima_fecha,

            on_change=self._fecha_seleccionada,

        )

        # ✅ BUG: antes se hacía `page.overlay.append(self.date_picker)`
        # aquí y luego, en _abrir_calendario, `self.date_picker.open = True`
        # + `self.page.update()`. Ese es el patrón de Flet clásico para
        # mostrar diálogos. En versiones recientes de Flet ese patrón fue
        # reemplazado por `Page.show_dialog(control)`, y el viejo ya no
        # muestra nada -- ni error, ni calendario, nada (el botón solo
        # cambia de color al pasar el mouse porque eso es CSS de hover,
        # no efecto del clic). Ahora _abrir_calendario decide en tiempo de
        # ejecución cuál mecanismo usar según lo que soporte la Page.

        self.controls = [

            self.campo,

            self.boton,

        ]
    #================================
    # ABRIR CALENDARIO
    #================================
    
    def _abrir_calendario(self, e):

        if hasattr(self.page, "show_dialog"):
            # Flet reciente: los diálogos (DatePicker incluido) se abren así.
            self.page.show_dialog(self.date_picker)
        else:
            # Flet clásico (aprox. <= 0.21): overlay + open=True.
            if self.date_picker not in self.page.overlay:
                self.page.overlay.append(self.date_picker)
            self.date_picker.open = True
            self.page.update()
    
    #==============================
    # MOMENTO DE SELECCION
    #==============================

    def _fecha_seleccionada(self, e):

        if self.date_picker.value:

            self._valor = _a_date(self.date_picker.value)

            self.campo.value = self._valor.strftime(self.formato) if self._valor else ""
            self.campo.update()
            if self.on_change:

                self.on_change(e)

        self.page.update()

    #====================================
    # METODODS PUBLICOS
    #====================================

    def obtener(self):
        """✅ Devuelve la fecha en formato ISO (YYYY-MM-DD), lista para
        guardarse directamente en una columna DATE — no el texto mostrado."""

        return self._valor.isoformat() if self._valor else None


    def establecer(self, fecha):

        self._valor = _a_date(fecha)

        self.campo.value = self._valor.strftime(self.formato) if self._valor else ""

        # ✅ Antes esto no refrescaba el control visualmente si ya estaba
        # montado en pantalla: el valor interno cambiaba pero el texto del
        # campo se quedaba con la fecha anterior hasta el próximo render
        # completo de la página (mismo problema que tenía Selector con
        # establecer_opciones()).
        if self.campo.page:
            self.campo.update()


    def limpiar(self):

        self._valor = None

        self.campo.value = ""

        if self.campo.page:
            self.campo.update()