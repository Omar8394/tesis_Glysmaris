"""
============================================================
Sistema La Dulce Tía

Archivo:
    panel_estados.py

Responsabilidad:
    Panel que muestra las órdenes agrupadas por estado en columnas.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography
from .orden_card import OrdenCard


class PanelEstados(ft.Row):
    """Panel con columnas de órdenes agrupadas por estado."""

    def __init__(
        self,
        ordenes: list[dict],
        on_iniciar: callable = None,
        on_continuar: callable = None,
        on_finalizar: callable = None,
        on_ver_detalle: callable = None,
        on_cancelar: callable = None,
    ):
        super().__init__(expand=True, spacing=AppSpacing.CONTROL_SPACING)

        self.ordenes = ordenes
        self.on_iniciar = on_iniciar
        self.on_continuar = on_continuar
        self.on_finalizar = on_finalizar
        self.on_ver_detalle = on_ver_detalle
        self.on_cancelar = on_cancelar

        # Agrupar por estado
        self.agrupadas = {
            "pendiente": [],
            "en_proceso": [],
            "finalizada": [],
            "cancelada": [],
        }
        for o in ordenes:
            estado = o.get("estado", "pendiente")
            if estado in self.agrupadas:
                self.agrupadas[estado].append(o)

        # Construir columnas
        self.controls = [
            self._crear_columna("pendiente", "⏳ Pendientes", ft.colors.AMBER),
            self._crear_columna("en_proceso", "🔄 En proceso", ft.colors.BLUE),
            self._crear_columna("finalizada", "✅ Finalizadas", ft.colors.GREEN),
        ]

    def _crear_columna(self, estado: str, titulo: str, color: str) -> ft.Container:
        """Crea una columna con las órdenes de un estado."""
        ordenes_estado = self.agrupadas.get(estado, [])

        columna = ft.Column(
            [
                ft.Text(titulo, weight="bold", size=AppTypography.SECTION_TITLE),
                ft.Divider(color=color, height=2),
                *[
                    OrdenCard(
                        orden=o,
                        on_iniciar=self.on_iniciar if estado == "pendiente" else None,
                        on_continuar=self.on_continuar if estado == "en_proceso" else None,
                        on_finalizar=self.on_finalizar if estado == "en_proceso" else None,
                        on_ver_detalle=self.on_ver_detalle,
                        on_cancelar=self.on_cancelar if estado == "pendiente" else None,
                    )
                    for o in ordenes_estado
                ],
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Si no hay órdenes, mostrar mensaje
        if not ordenes_estado:
            columna.controls.append(
                ft.Text(
                    f"No hay órdenes {estado.replace('_', ' ')}",
                    color=ft.colors.GREY,
                    size=AppTypography.SMALL,
                )
            )

        return ft.Container(
            content=columna,
            expand=True,
            padding=AppSpacing.MD,
            bgcolor=ft.colors.with_opacity(0.05, ft.colors.BLACK),
            border_radius=10,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, ft.colors.BLACK)),
        )