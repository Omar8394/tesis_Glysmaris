"""
============================================================
Sistema La Dulce Tía

Archivo:
    module_registry.py

Responsabilidad:
    Registro central de módulos del sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Dict

from .module import Module

class ModuleRegistry:
    """
    Administra todos los módulos del sistema.
    """

    def __init__(self):

        self._modules: Dict[str, Module] = {}

        self._actual = None

    def registrar(

        self,

        nombre,

        modulo,

    ):

        self._modules[nombre] = modulo


    def obtener(

        self,

        nombre,

    ):

        return self._modules.get(nombre)
    
    def mostrar(

        self,

        nombre,

    ):

        if nombre not in self._modules:

            raise ValueError(

                f"Módulo '{nombre}' inexistente."

            )

        if self._actual:

            self._actual.on_hide()

        modulo = self._modules[nombre]

        modulo.inicializar()

        modulo.on_show()

        self._actual = modulo

        return modulo.obtener_vista()

    def destruir(

        self,

        nombre,

    ):

        modulo = self._modules.get(nombre)

        if not modulo:

            return

        modulo.on_destroy()

        del self._modules[nombre]

    @property

    def actual(self):

        return self._actual

    def __iter__(self):

        return iter(

            self._modules.values()

        )

    def limpiar(self):

        for modulo in self._modules.values():

            modulo.on_destroy()

        self._modules.clear()

        self._actual = None

module_registry = ModuleRegistry()

