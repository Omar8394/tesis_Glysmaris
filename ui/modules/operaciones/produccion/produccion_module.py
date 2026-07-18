"""
============================================================
Sistema La Dulce Tía

Archivo:
    produccion_module.py

Responsabilidad:
    Módulo principal del Centro de Producción.

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
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing
from ui.core.services.factory import ServiceFactory

from ui.components.producción.panel_estados import PanelEstados
from ui.components.producción.merma_dialog import MermaDialog
from ui.components.producción.produccion_wizard import ProduccionWizard


class ProduccionModule(Module):
    """Módulo principal de producción."""

    def __init__(self, page: ft.Page, content_area: ft.Control):
        super().__init__(page)
        self.content_area = content_area
        self._dialogo = None

        # Servicio real
        self.servicio = ServiceFactory.get_produccion_service()

        # Estado
        self._filtro_estado = ""
        self._filtro_busqueda = ""
        self._ordenes = []

        # Barra de herramientas
        self.buscador = Buscador(
            buscar=self._buscar,
            placeholder="Buscar orden...",
            width=300,
            mostrar_limpiar=True,
            mostrar_actualizar=True,
        )
        self.filtro_estado = Selector(
            etiqueta="Estado",
            opciones=["Todos", "pendiente", "en_proceso", "finalizada", "cancelada"],
            valor="Todos",
            width=160,
            on_change=lambda e: self._aplicar_filtros(),
        )
        self.btn_nuevo = BotonPrimario(
            texto="Nueva Orden",
            icono=AppIcons.ADD,
            on_click=lambda e: self._abrir_wizard(),
        )

        self.toolbar = Toolbar(
            izquierda=[self.buscador, self.filtro_estado],
            derecha=[self.btn_nuevo],
        )

        # Panel de estados (inicialmente vacío)
        self.panel_estados = ft.Container(
            expand=True,
            padding=AppSpacing.MD,
            content=ft.Column(
                [ft.Text("Cargando órdenes...", color=ft.colors.GREY)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Vista principal
        self.view = ft.Column(
            [
                self.toolbar,
                ft.Divider(height=1),
                self.panel_estados,
            ],
            expand=True,
            spacing=0,
        )

        # ❌ NO LLAMAR a cargar() aquí
        # self.cargar()  # <-- ELIMINAR

    def construir(self) -> ft.Control:
        return self.view

    def on_show(self):
        """Se ejecuta cuando el módulo se hace visible."""
        self.cargar()

    def cargar(self):
        """Carga las órdenes de producción."""
        filtros = {}
        if self._filtro_estado and self._filtro_estado != "Todos":
            filtros["estado"] = self._filtro_estado
        if self._filtro_busqueda:
            filtros["buscar"] = self._filtro_busqueda

        self._ordenes = self.servicio.listar(filtros)
        self._actualizar_panel()

    def _actualizar_panel(self):
        """Actualiza el panel con las órdenes filtradas."""
        self.panel_estados.content = PanelEstados(
            ordenes=self._ordenes,
            on_iniciar=self._iniciar_orden,
            on_continuar=self._continuar_orden,
            on_finalizar=self._finalizar_orden,
            on_ver_detalle=self._ver_detalle,
            on_cancelar=self._cancelar_orden,
        )
        if self.page:
            self.panel_estados.update()

    def _aplicar_filtros(self):
        self._filtro_busqueda = self.buscador.obtener() or ""
        self._filtro_estado = self.filtro_estado.value or ""
        self.cargar()

    def _buscar(self, texto):
        self._aplicar_filtros()

    # =========================================================
    # ACCIONES DE ÓRDENES
    # =========================================================

    def _iniciar_orden(self, id_orden):
        resultado = self.servicio.iniciar_produccion(id_orden)
        if resultado.exito:
            MensajeSistema.exito(self.page, "Producción iniciada.")
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _continuar_orden(self, id_orden):
        self._ver_detalle(id_orden)

    def _finalizar_orden(self, id_orden):
        merma_dialog = MermaDialog(
            page=self.page,
            id_orden=id_orden,
            on_guardar=lambda datos: self._confirmar_finalizacion(id_orden, datos),
        )
        merma_dialog.abrir()

    def _confirmar_finalizacion(self, id_orden, datos_merma):
        orden_completa = self.servicio.obtener(id_orden)
        if not orden_completa:
            MensajeSistema.error(self.page, "Orden no encontrada.")
            return

        datos_fin = {
            "detalles": {},
            "mermas": [datos_merma] if datos_merma else [],
        }

        for det in orden_completa.get("detalles", []):
            datos_fin["detalles"][str(det["id_detalle"])] = {
                "cantidad_obtenida": det["cantidad_planificada"],
                "precio_final": det.get("precio_final", 0),
                "costo_calculado": det.get("costo_calculado", 0),
                "disponible_venta": True,
            }

        resultado = self.servicio.finalizar_produccion(id_orden, datos_fin)
        if resultado.exito:
            MensajeSistema.exito(self.page, "Orden finalizada.")
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _ver_detalle(self, id_orden):
        orden_completa = self.servicio.obtener(id_orden)
        if not orden_completa:
            MensajeSistema.error(self.page, "Orden no encontrada.")
            return

        orden = orden_completa["orden"]
        detalles = orden_completa.get("detalles", [])

        productos_textos = []
        for det in detalles:
            nombre = det.get("nombre_producto")
            if not nombre:
                nombre = "Producto {}".format(det.get("id_producto", "?"))
            texto = "• {} x {} (obtenido: {})".format(
                nombre,
                det.get("cantidad_planificada", 0),
                det.get("cantidad_obtenida", 0)
            )
            productos_textos.append(ft.Text(texto))

        contenido = ft.Column(
            [
                ft.Text("Número: {}".format(orden.get("numero_orden", "N/A")), weight="bold"),
                ft.Text("Estado: {}".format(orden.get("estado", "N/A"))),
                ft.Text("Fecha: {}".format(orden.get("fecha_planificada", "N/A"))),
                ft.Text("Prioridad: {}".format(orden.get("prioridad", "N/A"))),
                ft.Divider(height=10),
                ft.Text("Productos:", weight="bold"),
            ]
            + productos_textos,
            spacing=AppSpacing.CONTROL_SPACING,
            width=500,
        )

        Dialogo.personalizado(
            page=self.page,
            titulo="Detalle de orden",
            contenido=contenido,
            acciones=[ft.TextButton("Cerrar", on_click=lambda e: self._cerrar_dialogo())],
            ancho=550,
            modal=True,
        )

    def _cancelar_orden(self, id_orden):
        Dialogo.confirmacion(
            page=self.page,
            titulo="Cancelar orden",
            mensaje="¿Estás seguro de que deseas cancelar esta orden?",
            on_confirmar=lambda e: self._confirmar_cancelar(id_orden),
            texto_confirmar="Cancelar",
            texto_cancelar="Volver",
        )

    def _confirmar_cancelar(self, id_orden):
        resultado = self.servicio.cancelar_orden(id_orden)
        if resultado.exito:
            MensajeSistema.exito(self.page, "Orden cancelada.")
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    # =========================================================
    # WIZARD
    # =========================================================

    def _abrir_wizard(self):
        wizard = ProduccionWizard(
            on_guardar=self._crear_orden_desde_wizard,
            on_cancelar=self._cerrar_dialogo,
        )
        self._dialogo = Dialogo.personalizado(
            page=self.page,
            titulo="Nueva Orden de Producción",
            contenido=wizard,
            acciones=[],
            ancho=800,
            modal=True,
        )

    def _cerrar_dialogo(self):
        if self._dialogo:
            self._dialogo.cerrar()
            self._dialogo = None

    def _crear_orden_desde_wizard(self, datos):
        resultado = self.servicio.crear_orden(datos)
        if resultado.exito:
            MensajeSistema.exito(
                self.page,
                "Orden {} creada.".format(resultado.datos["orden"]["numero_orden"])
            )
            self._cerrar_dialogo()
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)