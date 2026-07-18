"""
============================================================
Sistema La Dulce Tía

Tabla reutilizable de ingredientes de una receta.
============================================================
"""

from __future__ import annotations

import flet as ft


class IngredientesTable(ft.Container):

    def __init__(self):

        super().__init__(expand=True)

        self.ingredientes: list[dict] = []

        self.on_delete = None

        self.tabla = ft.DataTable(
            expand=True,
            column_spacing=20,
            heading_row_height=40,
            data_row_min_height=40,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            columns=[
                ft.DataColumn(ft.Text("Ingrediente")),
                ft.DataColumn(ft.Text("Cantidad")),
                ft.DataColumn(ft.Text("Unidad")),
                ft.DataColumn(ft.Text("Acción")),
            ],
            rows=[],
        )

        self.content = ft.Container(
            height=260,
            border_radius=10,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            padding=10,
            content=self.tabla,
        )

    # --------------------------------------------------

    def agregar(self, ingrediente: dict):

        self.ingredientes.append(ingrediente)

        self.actualizar()

    # --------------------------------------------------

    def reemplazar(self, ingredientes: list[dict]):

        self.ingredientes = ingredientes.copy()

        self.actualizar()

    # --------------------------------------------------

    def eliminar(self, indice: int):

        if 0 <= indice < len(self.ingredientes):

            self.ingredientes.pop(indice)

            self.actualizar()

    # --------------------------------------------------

    def limpiar(self):

        self.ingredientes.clear()

        self.actualizar()

    # --------------------------------------------------

    def obtener(self):

        return self.ingredientes

    # --------------------------------------------------

    def actualizar(self):

        self.tabla.rows.clear()

        for indice, ingrediente in enumerate(self.ingredientes):

            boton = ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE,
                icon_color=ft.colors.RED,
                tooltip="Eliminar ingrediente",
                on_click=lambda e, i=indice: self._eliminar(i),
            )

            self.tabla.rows.append(

                ft.DataRow(

                    cells=[

                        ft.DataCell(
                            ft.Text(
                                ingrediente["nombre"]
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                str(ingrediente["cantidad"])
                            )
                        ),

                        ft.DataCell(
                            ft.Text(
                                ingrediente["unidad"]
                            )
                        ),

                        ft.DataCell(
                            boton
                        ),
                    ]
                )

            )

        self.update()

    # --------------------------------------------------

    def _eliminar(self, indice):

        if self.on_delete:

            self.on_delete(indice)

        else:

            self.eliminar(indice)