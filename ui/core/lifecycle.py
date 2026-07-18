"""
============================================================
Sistema La Dulce Tía

Archivo:
    lifecycle.py

Responsabilidad:
    Definir el ciclo de vida estándar de módulos y widgets.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from typing import Dict

from ui.core.events.event_bus import event_bus
from ui.core.events.events import Eventos
from ui.core.state_manager import StateManager


class LifecycleState(Enum):
    """Estados posibles del ciclo de vida."""

    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    SHOWING = "showing"
    HIDDEN = "hidden"
    DESTROYED = "destroyed"


class LifecycleMixin:
    """
    Mixin que añade gestión del ciclo de vida a cualquier clase.

    Proporciona implementaciones predeterminadas para:
        - Suscripción/desuscripción automática a eventos globales.
        - Guardado/restauración de estado al ocultar/mostrar.
        - Manejo de cambios de tema y responsive.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lifecycle_state = LifecycleState.UNINITIALIZED
        self._eventos_registrados = False
        self._module_name = self.__class__.__name__

    # ============================================================
    # GANCHOS PRINCIPALES (Sobrescribir en clases hijas)
    # ============================================================

    def on_init(self) -> None:
        """
        Se ejecuta UNA SOLA VEZ cuando el módulo/widget se inicializa.
        Ideal para cargar configuraciones estáticas.
        """
        pass

    def on_show(self) -> None:
        """
        Se ejecuta CADA VEZ que el módulo/widget se vuelve visible.
        Ideal para restaurar estado y refrescar datos.
        """
        pass

    def on_hide(self) -> None:
        """
        Se ejecuta CADA VEZ que el módulo/widget se oculta.
        Ideal para guardar estado y cancelar temporizadores.
        """
        pass

    def on_destroy(self) -> None:
        """
        Se ejecuta cuando el módulo/widget se destruye.
        Ideal para liberar recursos pesados.
        """
        pass

    def on_theme_changed(self) -> None:
        """
        Se ejecuta cuando el tema del sistema cambia.
        """
        pass

    def on_resize(self, responsive_info) -> None:
        """
        Se ejecuta cuando la ventana cambia de tamaño.
        responsive_info contiene el ancho, alto y breakpoint.
        """
        pass

    # ============================================================
    # GESTIÓN DE EVENTOS (Automática)
    # ============================================================

    def _suscribir_eventos_globales(self) -> None:
        """
        Suscribe el módulo a eventos críticos del sistema.
        """
        if self._eventos_registrados:
            return

        event_bus.suscribir(Eventos.CAMBIO_TEMA, self._on_cambio_tema)
        event_bus.suscribir(Eventos.CAMBIO_RESPONSIVE, self._on_cambio_responsive)

        self._eventos_registrados = True

    def _cancelar_eventos_globales(self) -> None:
        """
        Cancela la suscripción a eventos críticos.
        """
        if not self._eventos_registrados:
            return

        event_bus.cancelar(Eventos.CAMBIO_TEMA, self._on_cambio_tema)
        event_bus.cancelar(Eventos.CAMBIO_RESPONSIVE, self._on_cambio_responsive)

        self._eventos_registrados = False

    def _on_cambio_tema(self) -> None:
        """Callback interno para cambio de tema."""
        self.on_theme_changed()
        # Si la vista existe, la actualizamos
        if hasattr(self, "view") and self.view:
            self.view.update()

    def _on_cambio_responsive(self, info) -> None:
        """Callback interno para cambio de tamaño."""
        self.on_resize(info)

    # ============================================================
    # GESTIÓN DE ESTADO (Automática)
    # ============================================================

    def _restaurar_estado(self) -> None:
        """
        Recupera el estado guardado y lo aplica.
        """
        estado = StateManager.recuperar(self._module_name)
        if estado:
            # Si la clase tiene un atributo `estado`, lo actualizamos
            if hasattr(self, "estado") and isinstance(self.estado, dict):
                self.estado.update(estado)

            # Si tiene métodos específicos para restaurar, se llaman aquí
            if hasattr(self, "_aplicar_estado"):
                self._aplicar_estado(estado)

    def _guardar_estado(self) -> None:
        """
        Guarda el estado actual del módulo.
        """
        estado_a_guardar = {}

        # Si la clase tiene un atributo `estado`, lo guardamos
        if hasattr(self, "estado") and isinstance(self.estado, dict):
            estado_a_guardar.update(self.estado)

        # Si tiene un método para extraer estado, lo llamamos
        if hasattr(self, "_extraer_estado"):
            extra = self._extraer_estado()
            if isinstance(extra, dict):
                estado_a_guardar.update(extra)

        if estado_a_guardar:
            StateManager.guardar(self._module_name, estado_a_guardar)

    # ============================================================
    # MÉTODOS PÚBLICOS DEL CICLO DE VIDA
    # ============================================================

    def inicializar(self) -> None:
        """
        Inicializa el módulo si no lo está.
        """
        if self._lifecycle_state != LifecycleState.UNINITIALIZED:
            return

        self._suscribir_eventos_globales()
        self.on_init()
        self._lifecycle_state = LifecycleState.INITIALIZED

    def mostrar(self) -> None:
        """
        Marca el módulo como visible y ejecuta on_show.
        """
        if self._lifecycle_state == LifecycleState.DESTROYED:
            return

        # Si no está inicializado, lo inicializamos primero
        if self._lifecycle_state == LifecycleState.UNINITIALIZED:
            self.inicializar()

        self._suscribir_eventos_globales()
        self._restaurar_estado()
        self.on_show()
        self._lifecycle_state = LifecycleState.SHOWING

    def ocultar(self) -> None:
        """
        Marca el módulo como oculto y ejecuta on_hide.
        """
        if self._lifecycle_state in (LifecycleState.HIDDEN, LifecycleState.DESTROYED):
            return

        self._guardar_estado()
        self.on_hide()
        self._lifecycle_state = LifecycleState.HIDDEN

    def destruir(self) -> None:
        """
        Destruye el módulo y libera recursos.
        """
        if self._lifecycle_state == LifecycleState.DESTROYED:
            return

        self._guardar_estado()
        self.on_destroy()
        self._cancelar_eventos_globales()
        self._lifecycle_state = LifecycleState.DESTROYED

    @property
    def lifecycle_state(self) -> LifecycleState:
        return self._lifecycle_state