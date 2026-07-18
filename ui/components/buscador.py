"""
============================================================
Sistema La Dulce Tía

Archivo:
    buscador.py

Responsabilidad:
    Componente oficial de búsqueda del sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.campo_texto import CampoTexto
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing

class Buscador(ft.Row):
    """
    Barra de búsqueda reutilizable.
    """

    def __init__(

        self,

        buscar,

        placeholder="Buscar...",

        width=350,

        mostrar_actualizar=True,

        mostrar_limpiar=True,

    ):

        super().__init__()

        self.buscar = buscar

        self.campo = CampoTexto(

            etiqueta=placeholder,

            width=width,

            on_change=self._buscar,

        )

        self.btn_limpiar = ft.IconButton(

            icon=AppIcons.CLEAR,

            tooltip="Limpiar",

            visible=mostrar_limpiar,

            on_click=self._limpiar,

        )

        self.btn_actualizar = ft.IconButton(

            icon=AppIcons.REFRESH,

            tooltip="Actualizar",

            visible=mostrar_actualizar,

            on_click=self._actualizar,

        )

        self.spacing = AppSpacing.SM

        self.controls = [

            self.campo,

            self.btn_limpiar,

            self.btn_actualizar,

        ]

    def _buscar(self, e):

        if self.buscar:

            self.buscar(self.campo.value)

    def _limpiar(self, e):

        self.campo.value = ""

        self.update()

        if self.buscar:

            self.buscar("")

    def _actualizar(self, e):

        if self.buscar:

            self.buscar(self.campo.value)

    def obtener(self):

        return self.campo.value


    def establecer(self, valor):

        self.campo.value = valor

        self.update()


    def limpiar(self):

        self._limpiar(None)


    def enfocar(self):

        self.campo.focus()


        