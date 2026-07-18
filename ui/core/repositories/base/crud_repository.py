"""
============================================================
Sistema La Dulce Tía

Archivo:
    repository.py

Responsabilidad:
    Clase base para el acceso a datos.

    Centraliza las operaciones comunes para todos los
    los repositorios del sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ui.core.repositories.base.repository import Repository

class CRUDRepository(Repository, ABC):
    """
    Clase base para todos los repositorios.
    Repositorio con operaciones CRUD estándar.
    Únicamente contiene operaciones relacionadas con
    la persistencia de datos.

    No debe contener reglas de negocio.
    """

    def __init__(self, conexion):

        self._conexion = conexion

    @abstractmethod
    def crear(

        self,

        datos: Dict[str, Any],

    ) -> Any:
        """
        Inserta un nuevo registro.
        """

    @abstractmethod
    def actualizar(

        self,

        identificador: Any,

        datos: Dict[str, Any],

    ) -> bool:
        """
        Actualiza un registro.
        """

    @abstractmethod
    def eliminar(

        self,

        identificador: Any,

    ) -> bool:
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

    def existe(

        self,

        identificador,

    ) -> bool:

        return (

            self.obtener(

                identificador,

            )

            is not None

        )

    def contar(self):

        return len(

            self.listar()

        )

    def obtener_varios(

        self,

        identificadores,

    ):

        registros = []

        for identificador in identificadores:

            registro = self.obtener(

                identificador,

            )

            if registro:

                registros.append(

                    registro,

                )

        return registros

    def refrescar(

        self,

        identificador,

    ):

        return self.obtener(

            identificador,

        )

   

