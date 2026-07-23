"""
============================================================
Sistema La Dulce Tía

Archivo:
    estadisticas_view.py

Responsabilidad:
    Interfaz del módulo de Estadísticas y Analítica de Negocio.

    Sólo se encarga de presentación: pide datos al
    EstadisticasService (vía ServiceFactory) e interpreta el
    ServiceResult devuelto. No contiene SQL ni reglas de negocio.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.services.factory import ServiceFactory


class EstadisticasView(ft.Column):
    def __init__(self):
        super().__init__(expand=True, spacing=15)

        self._service = ServiceFactory.get_estadisticas_service()

        self.header = ft.Row(
            [
                ft.Icon(ft.icons.BAR_CHART_ROUNDED, size=28, color=ft.colors.PRIMARY),
                ft.Text(
                    "Módulo de Analítica & Estadísticas",
                    size=22,
                    weight="bold",
                ),
            ]
        )

        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="📊 Ventas & Rendimiento",
                    content=self._crear_pestana_rendimiento(),
                ),
                ft.Tab(
                    text="⏳ Inteligencia de Temporadas",
                    content=self._crear_pestana_temporadas(),
                ),
                ft.Tab(
                    text="📉 Mermas & Rentabilidad",
                    content=self._crear_pestana_mermas(),
                ),
            ],
            expand=True,
        )

        self.controls = [self.header, self.tabs]

    # -------------------------------------------------------------
    # Pestaña 1: Rendimiento
    # -------------------------------------------------------------
    def _crear_pestana_rendimiento(self):
        resultado = self._service.obtener_rendimiento_productos(dias=30)

        lista_barras = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        if not resultado.exito:
            lista_barras.controls.append(
                ft.Text(resultado.mensaje, color="red-600"),
            )
        elif not resultado.datos:
            lista_barras.controls.append(
                ft.Text(resultado.mensaje or "No hay registros de ventas suficientes."),
            )
        else:
            datos = resultado.datos
            max_ventas = max(d["total_unidades"] for d in datos) or 1

            for p in datos:
                porcentaje = p["total_unidades"] / max_ventas

                fila_barra = ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(p["nombre_producto"], weight="w500", expand=True),
                                ft.Text(
                                    f"{p['total_unidades']} un. (${p['total_generado']:.2f})",
                                    weight="bold",
                                ),
                            ]
                        ),
                        ft.ProgressBar(
                            value=porcentaje,
                            color=ft.colors.PRIMARY,
                            bgcolor="grey-200",
                            height=8,
                        ),
                    ],
                    spacing=3,
                )

                lista_barras.controls.append(fila_barra)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Top de Productos Vendidos (Últimos 30 días)",
                        weight="bold",
                        size=16,
                    ),
                    ft.Divider(),
                    lista_barras,
                ]
            ),
            padding=15,
        )

    # -------------------------------------------------------------
    # Pestaña 2: Temporadas
    # -------------------------------------------------------------
    def _crear_pestana_temporadas(self):
        resultado = self._service.obtener_recomendaciones_temporada()

        col_alta = ft.Column(spacing=10)
        col_baja = ft.Column(spacing=10)

        if not resultado.exito:
            col_alta.controls.append(ft.Text(resultado.mensaje, color="red-600"))
        else:
            recs = resultado.datos

            for item in recs["alta"]:
                col_alta.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"🔥 {item['nombre']}",
                                    weight="bold",
                                    color="green-900",
                                ),
                                ft.Text(item["razon"], size=12, color="green-800"),
                            ]
                        ),
                        bgcolor="green-50",
                        border=ft.border.all(1, "green-300"),
                        padding=10,
                        border_radius=8,
                    )
                )

            for item in recs["baja"]:
                col_baja.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"❄️ {item['nombre']}",
                                    weight="bold",
                                    color="red-900",
                                ),
                                ft.Text(item["razon"], size=12, color="red-800"),
                            ]
                        ),
                        bgcolor="red-50",
                        border=ft.border.all(1, "red-300"),
                        padding=10,
                        border_radius=8,
                    )
                )

            if not recs["alta"]:
                col_alta.controls.append(ft.Text("Sin productos en alta demanda por ahora."))
            if not recs["baja"]:
                col_baja.controls.append(ft.Text("Sin productos en baja demanda por ahora."))

        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Aumentar Producción / Stock",
                                weight="bold",
                                color="green-700",
                            ),
                            col_alta,
                        ],
                        expand=True,
                    ),
                    ft.VerticalDivider(),
                    ft.Column(
                        [
                            ft.Text(
                                "Congelar / Producir Bajo Pedido",
                                weight="bold",
                                color="red-700",
                            ),
                            col_baja,
                        ],
                        expand=True,
                    ),
                ],
                spacing=15,
            ),
            padding=15,
        )

    # -------------------------------------------------------------
    # Pestaña 3: Mermas
    # -------------------------------------------------------------
    def _crear_pestana_mermas(self):
        resultado = self._service.obtener_reporte_mermas(limite=10)

        tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Producto / Insumo")),
                ft.DataColumn(ft.Text("Motivo")),
                ft.DataColumn(ft.Text("Cantidad")),
                ft.DataColumn(ft.Text("Costo Pérdida ($)")),
            ],
            rows=[],
        )

        contenido_extra = None

        if not resultado.exito:
            contenido_extra = ft.Text(resultado.mensaje, color="red-600")
        elif not resultado.datos:
            contenido_extra = ft.Text(resultado.mensaje or "No hay mermas registradas.")
        else:
            for m in resultado.datos:
                tabla.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(m["item"])),
                            ft.DataCell(ft.Text(m["motivo"])),
                            ft.DataCell(ft.Text(str(m["cantidad_perdida"]))),
                            ft.DataCell(
                                ft.Text(
                                    f"${m['costo_total_perdida']:.2f}",
                                    color="red-600",
                                    weight="bold",
                                )
                            ),
                        ]
                    )
                )

        cuerpo = [
            ft.Text(
                "Reporte de Desperdicios y Mermas Críticas",
                weight="bold",
                size=16,
            ),
            ft.Divider(),
        ]

        if contenido_extra is not None:
            cuerpo.append(contenido_extra)
        else:
            cuerpo.append(ft.ListView(controls=[tabla], expand=True))

        return ft.Container(
            content=ft.Column(cuerpo),
            padding=15,
        )
