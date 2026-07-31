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
    """Diálogo para registrar una o más mermas de producción, cada una
    asociada al producto de la orden que corresponda."""

    TIPOS = ["recuperable", "no_recuperable"]
    MOTIVOS = ["quemado", "rotura", "contaminacion", "error_preparacion", "decoracion", "otro"]
    # Unidad en la que se mide la cantidad de la merma: puede ser por
    # conteo (ej. "3 galletas rotas") o por peso/volumen (ej. "20g de
    # retazos de torta"), según convenga para ese recuperable en particular.
    UNIDADES = ["unidad", "g", "kg", "ml", "l"]

    def __init__(self, page: ft.Page, id_orden: int, detalles: list[dict], on_guardar: callable):
        self.page = page
        self.id_orden = id_orden
        self.detalles = detalles or []
        self.on_guardar = on_guardar
        self.dialogo = None
        self._mermas: list[dict] = []

        self._detalles_por_etiqueta = {self._etiqueta_detalle(d): d for d in self.detalles}
        etiquetas = list(self._detalles_por_etiqueta.keys()) or ["Sin productos"]

        self.producto = Selector(etiqueta="Producto", opciones=etiquetas, valor=etiquetas[0], width=220)
        self.cantidad = CampoTexto(
            etiqueta="Cantidad", width=100, keyboard_type=ft.KeyboardType.NUMBER, value="0"
        )
        self.unidad = Selector(etiqueta="Unidad", opciones=self.UNIDADES, valor="unidad", width=110)
        self.tipo = Selector(
            etiqueta="Tipo",
            opciones=self.TIPOS,
            valor="no_recuperable",
            width=160,
            on_change=self._toggle_recuperable,
        )
        self.motivo = Selector(etiqueta="Motivo", opciones=self.MOTIVOS, valor="otro", width=170)
        # Solo aplica a mermas "recuperable": ese sobrante pasa a ser un
        # insumo con identidad propia (ej. "trozos de torta", "polvo de
        # galleta") que puede reutilizarse luego, por eso necesita nombre.
        self.nombre_recuperado = CampoTexto(
            etiqueta="Nombre del recuperable",
            width=460,
            hint="Ej: trozos de torta, polvo de galleta...",
        )
        self.nombre_recuperado.visible = False
        self.descripcion = CampoTexto(
            etiqueta="Descripción", multiline=True, width=460, hint="Detalles adicionales..."
        )
        self.lista_mermas = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, height=160)

    @staticmethod
    def _etiqueta_detalle(detalle: dict) -> str:
        nombre = detalle.get("nombre_producto") or f"Producto {detalle.get('id_producto')}"
        return f"{nombre} (#{detalle.get('id_detalle')})"

    def abrir(self):
        """Abre el diálogo."""
        contenido = ft.Column(
            [
                ft.Text(f"Registrar mermas para orden #{self.id_orden}", weight="bold"),
                ft.Row(
                    [self.producto, self.cantidad, self.unidad],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                ft.Row(
                    [self.tipo, self.motivo],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                ft.Row([self.nombre_recuperado]),
                ft.Row([self.descripcion]),
                ft.Row([BotonSecundario(texto="Agregar merma", icono=ft.icons.ADD, on_click=self._agregar)]),
                ft.Divider(height=5),
                ft.Text("Mermas registradas:", weight="bold"),
                self.lista_mermas,
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            width=560,
            scroll=ft.ScrollMode.AUTO,
        )

        self.dialogo = Dialogo.personalizado(
            page=self.page,
            titulo="Registrar mermas",
            contenido=contenido,
            acciones=[
                BotonSecundario(
                    texto="Finalizar sin mermas", icono=ft.icons.SKIP_NEXT, on_click=self._finalizar_sin_mermas
                ),
                BotonPrimario(texto="Finalizar orden", icono=ft.icons.SAVE, on_click=self._finalizar),
            ],
            ancho=650,
            modal=True,
        )

    def _toggle_recuperable(self, e):
        """Muestra el campo de nombre solo cuando la merma es recuperable
        -- una merma no_recuperable es solo descarte, no necesita nombre
        propio porque no se va a reutilizar como insumo."""
        self.nombre_recuperado.visible = (self.tipo.value == "recuperable")
        if self.nombre_recuperado.page:
            self.nombre_recuperado.update()

    def _agregar(self, e):
        """Agrega una merma a la lista pendiente de guardar (no cierra el diálogo)."""
        try:
            cantidad = float(self.cantidad.value) if self.cantidad.value else 0
        except ValueError:
            cantidad = 0
        if cantidad <= 0:
            self._mostrar_error("La cantidad debe ser mayor a 0.")
            return

        es_recuperable = self.tipo.value == "recuperable"
        nombre_recuperado = (self.nombre_recuperado.value or "").strip()
        if es_recuperable and not nombre_recuperado:
            self._mostrar_error(
                "Indicá un nombre para el recuperable (ej. trozos de torta, "
                "polvo de galleta)."
            )
            return

        detalle = self._detalles_por_etiqueta.get(self.producto.value)
        self._mermas.append({
            "id_detalle": detalle.get("id_detalle") if detalle else None,
            "id_producto": detalle.get("id_producto") if detalle else None,
            "cantidad": cantidad,
            "unidad": self.unidad.value,
            "tipo_merma": self.tipo.value,
            "motivo": self.motivo.value,
            "nombre_recuperado": nombre_recuperado if es_recuperable else None,
            "descripcion": self.descripcion.value or "",
        })

        self.cantidad.value = "0"
        self.descripcion.value = ""
        self.nombre_recuperado.value = ""
        self._refrescar_lista()

    def _refrescar_lista(self):
        self.lista_mermas.controls.clear()
        for idx, m in enumerate(self._mermas):
            detalle = next((d for d in self.detalles if d.get("id_detalle") == m["id_detalle"]), None)
            nombre = self._etiqueta_detalle(detalle) if detalle else "General"
            texto = f"• {nombre}: {m['cantidad']} {m.get('unidad', '')} ({m['tipo_merma']}, {m['motivo']})"
            if m.get("nombre_recuperado"):
                texto += f" → recuperado como: {m['nombre_recuperado']}"
            self.lista_mermas.controls.append(
                ft.Row(
                    [
                        ft.Text(
                            texto,
                            expand=True,
                            size=12,
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=ft.colors.RED,
                            tooltip="Quitar",
                            on_click=lambda e, i=idx: self._quitar(i),
                        ),
                    ]
                )
            )
        if self.lista_mermas.page:
            self.lista_mermas.update()
        if self.page:
            self.page.update()

    def _quitar(self, idx: int):
        if 0 <= idx < len(self._mermas):
            self._mermas.pop(idx)
            self._refrescar_lista()

    def _finalizar(self, e):
        self.on_guardar(self._mermas)
        self.cerrar()

    def _finalizar_sin_mermas(self, e):
        self.on_guardar([])
        self.cerrar()

    def cerrar(self):
        if self.dialogo:
            self.dialogo.cerrar()
            self.dialogo = None

    def _mostrar_error(self, mensaje: str):
        from ui.components.mensajes import MensajeSistema
        MensajeSistema.error(self.page, mensaje)