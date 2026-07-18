"""
============================================================
Sistema La Dulce Tía

Archivo:
    producto_tarjeta.py

Responsabilidad:
    Tarjeta visual de un producto dentro del catálogo.

    No conoce el service ni el repositorio: solo recibe un
    diccionario con los datos ya resueltos y expone callbacks
    para cada acción disponible.

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


class TarjetaProducto(ft.Container):
    """
    Tarjeta individual del catálogo de productos.

    `producto` es un dict esperado con, al menos:
        nombre, categoria, precio_final, costo_total,
        presentaciones (list[str] opcional), activo (bool),
        icono (opcional, un ft.icons.*)
    """

    ANCHO = 240

    ALTO = 270

    def __init__(

        self,

        producto: dict,

        seleccionado: bool = False,

        on_click=None, 

        on_editar=None,

        on_duplicar=None,

        on_ver_composicion=None,

        on_desactivar=None,

        on_eliminar=None,

    ):

        self.tema = ThemeManager.theme

        self.producto = producto

        self.seleccionado = seleccionado

        #self.on_click = on_click

        self.on_editar = on_editar

        self.on_duplicar = on_duplicar

        self.on_ver_composicion = on_ver_composicion

        self.on_desactivar = on_desactivar

        self.on_eliminar = on_eliminar

        super().__init__(

            width=self.ANCHO,

            height=self.ALTO,

            padding=AppSpacing.MD,

            border_radius=AppRadius.CARD,

            bgcolor=self.tema.card,

            border=ft.border.all(

                2 if seleccionado else 1,

                self.tema.primary if seleccionado else self.tema.border,

            ),

            ink=True,

            on_click=on_click, 

        )

        self.content = self._construir_contenido()

    # --------------------------------------------------

    def _construir_contenido(self):

        activo = self.producto.get("activo", True)

        presentaciones = self.producto.get("presentaciones") or []

        encabezado = ft.Row(

            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,

            controls=[

                ft.Container(

                    width=44,

                    height=44,

                    border_radius=AppRadius.MD,

                    bgcolor=self.tema.primary + "15",

                    alignment=ft.alignment.center,

                    content=ft.Icon(

                        self.producto.get("icono") or AppIcons.PRODUCT,

                        color=self.tema.primary,

                    ),

                ),

                ft.Row(

                    spacing=0,

                    controls=[

                        ft.Icon(

                            ft.icons.CHECK,

                            color=self.tema.primary,

                            size=20,

                            visible=self.seleccionado,

                        ),

                        ft.PopupMenuButton(

                            icon=ft.icons.MORE_VERT,

                            items=self._crear_menu(),

                        ),

                    ],

                ),

            ],

        )

        cuerpo = ft.Column(

            spacing=2,

            controls=[

                ft.Text(

                    self.producto.get("nombre", ""),

                    size=AppTypography.CARD_TITLE,

                    weight=AppTypography.BOLD,

                    max_lines=1,

                    overflow=ft.TextOverflow.ELLIPSIS,

                ),

                ft.Text(

                    self.producto.get("categoria") or "Sin categoría",

                    size=AppTypography.SMALL,

                    color=self.tema.text_secondary,

                ),

            ],

        )

        precios = ft.Row(

            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,

            controls=[

                ft.Column(

                    spacing=0,

                    controls=[

                        ft.Text("Costo", size=AppTypography.TINY, color=self.tema.text_secondary),

                        ft.Text(

                            f"${float(self.producto.get('costo_total', 0) or 0):,.2f}",

                            size=AppTypography.BODY,

                            weight=AppTypography.SEMIBOLD,

                        ),

                    ],

                ),

                ft.Column(

                    spacing=0,

                    horizontal_alignment=ft.CrossAxisAlignment.END,

                    controls=[

                        ft.Text("Precio", size=AppTypography.TINY, color=self.tema.text_secondary),

                        ft.Text(

                            f"${float(self.producto.get('precio_final', 0) or 0):,.2f}",

                            size=AppTypography.SUBTITLE,

                            weight=AppTypography.BOLD,

                            color=self.tema.success,

                        ),

                    ],

                ),

            ],

        )

        chips_presentaciones = ft.Row(

            wrap=True,

            spacing=4,

            controls=[

                ft.Container(

                    padding=ft.padding.symmetric(horizontal=8, vertical=2),

                    bgcolor=self.tema.surface,

                    border_radius=AppRadius.CHIP,

                    content=ft.Text(p, size=AppTypography.TINY),

                )
                for p in presentaciones[:3]

            ],

        )

        pie = ft.Row(

            controls=[

                ft.Container(

                    padding=ft.padding.symmetric(horizontal=8, vertical=2),

                    border_radius=AppRadius.CHIP,

                    bgcolor=(self.tema.success + "20") if activo else (self.tema.error + "20"),

                    content=ft.Text(

                        "Activo" if activo else "Inactivo",

                        size=AppTypography.TINY,

                        color=self.tema.success if activo else self.tema.error,

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

                precios,

                chips_presentaciones,

                ft.Container(expand=True),

                pie,

            ],

        )

    # --------------------------------------------------

    def _crear_menu(self):

        return [

            ft.PopupMenuItem(

                text="Editar",

                icon=ft.icons.EDIT_OUTLINED,

                on_click=lambda e: self._accion(self.on_editar),

            ),

            ft.PopupMenuItem(

                text="Duplicar",

                icon=ft.icons.COPY_ALL_OUTLINED,

                on_click=lambda e: self._accion(self.on_duplicar),

            ),

            ft.PopupMenuItem(

                text="Ver composición",

                icon=ft.icons.ACCOUNT_TREE_OUTLINED,

                on_click=lambda e: self._accion(self.on_ver_composicion),

            ),

            ft.PopupMenuItem(),

            ft.PopupMenuItem(

                text="Desactivar" if activo_o_true(self.producto) else "Activar",

                icon=ft.icons.VISIBILITY_OFF_OUTLINED,

                on_click=lambda e: self._accion(self.on_desactivar),

            ),

            ft.PopupMenuItem(

                text="Eliminar",

                icon=ft.icons.DELETE_OUTLINE,

                on_click=lambda e: self._accion(self.on_eliminar),

            ),

        ]

    # --------------------------------------------------

    def _accion(self, callback):

        if callback:

            callback(self.producto)

    # --------------------------------------------------

    def _click(self, e):

        if self.on_click:

            self.on_click(self.producto)


def activo_o_true(producto: dict) -> bool:
    """Pequeño helper para no repetir `producto.get("activo", True)`."""

    return producto.get("activo", True)
