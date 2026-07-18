"""
============================================================
Sistema La Dulce Tía

Archivo:
    event_bus.py

Responsabilidad:
    Bus de eventos interno del sistema.

Permite que los módulos se comuniquen
sin depender unos de otros.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from collections import defaultdict

from typing import Callable

class EventBus:
    """
    Gestor central de eventos.
    """

    def __init__(self):

        self._listeners = defaultdict(list)

    def suscribir(

        self,

        evento: str,

        callback: Callable,

    ):

        """
        Registra un listener.
        """

        self._listeners[evento].append(callback)

    def cancelar(

        self,

        evento,

        callback,

    ):

        if evento not in self._listeners:

            return

        if callback in self._listeners[evento]:

            self._listeners[evento].remove(callback)

    def emitir(

        self,

        evento,

        *args,

        **kwargs,

    ):

        if evento not in self._listeners:

            return

        for callback in self._listeners[evento]:

            callback(

                *args,

                **kwargs,

            )

    def limpiar(self):

        self._listeners.clear()

event_bus = EventBus()