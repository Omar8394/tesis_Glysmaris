"""
============================================================
Sistema La Dulce Tía

Archivo:
    module.py

Responsabilidad:
    Clase base para todos los módulos del sistema.

Todos los módulos deberán heredar de esta clase.

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
from ui.components.mensajes import MensajeSistema


class Module(ABC):
    """
    Clase base de todos los módulos del sistema.
    """
    def __init__(

        self,

        page: ft.Page,

        usuario=None,

    ):
        super().__init__()

        self.page = page
        self.usuario = usuario
        self.tema = ThemeManager.theme
        self.view = None
        self.estado = {}  # Diccionario de estado mutable

        # ✅ Faltaba: inicializar() y la property `inicializado` leen
        # self._inicializado, pero nunca se definía acá. Cualquier
        # módulo reventaba con AttributeError apenas ModuleRegistry
        # llamaba a modulo.inicializar() (ej. al mostrar el módulo
        # por primera vez).
        self._inicializado = False

        # El módulo se auto-registra para el ciclo de vida
        self._module_name = f"{self.__class__.__name__}"

    @property

    def inicializado(self):

        return self._inicializado
    
    def inicializar(self):

        """
        Inicializa el módulo.

        Solo se ejecuta una vez.
        """

        if self._inicializado:

            return

        self.on_init()

        self._inicializado = True

    def obtener_vista(self):

        return self.view

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

    def actualizar(self) -> None:
        """Actualiza la vista."""
        if self.view:
            self.view.update()

    def mensaje(self, texto, tipo="info"): 
        getattr(MensajeSistema, tipo)(self.page, texto)

    def guardar_estado(

        self,

        clave,

        valor,

    ):

        self.estado[clave] = valor

    def obtener_estado(

        self,

        clave,

        defecto=None,

    ):

        return self.estado.get(

            clave,

            defecto,

        )

    def tiene_permiso(

        self,

        permiso,

    ):

        return True
    
    

    def on_init(self) -> None:
        """
        Inicializa el módulo. Se ejecuta una sola vez.
        """
        # Aquí podrías cargar configuraciones estáticas
        pass

    def on_show(self) -> None:
        """
        El módulo se muestra. Restauramos el estado y refrescamos.
        """
        # Refrescar datos automáticamente al mostrar
        if hasattr(self, "cargar") and callable(self.cargar):
            self.cargar()

    def on_hide(self) -> None:
        """
        El módulo se oculta. Guardamos el estado.
        """
        # Guardamos el estado automáticamente
        self._guardar_estado()

    def on_destroy(self) -> None:
        """
        El módulo se destruye.
        """
        pass

    def on_theme_changed(self) -> None:
        """
        Actualiza el tema del módulo.
        """
        self.tema = ThemeManager.theme
        if self.view:
            self.view.update()

    def on_resize(self, responsive_info) -> None:
        """
        Maneja el redimensionamiento.
        """
        pass

    @abstractmethod
    def construir(self) -> ft.Control:
        """
        Construye la interfaz. Debe devolver un Control de Flet.
        """
        pass

    def crear(self) -> ft.Control:
        """
        Crea la vista aplicando el ciclo de vida.
        """
        self.view = self.construir()
        self.inicializar()
        return self.view

    def obtener_vista(self) -> ft.Control:
        """Devuelve la vista construida."""
        return self.view
    
    def _extraer_estado(self) -> dict:
        """
        Extrae el estado relevante para guardar.
        Sobrescribir en módulos concretos si tienen datos extra.
        """
        return {
            "filtro": getattr(self, "_filtro_actual", ""),
            "seleccionado": getattr(self, "_seleccionado", None),
        }

    def _aplicar_estado(self, estado: dict) -> None:
        """
        Aplica el estado guardado.
        Sobrescribir en módulos concretos.
        """
        if "filtro" in estado:
            self._filtro_actual = estado["filtro"]
            if hasattr(self, "buscador"):
                self.buscador.establecer(estado["filtro"])

        if "seleccionado" in estado:
            self._seleccionado = estado["seleccionado"]
            