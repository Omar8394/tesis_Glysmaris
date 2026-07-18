"""
============================================================
Sistema La Dulce Tía

Archivo:
    widget.py

Responsabilidad:
    Clase base para todos los widgets del sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

import flet as ft

from ui.core.events.event_bus import event_bus
from ui.core.theme_manager import ThemeManager
from ui.core.lifecycle import LifecycleMixin

class Widget(ABC,LifecycleMixin):
    """
    Clase base para widgets reutilizables.
    """
    def __init__(

        self,

        page,

    ):
         # Inicializar el LifecycleMixin
        super().__init__()
        
        self.page = page
        self.tema = ThemeManager.theme
        self.control = None
        
        # Estado interno del widget (lo usa el registry)
        self._visible = True
        self._minimizado = False

    def crear(self):

        self.control = self.construir()
        self.inicializar()

        return self.control

    @abstractmethod
    def construir(self):

        ...

    def actualizar(self):

        if self.control:

            self.control.update()

    def emitir(

        self,

        evento,

        *args,

        **kwargs,

    ):

        event_bus.emitir(

            evento,

            *args,

            **kwargs,

        )

    def suscribir(

        self,

        evento,

        callback,

    ):

        event_bus.suscribir(

            evento,

            callback,

        )

    def cancelar(

        self,

        evento,

        callback,

    ):

        event_bus.cancelar(

            evento,

            callback,

        )

    def actualizar_tema(self):

        self.tema = ThemeManager.theme

        self.on_theme_changed()

    def on_init(self) -> None:
        """Se ejecuta una sola vez al crear el widget."""
        # Aquí puedes cargar configuraciones estáticas
        pass

    def on_show(self) -> None:
        """Se ejecuta cuando el widget se vuelve visible."""
        # Si el control existe y estaba oculto, lo mostramos
        if self.control and not self._visible:
            self._visible = True
            self.control.visible = True
            self.control.update()

    def on_hide(self) -> None:
        """Se ejecuta cuando el widget se oculta."""
        if self.control and self._visible:
            self._visible = False
            self.control.visible = False
            self.control.update()

    def on_destroy(self) -> None:
        """Libera recursos pesados si los hubiera."""
        pass

    def on_theme_changed(self) -> None:
        """Actualiza el tema y refresca el control."""
        self.tema = ThemeManager.theme
        if self.control:
            self.control.update()

    def on_resize(self, responsive_info) -> None:
        """Reacciona a cambios de tamaño."""
        # Si el widget necesita redibujarse, se hace aquí
        pass

    def mostrar(self) -> None:
        """Hace visible el widget."""
        # LifecycleMixin ya tiene mostrar(), pero lo sobrescribimos
        # para que además actualice el control.
        super().mostrar()
        if self.control:
            self.control.visible = True
            self.control.update()

    def ocultar(self) -> None:
        """Oculta el widget."""
        super().ocultar()
        if self.control:
            self.control.visible = False
            self.control.update()

    def minimizar(self) -> None:
        """Alternativa para minimizar (puede cambiar tamaño a 0)."""
        self._minimizado = True
        # Aquí podrías reducir la altura del control a 0
        # o cambiar su contenido a un ícono de minimizado.

    def restaurar(self) -> None:
        """Restaura el widget de su estado minimizado."""
        self._minimizado = False

