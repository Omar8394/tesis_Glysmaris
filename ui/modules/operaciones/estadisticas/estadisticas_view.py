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

# Paleta cíclica para los charts (barras y torta)
_PALETA = [
    "#7C5CFC", "#FF8A65", "#4FC3F7", "#81C784",
    "#FFD54F", "#F06292", "#A1887F", "#4DB6AC",
]


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

        cuerpo = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        if not resultado.exito:
            cuerpo.controls.append(ft.Text(resultado.mensaje, color="red600"))
        elif not resultado.datos:
            cuerpo.controls.append(
                ft.Text(resultado.mensaje or "No hay registros de ventas suficientes.")
            )
        else:
            datos = resultado.datos
            top_chart = datos[:8]  # el chart de barras se satura con muchos productos

            cuerpo.controls.append(self._crear_bar_chart_rendimiento(top_chart))
            cuerpo.controls.append(ft.Divider())
            cuerpo.controls.append(self._crear_lista_rendimiento(datos))

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Top de Productos Vendidos (Últimos 30 días)",
                        weight="bold",
                        size=16,
                    ),
                    ft.Divider(),
                    cuerpo,
                ],
                expand=True,
            ),
            padding=15,
        )

    def _crear_bar_chart_rendimiento(self, datos):
        max_unidades = float(max(d["total_unidades"] for d in datos) or 1)

        grupos = []
        etiquetas = []

        for i, p in enumerate(datos):
            color = _PALETA[i % len(_PALETA)]
            unidades = float(p["total_unidades"])

            grupos.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=unidades,
                            width=28,
                            color=color,
                            tooltip=f"{p['nombre_producto']}\n{p['total_unidades']} un.",
                            border_radius=4,
                        )
                    ],
                )
            )

            nombre_corto = (
                p["nombre_producto"][:10] + "…"
                if len(p["nombre_producto"]) > 10
                else p["nombre_producto"]
            )
            etiquetas.append(
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(nombre_corto, size=10, no_wrap=True),
                )
            )

        return ft.Container(
            content=ft.BarChart(
                bar_groups=grupos,
                border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                left_axis=ft.ChartAxis(labels_size=40),
                bottom_axis=ft.ChartAxis(labels=etiquetas, labels_size=36),
                horizontal_grid_lines=ft.ChartGridLines(
                    color=ft.colors.OUTLINE_VARIANT, width=1, dash_pattern=[3, 3]
                ),
                tooltip_bgcolor=ft.colors.with_opacity(0.85, ft.colors.SURFACE_VARIANT),
                max_y=max_unidades * 1.15,
                interactive=True,
                expand=True,
            ),
            height=260,
        )

    def _crear_lista_rendimiento(self, datos):
        lista_barras = ft.Column(spacing=10)
        max_ventas = float(max(d["total_unidades"] for d in datos) or 1)

        for p in datos:
            porcentaje = float(p["total_unidades"]) / max_ventas

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
                        bgcolor="grey200",
                        height=8,
                    ),
                ],
                spacing=3,
            )

            lista_barras.controls.append(fila_barra)

        return lista_barras

    # -------------------------------------------------------------
    # Pestaña 2: Temporadas
    # -------------------------------------------------------------
    def _crear_pestana_temporadas(self):
        resultado = self._service.obtener_recomendaciones_temporada()

        col_alta = ft.Column(spacing=10)
        col_baja = ft.Column(spacing=10)

        if not resultado.exito:
            col_alta.controls.append(ft.Text(resultado.mensaje, color="red600"))
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
                                    color="green900",
                                ),
                                ft.Text(item["razon"], size=12, color="green800"),
                            ]
                        ),
                        bgcolor="green50",
                        border=ft.border.all(1, "green300"),
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
                                    color="red900",
                                ),
                                ft.Text(item["razon"], size=12, color="red800"),
                            ]
                        ),
                        bgcolor="red50",
                        border=ft.border.all(1, "red300"),
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
                                color="green700",
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
                                color="red700",
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

        cuerpo = [
            ft.Text(
                "Reporte de Desperdicios y Mermas Críticas",
                weight="bold",
                size=16,
            ),
            ft.Divider(),
        ]

        if not resultado.exito:
            cuerpo.append(ft.Text(resultado.mensaje, color="red600"))
        elif not resultado.datos:
            cuerpo.append(ft.Text(resultado.mensaje or "No hay mermas registradas."))
        else:
            cuerpo.append(self._crear_pie_chart_mermas(resultado.datos))
            cuerpo.append(ft.Divider())
            cuerpo.append(self._crear_tabla_mermas(resultado.datos))

        return ft.Container(
            content=ft.Column(cuerpo, expand=True),
            padding=15,
        )

    def _crear_pie_chart_mermas(self, datos):
        total_costo = sum(float(m["costo_total_perdida"] or 0) for m in datos)
        divisor_porcentaje = total_costo or 1

        secciones = []
        leyenda = ft.Column(spacing=6)

        for i, m in enumerate(datos):
            color = _PALETA[i % len(_PALETA)]
            costo = float(m["costo_total_perdida"] or 0)
            porcentaje = costo / divisor_porcentaje * 100

            secciones.append(
                ft.PieChartSection(
                    value=costo,
                    title=f"{porcentaje:.0f}%" if porcentaje >= 6 else "",
                    title_style=ft.TextStyle(
                        size=11, color=ft.colors.WHITE, weight="bold"
                    ),
                    color=color,
                    radius=90,
                )
            )
            leyenda.controls.append(
                ft.Row(
                    [
                        ft.Container(width=12, height=12, bgcolor=color, border_radius=3),
                        ft.Text(f"{m['item']} · {m['motivo']}", size=12, expand=True),
                        ft.Text(f"${costo:.2f}", size=12, weight="bold"),
                    ],
                    spacing=8,
                )
            )

        return ft.Row(
            [
                ft.Container(
                    content=ft.PieChart(
                        sections=secciones,
                        sections_space=2,
                        center_space_radius=35,
                        expand=True,
                    ),
                    height=220,
                    width=220,
                ),
                ft.VerticalDivider(),
                ft.Column(
                    [
                        ft.Text(
                            f"Costo total en pérdidas: ${total_costo:.2f}",
                            weight="bold",
                        ),
                        leyenda,
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
            spacing=15,
        )

    def _crear_tabla_mermas(self, datos):
        tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Producto / Insumo")),
                ft.DataColumn(ft.Text("Motivo")),
                ft.DataColumn(ft.Text("Cantidad")),
                ft.DataColumn(ft.Text("Costo Pérdida ($)")),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(m["item"])),
                        ft.DataCell(ft.Text(m["motivo"])),
                        ft.DataCell(ft.Text(str(m["cantidad_perdida"]))),
                        ft.DataCell(
                            ft.Text(
                                f"${m['costo_total_perdida']:.2f}",
                                color="red600",
                                weight="bold",
                            )
                        ),
                    ]
                )
                for m in datos
            ],
        )

        return ft.ListView(controls=[tabla], expand=True)