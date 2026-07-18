"""
============================================================
Sistema La Dulce Tía

Archivo:
    activo_tarjeta.py

Responsabilidad:
    Tarjeta visual de un activo (recurso) dentro de su catálogo.

    No conoce el service ni el repositorio: solo recibe un
    diccionario con los datos ya resueltos y expone callbacks
    para cada acción disponible. Sigue el mismo patrón que
    TarjetaProducto (ui/components/productos/producto_tarjeta.py).

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography
from ui.core.radius import AppRadius
from ui.core.spacing import AppSpacing
from ui.core.icons import AppIcons


class TarjetaActivo(ft.Container):
    """
    Tarjeta individual del catálogo de activos (recursos).

    `activo` es un dict esperado con, al menos:
        id_activo, nombre, tipo, estado, unidad, costo_unitario,
        modalidad_costo, stock_actual (si aplica)
    """

    ANCHO = 260

    ALTO = 190

    TIPOS_CON_STOCK = {"empaque", "utensilio", "herramienta", "mobiliario"}

    MODALIDADES_MOSTRADAS = {
        "por_unidad": "Por unidad",
        "mensual": "Mensual",
        "por_hora": "Por hora",
        "por_uso": "Por uso",
        "porcentaje": "Porcentaje",
    }

    def __init__(
        self,
        activo: dict,
        on_editar=None,
        on_duplicar=None,
        on_cambiar_estado=None,
        on_eliminar=None,
    ):
        self.tema = ThemeManager.theme

        self.activo = activo

        self.on_editar = on_editar
        self.on_duplicar = on_duplicar
        self.on_cambiar_estado = on_cambiar_estado
        self.on_eliminar = on_eliminar

        super().__init__(
            width=self.ANCHO,
            height=self.ALTO,
            padding=AppSpacing.MD,
            border_radius=AppRadius.CARD,
            bgcolor=self.tema.card,
            border=ft.border.all(1, self.tema.border),
        )

        self.content = self._construir_contenido()

    # --------------------------------------------------

    def _construir_contenido(self):

        activo_bool = self.activo.get("estado", "activo") == "activo"

        encabezado = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(AppIcons.CATEGORY, size=16, color=self.tema.text_secondary),
                        ft.Text(
                            self.activo.get("tipo", ""),
                            size=AppTypography.SMALL,
                            color=self.tema.text_secondary,
                        ),
                    ],
                ),
                ft.PopupMenuButton(
                    icon=ft.icons.MORE_VERT,
                    items=self._crear_menu(activo_bool),
                ),
            ],
        )

        cuerpo = ft.Text(
            self.activo.get("nombre", ""),
            size=AppTypography.CARD_TITLE,
            weight=AppTypography.BOLD,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        costo = ft.Text(
            f"${float(self.activo.get('costo_unitario', 0) or 0):,.2f} / {self.activo.get('unidad', '')}",
            size=AppTypography.BODY,
            weight=AppTypography.SEMIBOLD,
        )

        if self.activo.get("tipo") in self.TIPOS_CON_STOCK:
            detalle = ft.Text(
                f"En stock: {float(self.activo.get('stock_actual', 0) or 0):.0f} {self.activo.get('unidad', '')}",
                size=AppTypography.SMALL,
                color=self.tema.text_secondary,
            )
        else:
            modalidad = self.activo.get("modalidad_costo", "")
            detalle = ft.Text(
                f"Modalidad: {self.MODALIDADES_MOSTRADAS.get(modalidad, modalidad)}",
                size=AppTypography.SMALL,
                color=self.tema.text_secondary,
            )

        pie = ft.Row(
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=AppRadius.CHIP,
                    bgcolor=(self.tema.success + "20") if activo_bool else (self.tema.error + "20"),
                    content=ft.Text(
                        "Activo" if activo_bool else "Inactivo",
                        size=AppTypography.TINY,
                        color=self.tema.success if activo_bool else self.tema.error,
                        weight=AppTypography.BOLD,
                    ),
                ),
            ],
        )

        return ft.Column(
            spacing=8,
            controls=[
                encabezado,
                cuerpo,
                ft.Divider(height=1),
                costo,
                detalle,
                ft.Container(expand=True),
                pie,
            ],
        )

    # --------------------------------------------------

    def _crear_menu(self, activo_bool: bool):

        return [
            ft.PopupMenuItem(
                text="Editar",
                icon=AppIcons.EDIT,
                on_click=lambda e: self._accion(self.on_editar),
            ),
            ft.PopupMenuItem(
                text="Duplicar",
                icon=AppIcons.COPY,
                on_click=lambda e: self._accion(self.on_duplicar),
            ),
            ft.PopupMenuItem(
                text="Desactivar" if activo_bool else "Activar",
                icon=AppIcons.TOGGLE_ON if activo_bool else AppIcons.TOGGLE_OFF,
                on_click=lambda e: self._accion(self.on_cambiar_estado),
            ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                text="Eliminar",
                icon=AppIcons.DELETE,
                on_click=lambda e: self._accion(self.on_eliminar),
            ),
        ]

    # --------------------------------------------------

    def _accion(self, callback):

        if callback:
            callback(self.activo)