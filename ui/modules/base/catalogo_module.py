"""
============================================================
Sistema La Dulce Tía

Archivo:
    catalogo_module.py

Responsabilidad:
    Clase base para módulos tipo catálogo.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from abc import abstractmethod

import flet as ft

from ui.modules.base.module import Module

from ui.components.toolbar import Toolbar

from ui.components.buscador import Buscador

from ui.components.paginador import Paginador

class CatalogoModule(Module):
    """
    Clase base para catálogos.
    """

    def __init__(

        self,

        page,

        usuario=None,

    ):

        super().__init__(

            page,

            usuario,

        )

        self.toolbar = None

        self.buscador = None

        self.lista = None

        self.paginador = None

    def construir(self):

        self.toolbar = self.crear_toolbar()

        self.lista = self.crear_lista()

        self.paginador = self.crear_paginador()

        return self.crear_layout()

    def crear_toolbar(self):

        self.buscador = Buscador(

            on_change=self.buscar,

        )

        return Toolbar(

            izquierda=[

                self.buscador,

            ],

            derecha=self.botones_toolbar(),

        )

    @abstractmethod
    def crear_lista(self):
        ...

    @abstractmethod
    def botones_toolbar(self):
        ...

    @abstractmethod
    def buscar(

        self,

        texto,

    ):
        ...

    def crear_paginador(self):

        return Paginador(

            on_change=self.cambiar_pagina,

        )

    def cambiar_pagina(

        self,

        pagina,

        cantidad,

    ):

        pass


    def crear_layout(self):

        return ft.Column(

            [

                self.toolbar,

                self.lista,

                self.paginador,

            ],

            expand=True,

        )

