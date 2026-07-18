"""
============================================================
Sistema La Dulce Tía

Archivo:
    responsive_layout.py

Responsabilidad:
    Sistema de diseño responsivo reutilizable.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import flet as ft

from ui.core.events.event_bus import event_bus
from ui.core.events.events import Eventos

class Breakpoint(Enum):

    MOVIL = 600

    TABLET = 900

    ESCRITORIO = 1200

    GRANDE = 99999

@dataclass
class ResponsiveInfo:

    ancho: float

    alto: float

    breakpoint: Breakpoint

    es_movil: bool

    es_tablet: bool

    es_escritorio: bool

class ResponsiveLayout(ft.Container):

    """
    Administra el comportamiento responsivo de la aplicación.
    """
    def __init__(

        self,

        page: ft.Page,

        contenido: ft.Control,

    ):

        super().__init__()

        self.page = page

        self.expand = True

        self.content = contenido

        self.info = None

        self.page.on_resize = self._on_resize

        self._actualizar()

    def _on_resize(

        self,

        e,

    ):

        self._actualizar()

    def _obtener_breakpoint(

        self,

        ancho,

    ):

        if ancho < Breakpoint.MOVIL.value:

            return Breakpoint.MOVIL

        if ancho < Breakpoint.TABLET.value:

            return Breakpoint.TABLET

        if ancho < Breakpoint.ESCRITORIO.value:

            return Breakpoint.ESCRITORIO

        return Breakpoint.GRANDE

    def _actualizar(self):

        bp = self._obtener_breakpoint(

            self.page.width,

        )

        self.info = ResponsiveInfo(

            ancho=self.page.width,

            alto=self.page.height,

            breakpoint=bp,

            es_movil=bp == Breakpoint.MOVIL,

            es_tablet=bp == Breakpoint.TABLET,

            es_escritorio=bp in (

                Breakpoint.ESCRITORIO,

                Breakpoint.GRANDE,

            ),

        )

        event_bus.emitir(

            Eventos.CAMBIO_RESPONSIVE,

            self.info,

        )

        self.update()

    @property
    def responsive(self):

        return self.info

class ResponsiveRow(ft.Row):

    """
    Cambia automáticamente entre Row y Column.
    """
    def __init__(

        self,

        page,

        controls,

    ):

        super().__init__()

        self.page = page

        self.controls = controls

        self.expand = True

        event_bus.suscribir(

            Eventos.CAMBIO_RESPONSIVE,

            self._responsive,

        )

    def _responsive(

        self,

        info,

    ):

        if info.es_movil:

            self.wrap = True

        else:

            self.wrap = False

        self.update()

