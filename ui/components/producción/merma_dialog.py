"""
============================================================
Sistema La Dulce Tía

Archivo:
    merma_dialog.py

Responsabilidad:
    Diálogo para registrar mermas al finalizar una orden.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.dialogo import Dialogo
from ui.components.campo_texto import CampoTexto
from ui.components.selector import Selector
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.core.spacing import AppSpacing


class MermaDialog:
    """Diálogo para registrar mermas de producción."""

    def __init__(self, page: ft.Page, id_orden: int, on_guardar: callable):
        self.page = page
        self.id_orden = id_orden
        self.on_guardar = on_guardar
        self.dialogo = None

        # Campos
        self.cantidad = CampoTexto(
            etiqueta="Cantidad",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0",
        )
        self.tipo = Selector(
            etiqueta="Tipo",
            opciones=["recuperable", "no_recuperable"],
            valor="no_recuperable",
            width=180,
        )
        self.motivo = Selector(
            etiqueta="Motivo",
            opciones=["quemado", "rotura", "contaminacion", "error_preparacion", "decoracion", "otro"],
            valor="otro",
            width=200,
        )
        self.descripcion = CampoTexto(
            etiqueta="Descripción",
            multiline=True,
            width=350,
            hint="Detalles adicionales...",
        )

    def abrir(self):
        """Abre el diálogo."""
        contenido = ft.Column(
            [
                ft.Text(f"Registrar merma para orden #{self.id_orden}", weight="bold"),
                ft.Row([self.cantidad, self.tipo, self.motivo], spacing=AppSpacing.CONTROL_SPACING),
                ft.Row([self.descripcion]),
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            width=450,
        )

        def guardar(e):
            datos = {
                "cantidad": float(self.cantidad.value) if self.cantidad.value else 0,
                "tipo_merma": self.tipo.value,
                "motivo": self.motivo.value,
                "descripcion": self.descripcion.value or "",
            }
            if datos["cantidad"] <= 0:
                self._mostrar_error("La cantidad debe ser mayor a 0.")
                return
            self.on_guardar(datos)
            self.cerrar()

        def saltar(e):
            self.on_guardar(None)
            self.cerrar()

        self.dialogo = Dialogo.personalizado(
            page=self.page,
            titulo="Registrar merma",
            contenido=contenido,
            acciones=[
                BotonSecundario(texto="Saltar", icono=ft.icons.SKIP_NEXT, on_click=saltar),
                BotonPrimario(texto="Guardar", icono=ft.icons.SAVE, on_click=guardar),
            ],
            ancho=500,
            modal=True,
        )

    def cerrar(self):
        if self.dialogo:
            self.dialogo.cerrar()
            self.dialogo = None

    def _mostrar_error(self, mensaje: str):
        from ui.components.mensajes import MensajeSistema
        MensajeSistema.error(self.page, mensaje)