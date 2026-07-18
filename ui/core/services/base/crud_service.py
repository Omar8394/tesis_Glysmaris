"""
============================================================
Sistema La Dulce Tía

Archivo:
    crud_service.py

Responsabilidad:
    Clase base para todos los servicios CRUD.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

class CRUDService(ABC):
    """
    Clase base para todos los servicios del sistema.

    Centraliza las operaciones CRUD y define
    el contrato que deberán implementar los
    servicios concretos.
    """

    def __init__(self):

        super().__init__()

    @abstractmethod
    def crear(

        self,

        datos: Dict[str, Any],

    ) -> tuple[bool, str]:

        """
        Crea un nuevo registro.
        """

    @abstractmethod
    def actualizar(

        self,

        identificador: Any,

        datos: Dict[str, Any],

    ) -> tuple[bool, str]:

        """
        Actualiza un registro existente.
        """

    @abstractmethod
    def eliminar(

        self,

        identificador: Any,

    ) -> tuple[bool, str]:

        """
        Elimina un registro.
        """

    @abstractmethod
    def obtener(

        self,

        identificador: Any,

    ) -> Optional[Dict]:

        """
        Devuelve un registro.
        """

    @abstractmethod
    def listar(self) -> List[Dict]:

        """
        Devuelve todos los registros.
        """

    @abstractmethod
    def buscar(

        self,

        texto: str,

    ) -> List[Dict]:

        """
        Busca registros.
        """

    @abstractmethod
    def validar(

        self,

        datos: Dict[str, Any],

    ) -> tuple[bool, str]:

        """
        Valida la información antes de guardarla.
        """

    def existe(

        self,

        identificador,

    ) -> bool:

        return self.obtener(

            identificador,

        ) is not None
    
    def contar(self) -> int:

        return len(

            self.listar()

        )
    
    def guardar(
        self,
        datos: Dict[str, Any],
        identificador: Any = None,
    ) -> tuple[bool, str]:
        """
        Crea o actualiza un registro según exista
        un identificador.
        """

        valido, mensaje = self.validar(datos)

        if not valido:
            return False, mensaje

        if identificador is None:
            return self.crear(datos)

        return self.actualizar(
            identificador,
            datos,
        )
