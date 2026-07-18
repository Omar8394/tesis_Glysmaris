"""
============================================================
Sistema La Dulce Tía

Archivo:
    validacion_view.py

Responsabilidad:
    Panel que muestra el resultado del análisis de disponibilidad
    de una orden. Se utiliza en el Paso 2 del wizard.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing


class ValidacionView(ft.Container):
    """
    Muestra el análisis de disponibilidad para los productos de una orden.
    """

    def __init__(self, analisis: list[dict], faltantes_por_producto: dict = None):
        super().__init__()
        self.tema = ThemeManager.theme
        self.padding = AppSpacing.MD
        self.border = ft.border.all(1, self.tema.border)
        self.border_radius = 8

        self.analisis = analisis
        self.faltantes_por_producto = faltantes_por_producto or {}

        self.content = self._construir_contenido()

    def _construir_contenido(self) -> ft.Column:
        """Construye el contenido del panel."""
        controles = [
            ft.Text("Validación de Inventario", size=AppTypography.SECTION_TITLE, weight="bold"),
        ]

        if not self.analisis:
            controles.append(
                ft.Text("No hay productos para analizar.", color=ft.colors.GREY)
            )
            return ft.Column(controles, spacing=AppSpacing.CONTROL_SPACING)

        for item in self.analisis:
            # Datos del análisis
            id_producto = item.get("id_producto")
            cantidad_solicitada = item.get("cantidad_solicitada", 0)
            cantidad_posible = item.get("cantidad_posible", 0)
            resultado = item.get("resultado", "inviable")

            # Nombre del producto (idealmente vendría del service)
            nombre_producto = item.get("nombre_producto", f"Producto #{id_producto}")

            # Color según resultado
            color_resultado = {
                "completo": ft.colors.GREEN,
                "parcial": ft.colors.ORANGE,
                "inviable": ft.colors.RED,
            }.get(resultado, ft.colors.GREY)

            # Texto resultado
            texto_resultado = {
                "completo": "✔ Puede fabricarse completamente",
                "parcial": f"⚠ Solo pueden fabricarse {cantidad_posible}",
                "inviable": "✖ No puede fabricarse",
            }.get(resultado, "")

            # Crear tarjeta para el producto
            tarjeta = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(nombre_producto, size=AppTypography.BODY, weight="bold"),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        f"Solicitado: {cantidad_solicitada}",
                                        size=AppTypography.SMALL,
                                    ),
                                    ft.Text(
                                        f"Máximo: {cantidad_posible}",
                                        size=AppTypography.SMALL,
                                    ),
                                ],
                                spacing=AppSpacing.CONTROL_SPACING,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.CIRCLE,
                                        size=10,
                                        color=color_resultado,
                                    ),
                                    ft.Text(texto_resultado, size=AppTypography.BODY),
                                ],
                                spacing=4,
                            ),
                            # Sección de faltantes
                            self._crear_faltantes(id_producto),
                        ],
                        spacing=AppSpacing.SM,
                    ),
                    padding=AppSpacing.MD,
                ),
                elevation=1,
            )

            controles.append(tarjeta)

        return ft.Column(controles, spacing=AppSpacing.CONTROL_SPACING)

    def _crear_faltantes(self, id_producto: int) -> ft.Container:
        """Crea la lista de faltantes para un producto (si los hay)."""
        faltantes = self.faltantes_por_producto.get(id_producto, [])
        if not faltantes:
            return ft.Container()

        # Tabla de faltantes
        filas = []
        for falta in faltantes:
            tipo = "Ingrediente" if "id_ingrediente" in falta else "Activo"
            nombre = falta.get("nombre", "Desconocido")
            necesario = falta.get("necesario", 0)
            disponible = falta.get("disponible", 0)
            faltante = falta.get("faltante", 0)

            filas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(tipo, size=AppTypography.SMALL)),
                        ft.DataCell(ft.Text(nombre, size=AppTypography.SMALL)),
                        ft.DataCell(ft.Text(f"{necesario:.2f}", size=AppTypography.SMALL)),
                        ft.DataCell(ft.Text(f"{disponible:.2f}", size=AppTypography.SMALL)),
                        ft.DataCell(
                            ft.Text(
                                f"{faltante:.2f}",
                                size=AppTypography.SMALL,
                                color=ft.colors.RED,
                                weight="bold",
                            )
                        ),
                    ]
                )
            )

        tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Tipo", size=AppTypography.SMALL, weight="bold")),
                ft.DataColumn(ft.Text("Recurso", size=AppTypography.SMALL, weight="bold")),
                ft.DataColumn(ft.Text("Necesario", size=AppTypography.SMALL, weight="bold")),
                ft.DataColumn(ft.Text("Disponible", size=AppTypography.SMALL, weight="bold")),
                ft.DataColumn(
                    ft.Text("Faltante", size=AppTypography.SMALL, weight="bold", color=ft.colors.RED)
                ),
            ],
            rows=filas,
            column_spacing=20,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Faltantes:", size=AppTypography.BODY, weight="bold"),
                    tabla,
                ],
                spacing=AppSpacing.SM,
            ),
            padding=ft.padding.only(top=8),
        )