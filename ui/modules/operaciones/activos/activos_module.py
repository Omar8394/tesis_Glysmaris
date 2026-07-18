"""
============================================================
Sistema La Dulce Tía

Archivo:
    activo_module.py

Responsabilidad:
    Módulo de gestión de recursos del negocio (activos).
    Vista con catálogo de tarjetas, toolbar con filtros,
    resumen y asistente para crear/editar.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.modules.base.module import Module
from ui.components.toolbar import Toolbar
from ui.components.buscador import Buscador
from ui.components.selector import Selector
from ui.components.boton import BotonPrimario
from ui.components.dialogo import Dialogo
from ui.components.mensajes import MensajeSistema
from ui.components.tarjetas import TarjetaResumen
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing
from ui.core.services.factory import ServiceFactory

from ui.components.activos.activo_wizard import ActivoWizard
from ui.components.activos.activo_tarjeta import TarjetaActivo


class ActivoModule(Module):
    """
    Módulo de recursos del negocio.
    """

    def __init__(self, page: ft.Page, content_area: ft.Control):
        super().__init__(page)  # Module espera solo page
        self.content_area = content_area
        self.servicio = ServiceFactory.get_activo_service()

        # Estado
        self._filtro_texto = ""
        self._filtro_tipo = ""
        self._activos_mostrados = []
        self._activo_editando = None
        self._dialogo = None

        # --- Componentes UI ---
        self.buscador = Buscador(
            buscar=self._aplicar_filtros,
            placeholder="Buscar recurso...",
            width=300,
            mostrar_limpiar=False,      # ✅ quita el botón "X"
            mostrar_actualizar=False, 
        )
        self.filtro_tipo = Selector(
            etiqueta="Tipo",
            opciones=["Todos"] + self.servicio.TIPOS_VALIDOS,
            valor="Todos",
            width=180,
            on_change=lambda e: self._aplicar_filtros(),
        )
        self.orden_selector = Selector(
            etiqueta="Ordenar por",
            opciones=["Nombre (A-Z)", "Nombre (Z-A)", "Costo (menor)", "Costo (mayor)"],
            valor="Nombre (A-Z)",
            width=200,
            on_change=lambda e: self._aplicar_filtros(),
        )
        self.btn_nuevo = BotonPrimario(
            texto="Nuevo Recurso",
            icono=AppIcons.ADD,
            on_click=lambda e: self._abrir_wizard(),
        )

        self.toolbar = Toolbar(
            izquierda=[self.buscador, self.filtro_tipo],
            derecha=[self.orden_selector, self.btn_nuevo],
        )

        # Grid de tarjetas
        self.grid = ft.GridView(
            expand=True,
            runs_count=0,
            max_extent=280,
            spacing=AppSpacing.CONTROL_SPACING,
            run_spacing=AppSpacing.CONTROL_SPACING,
            padding=AppSpacing.MD,
        )

        # Resumen
        self.resumen_total = TarjetaResumen(
            titulo="Total Recursos", valor=0, icono=AppIcons.INVENTARIO, width=180
        )
        self.resumen_activos = TarjetaResumen(
            titulo="Activos", valor=0, icono=AppIcons.CHECK,
            color=ft.colors.GREEN, width=180
        )
        self.resumen_tipos = TarjetaResumen(
            titulo="Tipos", valor=0, icono=AppIcons.CATEGORY,
            color=ft.colors.BLUE, width=180
        )
        self.resumen_row = ft.Row(
            [self.resumen_total, self.resumen_activos, self.resumen_tipos],
            spacing=AppSpacing.CONTROL_SPACING,
            wrap=True,
        )

        # Vista principal
        self.view = ft.Column(
            [
                self.toolbar,
                self.resumen_row,
                ft.Container(content=self.grid, expand=True, padding=AppSpacing.MD),
            ],
            expand=True,
            spacing=0,
        )

        # Carga inicial
        #self.cargar()

    # ------------------------------------------------------------
    #  Construcción e inicialización
    # ------------------------------------------------------------

    def construir(self) -> ft.Control:
        """Devuelve la vista del módulo."""
        return self.view
    
    def on_show(self):
        """Se ejecuta cuando el módulo se hace visible."""
        self.cargar()

    # ------------------------------------------------------------
    #  Carga, filtrado y orden
    # ------------------------------------------------------------

    def cargar(self):
        """Carga los activos desde el servicio y aplica filtros/orden."""
        activos = self.servicio.listar()

        # Filtro por texto
        if self._filtro_texto:
            texto = self._filtro_texto.lower()
            activos = [
                a for a in activos
                if texto in a["nombre"].lower() or texto in a["tipo"].lower()
            ]

        # Filtro por tipo
        if self._filtro_tipo and self._filtro_tipo != "Todos":
            activos = [a for a in activos if a["tipo"] == self._filtro_tipo]

        # Orden
        orden = self.orden_selector.value
        if orden == "Nombre (A-Z)":
            activos.sort(key=lambda x: x["nombre"].lower())
        elif orden == "Nombre (Z-A)":
            activos.sort(key=lambda x: x["nombre"].lower(), reverse=True)
        elif orden == "Costo (menor)":
            activos.sort(key=lambda x: x["costo_unitario"])
        elif orden == "Costo (mayor)":
            activos.sort(key=lambda x: x["costo_unitario"], reverse=True)

        self._activos_mostrados = activos
        self._refrescar_grid()
        self._actualizar_resumen()
        if self.page:        
            self.actualizar()

    def _refrescar_grid(self):
        """Reconstruye el grid con las tarjetas."""
        self.grid.controls.clear()
        for activo in self._activos_mostrados:
            tarjeta = self._crear_tarjeta(activo)
            self.grid.controls.append(tarjeta)
        if self.page:        # ✅ solo si ya está en la página
            self.grid.update()

    def _actualizar_resumen(self):
        """Actualiza las tarjetas de resumen."""
        total = len(self._activos_mostrados)
        activos = sum(1 for a in self._activos_mostrados if a["estado"] == "activo")
        tipos = len(set(a["tipo"] for a in self._activos_mostrados))

        self.resumen_total.content.controls[1].controls[0].value = str(total)
        self.resumen_activos.content.controls[1].controls[0].value = str(activos)
        self.resumen_tipos.content.controls[1].controls[0].value = str(tipos)
        if self.page:        # ✅ solo si ya está en la página
            self.resumen_row.update()

    def _aplicar_filtros(self):
        """Aplica los filtros y recarga."""
        self._filtro_texto = self.buscador.obtener() or ""
        self._filtro_tipo = self.filtro_tipo.value or ""
        self.cargar()

    # ------------------------------------------------------------
    #  Creación de tarjetas (con menú contextual)
    # ------------------------------------------------------------

    def _crear_tarjeta(self, activo: dict) -> ft.Control:
        """Crea la tarjeta reutilizable (con menú contextual) de un activo."""
        return TarjetaActivo(
            activo=activo,
            on_editar=lambda a: self._editar_activo(a["id_activo"]),
            on_duplicar=lambda a: self._duplicar_activo(a["id_activo"]),
            on_cambiar_estado=lambda a: self._cambiar_estado(a["id_activo"]),
            on_eliminar=lambda a: self._eliminar_activo(a["id_activo"]),
        )

    # ------------------------------------------------------------
    #  Acciones: Wizard, guardar, editar, duplicar, estado, eliminar
    # ------------------------------------------------------------

    def _abrir_wizard(self, datos: dict | None = None):
        """Abre el diálogo con el asistente."""
        wizard = ActivoWizard(
            datos_iniciales=datos or {},
            on_guardar=self._guardar_activo,
            on_cancelar=self._cerrar_dialogo,
            tipos_disponibles=self.servicio.TIPOS_VALIDOS,
        )
        self._dialogo = Dialogo.personalizado(
            page=self.page,
            titulo="Nuevo Recurso" if not datos else "Editar Recurso",
            contenido=wizard,
            acciones=[],
            ancho=750,
            modal=True,
        )

    def _cerrar_dialogo(self):
        """Cierra el diálogo actual."""
        if self._dialogo:
            self._dialogo.cerrar()
            self._dialogo = None

    def _guardar_activo(self, datos: dict):
        """Callback del wizard para guardar (crear o actualizar)."""
        if self._activo_editando:
            resultado = self.servicio.actualizar(self._activo_editando, datos)
            if resultado.exito:
                MensajeSistema.exito(self.page, "Recurso actualizado.")
                self._activo_editando = None
                self._cerrar_dialogo()
                self.cargar()
            else:
                MensajeSistema.error(self.page, resultado.mensaje)
        else:
            resultado = self.servicio.crear(datos)
            if resultado.exito:
                MensajeSistema.exito(self.page, "Recurso creado.")
                self._cerrar_dialogo()
                self.cargar()
            else:
                MensajeSistema.error(self.page, resultado.mensaje)

    def _editar_activo(self, activo_id: int):
        """Abre el wizard en modo edición."""
        activo = self.servicio.obtener(activo_id)
        if not activo:
            MensajeSistema.error(self.page, "Recurso no encontrado.")
            return
        self._activo_editando = activo_id
        self._abrir_wizard(activo)

    def _duplicar_activo(self, activo_id: int):
        """Duplica un activo existente."""
        resultado = self.servicio.duplicar(activo_id)
        if resultado.exito:
            MensajeSistema.exito(self.page, "Recurso duplicado.")
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _cambiar_estado(self, activo_id: int):
        """Cambia estado activo/inactivo."""
        activo = self.servicio.obtener(activo_id)
        if not activo:
            return
        nuevo_estado = "inactivo" if activo["estado"] == "activo" else "activo"
        resultado = self.servicio.cambiar_estado(activo_id, nuevo_estado)
        if resultado.exito:
            MensajeSistema.informacion(self.page, f"Estado cambiado a {nuevo_estado}.")
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _eliminar_activo(self, activo_id: int):
        """Solicita confirmación para eliminar."""
        activo = self.servicio.obtener(activo_id)
        if not activo:
            return
        Dialogo.confirmacion(
            page=self.page,
            mensaje=f"¿Estás seguro de eliminar el recurso '{activo['nombre']}'?",
            on_confirmar=lambda e: self._confirmar_eliminar(activo_id),
            titulo="Eliminar recurso",
            texto_confirmar="Eliminar",
            texto_cancelar="Cancelar",
        )

    def _confirmar_eliminar(self, activo_id: int):
        """Ejecuta la eliminación después de confirmar."""
        resultado = self.servicio.eliminar(activo_id)
        if resultado.exito:
            MensajeSistema.exito(self.page, "Recurso eliminado.")
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)