"""
============================================================
Sistema La Dulce Tía

Archivo:
    catalogo_productos.py

Responsabilidad:
    Contenedor del catálogo de productos en forma de tarjetas
    (Cards), agrupadas opcionalmente por categoría.

    No conoce el service: recibe la lista de productos ya
    filtrada/ordenada y expone callbacks para cada acción.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.productos.producto_tarjeta import TarjetaProducto
from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography
from ui.core.theme_manager import ThemeManager


class CatalogoProductos(ft.Container):
    """
    Catálogo visual de productos.
    """

    def __init__(

        self,

        on_seleccionar=None,

        on_editar=None,

        on_duplicar=None,

        on_ver_composicion=None,

        on_desactivar=None,

        on_eliminar=None,

        agrupar_por_categoria=True,

    ):

        super().__init__(expand=True)

        self.tema = ThemeManager.theme

        self.on_seleccionar = on_seleccionar

        self.on_editar = on_editar

        self.on_duplicar = on_duplicar

        self.on_ver_composicion = on_ver_composicion

        self.on_desactivar = on_desactivar

        self.on_eliminar = on_eliminar

        self.agrupar_por_categoria = agrupar_por_categoria

        self.productos: list[dict] = []

        self.seleccionados: set = set()

        self.columna = ft.Column(

            spacing=AppSpacing.SECTION_SPACING,

            scroll=ft.ScrollMode.AUTO,

            expand=True,

        )

        self.content = self.columna

    # --------------------------------------------------

    def reemplazar(self, productos: list[dict]):

        self.productos = productos.copy()

        self._render()

    # --------------------------------------------------

    def limpiar_seleccion(self):

        self.seleccionados.clear()

        self._render()

    # --------------------------------------------------

    def obtener_seleccionados(self):

        return [

            p for p in self.productos
            if p.get("id_producto") in self.seleccionados

        ]

    # --------------------------------------------------

    def _render(self):

        self.columna.controls.clear()

        if not self.productos:

            self.columna.controls.append(self._estado_vacio())

        elif self.agrupar_por_categoria:

            for categoria, items in self._agrupar(self.productos).items():

                self.columna.controls.append(

                    ft.Text(

                        categoria,

                        size=AppTypography.SECTION_TITLE,

                        weight=AppTypography.BOLD,

                    )

                )

                self.columna.controls.append(self._fila_tarjetas(items))

        else:

            self.columna.controls.append(self._fila_tarjetas(self.productos))

        if self.page:
            self.update()

    # --------------------------------------------------

    def _agrupar(self, productos):

        grupos: dict[str, list] = {}

        for p in productos:

            categoria = p.get("categoria") or "Sin categoría"

            grupos.setdefault(categoria, []).append(p)

        # ✅ Sin esto, el orden de las secciones dependía del orden
        # en que aparecían los productos (nombre/precio/costo), y
        # las categorías "saltaban" de lugar al cambiar el filtro.
        return dict(sorted(grupos.items()))

    # --------------------------------------------------

    def _fila_tarjetas(self, productos):

        return ft.Row(

            wrap=True,

            spacing=AppSpacing.MD,

            run_spacing=AppSpacing.MD,

            controls=[

                TarjetaProducto(

                    producto=p,

                    seleccionado=p.get("id_producto") in self.seleccionados,

                    on_click=lambda e, p = p: self._click_tarjeta(p),

                    on_editar=self.on_editar,

                    on_duplicar=self.on_duplicar,

                    on_ver_composicion=self.on_ver_composicion,

                    on_desactivar=self.on_desactivar,

                    on_eliminar=self.on_eliminar,

                )
                for p in productos

            ],

        )

    # --------------------------------------------------

    def _click_tarjeta(self, producto):

        id_producto = producto.get("id_producto")

        if id_producto in self.seleccionados:

            self.seleccionados.discard(id_producto)

        else:

            self.seleccionados.add(id_producto)

        self._render()

        if self.on_seleccionar:

            self.on_seleccionar(self.obtener_seleccionados())

    # --------------------------------------------------

    def _estado_vacio(self):

        return ft.Container(

            expand=True,

            alignment=ft.alignment.center,

            padding=AppSpacing.XXL,

            content=ft.Column(

                horizontal_alignment=ft.CrossAxisAlignment.CENTER,

                controls=[

                    ft.Icon(

                        ft.icons.INVENTORY_2_OUTLINED,

                        size=48,

                        color=self.tema.text_secondary,

                    ),

                    ft.Text(

                        "Todavía no hay productos registrados.",

                        color=self.tema.text_secondary,

                    ),

                ],

            ),

        )