"""
============================================================
Sistema La Dulce Tía

Archivo:
    tabla_seleccion.py

Responsabilidad:
    Tabla reutilizable para listas de "elementos agregados"
    dentro de asistentes (empaques, costos indirectos,
    componentes, productos de un combo, presentaciones, etc.).

    No conoce el origen de los datos: solo recibe diccionarios
    ya armados y los muestra con una acción de eliminar.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft


class TablaSeleccion(ft.Container):
    """
    Tabla genérica de elementos seleccionados.

    `columnas` es una lista de tuplas (clave, titulo). Cada
    elemento agregado es un dict que debe tener, como mínimo,
    esas claves.
    """

    def __init__(

        self,

        columnas=None,

        on_eliminar=None,

        altura=220,

    ):

        super().__init__(expand=True)

        self.columnas = columnas or [

            ("nombre", "Nombre"),

            ("cantidad", "Cantidad"),

        ]

        self.on_eliminar = on_eliminar

        self.elementos: list[dict] = []

        self.tabla = ft.DataTable(

            expand=True,

            column_spacing=20,

            heading_row_height=40,

            data_row_min_height=40,

            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),

            columns=[

                ft.DataColumn(ft.Text(titulo))
                for _, titulo in self.columnas

            ] + [

                ft.DataColumn(ft.Text("")),

            ],

            rows=[],

        )

        self.content = ft.Container(

            height=altura,

            border_radius=10,

            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),

            padding=10,

            content=ft.Column(

                [self.tabla],

                scroll=ft.ScrollMode.AUTO,

            ),

        )

    # --------------------------------------------------

    def agregar(self, elemento: dict):

        self.elementos.append(elemento)

        self._render()

    # --------------------------------------------------

    def reemplazar(self, elementos: list[dict]):

        self.elementos = elementos.copy()

        self._render()

    # --------------------------------------------------

    def eliminar(self, indice: int):

        if 0 <= indice < len(self.elementos):

            self.elementos.pop(indice)

            self._render()

    # --------------------------------------------------

    def limpiar(self):

        self.elementos.clear()

        self._render()

    # --------------------------------------------------

    def obtener(self):

        return self.elementos

    # --------------------------------------------------

    def _render(self):

        self.tabla.rows.clear()

        for indice, elemento in enumerate(self.elementos):

            celdas = [

                ft.DataCell(ft.Text(str(elemento.get(clave, ""))))
                for clave, _ in self.columnas

            ]

            boton = ft.IconButton(

                icon=ft.icons.DELETE_OUTLINE,

                icon_color=ft.colors.RED,

                tooltip="Quitar",

                on_click=lambda e, i=indice: self._eliminar_click(i),

            )

            celdas.append(ft.DataCell(boton))

            self.tabla.rows.append(ft.DataRow(cells=celdas))

        if self.page:
            self.update()

    # --------------------------------------------------

    def _eliminar_click(self, indice):

        if self.on_eliminar:

            self.on_eliminar(indice)

        else:

            self.eliminar(indice)
