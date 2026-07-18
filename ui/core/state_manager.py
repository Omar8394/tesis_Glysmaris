"""
============================================================
Sistema La Dulce Tía

Archivo:
    state_manager.py

Responsabilidad:
    Gestor central del estado efímero de los módulos.

    Permite que un módulo guarde su estado al ocultarse
    y lo recupere al mostrarse.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any
from typing import Dict


class StateManager:
    """
    Almacén en memoria para el estado de los módulos.
    """

    _states: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def guardar(cls, module_name: str, estado: Dict[str, Any]) -> None:
        """
        Guarda el estado de un módulo.

        Args:
            module_name: Identificador único del módulo.
            estado: Diccionario con el estado a guardar.
        """
        cls._states[module_name] = estado.copy()

    @classmethod
    def recuperar(cls, module_name: str) -> Dict[str, Any]:
        """
        Recupera el estado guardado de un módulo.

        Args:
            module_name: Identificador único del módulo.

        Returns:
            Diccionario con el estado, o vacío si no existe.
        """
        return cls._states.get(module_name, {})

    @classmethod
    def limpiar(cls, module_name: str) -> None:
        """
        Elimina el estado guardado de un módulo.
        """
        if module_name in cls._states:
            del cls._states[module_name]

    @classmethod
    def limpiar_todo(cls) -> None:
        """
        Elimina todos los estados guardados.
        """
        cls._states.clear()