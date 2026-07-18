"""
============================================================
Sistema La Dulce Tía

Archivo:
    tabla.py

Responsabilidad:
    Tabla reutilizable para todos los módulos CRUD.

Contiene:
    - ColumnaTabla
    - AccionTabla
    - _TablaBase
    - TablaDatos

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import flet as ft

from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing
from ui.core.radius import AppRadius

@dataclass
class ColumnaTabla:
    """
    Define una columna de la tabla.
    """

    titulo: str

    campo: str | None = None

    width: int = 150

    expand: bool = False

    alineacion: ft.TextAlign = ft.TextAlign.LEFT

    ordenar: bool = True

    visible: bool = True

    formato: Callable | None = None

@dataclass
class AccionTabla:
    """
    Acción disponible en una fila.
    """

    icono: str

    tooltip: str

    callback: Callable

    color: str | None = None


class EstadoFila:
    """
    Estados semánticos que puede tener una fila de la tabla.

    ✅ Los módulos (ej. IngredienteModule) NO deben conocer Flet ni sus
    colores: solo deciden un estado de negocio ("esto está por vencer",
    "esto ya venció"). Es tabla.py quien traduce ese estado al color real
    de Flet. Así se respeta la regla de la arquitectura: los módulos no
    conocen la capa de UI/Flet.
    """

    NORMAL = "normal"
    ALERTA = "alerta"
    VENCIDO = "vencido"
    VENCIDO_CRITICO = "vencido_critico"


# ✅ En Flet 22.1 el módulo de colores se llama 'colors' (minúscula), no
# 'Colors' (eso se introdujo recién en versiones más nuevas, 0.24+).
# Usar ft.Colors acá tira: AttributeError: module 'flet' has no attribute 'Colors'.
_COLORES_POR_ESTADO = {
    EstadoFila.ALERTA: ft.colors.AMBER_50,
    EstadoFila.VENCIDO: ft.colors.ORANGE_100,
    EstadoFila.VENCIDO_CRITICO: ft.colors.RED_100,
}


def _color_para_estado(estado):
    """Traduce un EstadoFila (str semántico) al color real de Flet.
    Si el estado no está mapeado (o es None), no se resalta la fila."""
    return _COLORES_POR_ESTADO.get(estado)

class _TablaBase(ft.Container):
    """
    Clase base utilizada por todas las tablas.
    """

    def __init__(
        self,
        columnas,
        expand=False,
    ):
        super().__init__()
        self.tema = ThemeManager.theme

        self.columnas = columnas

        self.expand = expand

        self.data_table = ft.DataTable(

            expand=True,

            border=ft.border.all(

                1,

                self.tema.border,

            ),

            border_radius=AppRadius.CARD,

            heading_row_color=self.tema.table_header,

            horizontal_margin=12,

            column_spacing=16,

            divider_thickness=1,

            data_row_min_height=44,

            data_row_max_height=44,

        )

        # ✅ Se envuelve la tabla en un contenedor con altura mínima real para que
        # Flet pueda dibujarla correctamente, incluso cuando se carga desde un
        # layout con contenido dinámico.
        self.content = ft.Container(
            content=self.data_table,
            padding=0,
            height=320,
            alignment=ft.alignment.top_left,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        self._crear_columnas()

    def _crear_columnas(self):

        self.data_table.columns.clear()

        for columna in self.columnas:

            self.data_table.columns.append(

                ft.DataColumn(

                    label=ft.Container(

                        width=columna.width,

                        content=ft.Text(

                            columna.titulo,

                            weight=AppTypography.BOLD,

                            text_align=columna.alineacion,

                        ),

                    )

                )

            )

    def _crear_celdas_datos(self, valores):
        """✅ Los valores llegan ya formateados desde el módulo que llama
        (ej. columna.formato ya aplicado en _poblar_tabla). Acá solo nos
        aseguramos de mostrarlos como texto, sin reformatear de nuevo
        (evita, por ejemplo, intentar convertir '$12.34' a float otra vez)."""
        celdas = []
        for columna, valor in zip(self.columnas, valores):
            texto = "" if valor is None else str(valor)
            celdas.append(
                ft.DataCell(ft.Text(texto, text_align=columna.alineacion))
            )
        return celdas

    def agregar_fila(self, valores, item_id=None):
        row = ft.DataRow(cells=self._crear_celdas_datos(valores))
        if item_id is not None:
            row.data = item_id  # Flet permite almacenar datos en .data
        self.data_table.rows.append(row)

    def limpiar(self):

        self.data_table.rows.clear()

    def actualizar(self):

        self.update()

class TablaDatos(_TablaBase):
    """
    Tabla preparada para módulos CRUD.
    """
    def __init__(

        self,

        columnas,

        acciones=None,

        seleccionar=None,

    ):

        super().__init__(columnas)

        self.acciones = acciones or []

        self.on_select = seleccionar

        self._agregar_columna_acciones()

    def _agregar_columna_acciones(self):

        if not self.acciones:

            return

        self.data_table.columns.append(

            ft.DataColumn(

                label=ft.Text(

                    "Acciones",

                    weight=AppTypography.BOLD,

                )

            )

        )

    def agregar_fila(self, valores, item_id=None, estado=None):
        # ✅ Reutiliza el formato de columnas de _TablaBase (antes esta
        # sobreescritura ignoraba columna.formato) y agrega la celda de
        # acciones. 'estado' es un valor semántico (EstadoFila.ALERTA, etc.)
        # que esta clase traduce a un color real de Flet — quien llama
        # (el módulo) no necesita saber qué color de Flet corresponde.
        celdas = self._crear_celdas_datos(valores)

        if self.acciones:
            celdas.append(ft.DataCell(self._crear_celda_acciones(item_id)))

        row = ft.DataRow(
            cells=celdas,
            color=_color_para_estado(estado),
            on_select_changed=self._on_select_changed if self.on_select else None,
        )
        if item_id is not None:
            row.data = item_id  # Flet permite almacenar datos en .data
        self.data_table.rows.append(row)

    def _crear_celda_acciones(self, item_id):
        botones = []
        for accion in self.acciones:
            botones.append(
                ft.IconButton(
                    icon=accion.icono,
                    tooltip=accion.tooltip,
                    icon_color=accion.color,
                    data=item_id,
                    on_click=accion.callback,
                )
            )
        return ft.Row(botones, spacing=4, tight=True)

    def _on_select_changed(self, e):
        if self.on_select:
            self.on_select(e)