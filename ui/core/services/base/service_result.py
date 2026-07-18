"""
============================================================
Sistema La Dulce Tía

Archivo:
    service_result.py

Responsabilidad:
    Representar el resultado de una operación realizada por
    un Service.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ServiceResult:
    """
    Resultado estándar devuelto por todos los servicios.
    """

    exito: bool

    mensaje: str = ""

    datos: Any = None

    errores: dict[str, str] = field(default_factory=dict)

    @property
    def fallo(self) -> bool:

        return not self.exito

    @property
    def tiene_errores(self) -> bool:

        return len(self.errores) > 0

    def agregar_error(
        self,
        campo: str,
        mensaje: str,
    ):

        self.errores[campo] = mensaje

    @classmethod
    def ok(
        cls,
        mensaje: str = "",
        datos=None,
    ):

        return cls(
            exito=True,
            mensaje=mensaje,
            datos=datos,
        )

    @classmethod
    def error(
        cls,
        mensaje: str,
        errores=None,
    ):

        return cls(
            exito=False,
            mensaje=mensaje,
            errores=errores or {},
        )

