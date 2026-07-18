"""
============================================================
Sistema La Dulce Tía

Archivo:
    dashboard_module.py

Responsabilidad:
    Clase base para todos los dashboards del sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from abc import abstractmethod

import flet as ft

from ui.modules.base.module import Module
from ui.widgets.widget_registry import widget_registry


class DashboardModule(Module):
    """
    Clase base para dashboards.

    Su única responsabilidad es registrar los widgets
    y construir el layout.

    No conoce permisos, roles ni lógica de widgets.
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

        self.widgets = widget_registry

    def construir(self):

        # Evita widgets duplicados
        self.widgets.limpiar()

        # El Registry conocerá el rol actual
        if self.usuario:

            self.widgets.establecer_rol(

                self.usuario.rol

            )

        # El Dashboard registra
        # únicamente los widgets
        self.registrar_widgets()

        return self.crear_layout()
    

    def registrar_widget(

        self,

        nombre,

        widget,

        **kwargs,

    ):

        self.widgets.registrar(

            nombre,

            widget,

            **kwargs,

        )
    
    def crear_layout(self):

        return ft.Column(

            controls=self.widgets.obtener_controles(),

            expand=True,

            spacing=20,

            scroll=ft.ScrollMode.AUTO,

        )

    def mostrar_widget(

        self,

        nombre,

    ):

        self.widgets.mostrar(nombre)

        self.actualizar()

    def ocultar_widget(

        self,

        nombre,

    ):

        self.widgets.ocultar(nombre)

        self.actualizar()

    def obtener_widget(

        self,

        nombre,

    ):

        return self.widgets.obtener(

            nombre,

        )

    def refrescar(self):

        self.widgets.actualizar()

        self.actualizar()

    def on_theme_changed(self):

        self.widgets.actualizar_tema()

    def on_resize(

        self,

        info,

    ):

        self.widgets.on_resize(info)

    def on_destroy(self):

        self.widgets.limpiar()


    