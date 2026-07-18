"""
============================================================
Sistema La Dulce Tía

Archivo:
    barra_acciones.py

Responsabilidad:
    Barra reutilizable de acciones para módulos CRUD.

Contiene:
    - Accion
    - BarraAcciones

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.boton import (
    BotonPrimario,
    BotonSecundario,
)

from ui.core.spacing import AppSpacing

class Accion:
    """
    Representa una acción dentro de una barra.
    """

    def __init__(

        self,

        texto,

        icono,

        callback,

        primario=False,

        visible=True,

    ):

        self.texto = texto

        self.icono = icono

        self.callback = callback

        self.primario = primario

        self.visible = visible

class BarraAcciones(ft.Row):
    """
    Barra reutilizable de botones.
    """

    def __init__(

        self,

        acciones,

        wrap=True,

        expand=False,

    ):

        super().__init__()

        self.spacing = AppSpacing.BUTTON_SPACING

        self.wrap = wrap

        self.expand = expand

        self.controls = []

        for accion in acciones:

            if not accion.visible:

                continue

            if accion.primario:

                boton = BotonPrimario(

                    texto=accion.texto,

                    icono=accion.icono,

                    on_click=accion.callback,

                )

            else:

                boton = BotonSecundario(

                    texto=accion.texto,

                    icono=accion.icono,

                    on_click=accion.callback,

                )

            self.controls.append(boton)

