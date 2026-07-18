"""
============================================================
Sistema La Dulce Tía

Archivo:
    crud_module.py

Responsabilidad:
    Clase base para todos los módulos CRUD.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from abc import abstractmethod

import flet as ft

from ui.components.crud_view import CRUDView
from ui.core.events.event_bus import event_bus
from ui.core.events.events import Eventos
from ui.components.mensajes import MensajeSistema
from ui.layouts.crud_layout import CRUDLayout
from ui.modules.base.module import Module 


class CRUDModule(Module):
    """
    Clase base reutilizable para módulos CRUD.
    Hereda el ciclo de vida y funcionalidades comunes de Module.
    """

    def __init__(self, page: ft.Page, usuario=None):
        # Inicializar Module (incluye page, usuario, tema, estado {}, etc.)
        super().__init__(page, usuario)

        # Atributos específicos de CRUD
        self.modo = "consulta"           # "consulta", "nuevo", "editar"
        self.toolbar = None
        self.tabla = None
        self.formulario = None
        self.paginador = None

        # Crear los componentes (toolbar, tabla, formulario, paginador)
        self._crear_componentes()

        # Registrar eventos si es necesario
        self.registrar_eventos()

    # ---------- Métodos abstractos que deben implementar las subclases ----------
    @abstractmethod
    def obtener_titulo(self) -> str:
        """Título del módulo."""
        ...

    @abstractmethod
    def obtener_icono(self) -> str:
        """Icono del módulo."""
        ...

    @abstractmethod
    def crear_toolbar(self) -> ft.Control:
        """Crea la barra de herramientas."""
        ...

    @abstractmethod
    def crear_formulario(self) -> ft.Control:
        """Crea el formulario de edición/creación."""
        ...

    @abstractmethod
    def crear_tabla(self) -> ft.Control:
        """Crea la tabla o listado de datos."""
        ...

    # ---------- Métodos opcionales para sobrescribir ----------
    def crear_paginador(self):
        """Crea el paginador (por defecto None)."""
        return None

    def registrar_eventos(self):
        """Registra suscripciones a eventos del bus."""
        pass

    # ---------- Construcción de la vista (ciclo de vida) ----------
    def construir(self) -> ft.Control:
        """
        Construye y retorna la vista completa del módulo CRUD.
        Este método es llamado por Module.crear().
        """
        # Si por alguna razón los componentes no se han creado, los creamos
        if self.toolbar is None:
            self._crear_componentes()

        return CRUDView(
            titulo=self.obtener_titulo(),
            icono=self.obtener_icono(),
            toolbar=self.toolbar,
            historial=self.tabla,
            formulario=self.formulario,
            paginador=self.paginador,
        )

    # ---------- Métodos auxiliares ----------
    def _crear_componentes(self):
        """Crea todos los componentes internos."""
        self.toolbar = self.crear_toolbar()
        self.formulario = self.crear_formulario()
        self.tabla = self.crear_tabla()
        self.paginador = self.crear_paginador()

    def cambiar_estado(self, estado: str):
        """Cambia el modo actual (consulta, nuevo, editar)."""
        self.modo = estado

    @property
    def nuevo(self) -> bool:
        return self.modo == "nuevo"

    @property
    def editando(self) -> bool:
        return self.modo == "editar"

    @property
    def consulta(self) -> bool:
        return self.modo == "consulta"

    def confirmar(self, titulo: str, mensaje: str, aceptar: callable):
        """
        Muestra un diálogo de confirmación.
        """
        from ui.components.dialogo import DialogoConfirmacion

        dialogo = DialogoConfirmacion(
            titulo=titulo,
            mensaje=mensaje,
            on_accept=aceptar,
        )
        self.page.dialog = dialogo
        dialogo.open = True
        self.page.update()
