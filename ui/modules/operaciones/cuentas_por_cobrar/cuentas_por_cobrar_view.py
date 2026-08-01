"""
============================================================
Sistema La Dulce Tía

Archivo:
    cuentas_por_cobrar_view.py

Responsabilidad:
    Vista (solo UI) del módulo de Cuentas por Cobrar y Clientes.
    No conoce servicios ni base de datos: solo dibuja lo que le
    pasan y avisa mediante callbacks cuando el usuario interactúa.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from datetime import datetime, date

import flet as ft

from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager
from ui.components.tabla import TablaDatos, ColumnaTabla, AccionTabla
from ui.components.paginador import Paginador
from ui.components.tarjetas import TarjetaResumen, TarjetaAdvertencia
from ui.components.campo_texto import CampoTexto


# Métodos válidos para abonar una deuda. No incluye "crédito": no tiene
# sentido pagar una deuda a crédito con más crédito.
METODOS_ABONO = [
    ("efectivo", "Efectivo"),
    ("debito", "Débito"),
    ("transferencia", "Transferencia"),
    ("pago_movil", "Pago móvil"),
]


def _formatear_moneda(valor):
    try:
        return f"${float(valor or 0):.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _formatear_fecha(valor):
    if not valor:
        return "—"
    if isinstance(valor, (datetime, date)):
        return valor.strftime("%d/%m/%Y")
    texto = str(valor)
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return texto


COLUMNAS_CUENTAS = [
    ColumnaTabla("Cliente", campo="cliente_nombre", width=150),
    ColumnaTabla("Teléfono", campo="cliente_telefono", width=95),
    ColumnaTabla("Total", campo="monto_total", width=80,
                 alineacion=ft.TextAlign.RIGHT, formato=_formatear_moneda),
    ColumnaTabla("Abonado", campo="monto_abonado", width=80,
                 alineacion=ft.TextAlign.RIGHT, formato=_formatear_moneda),
    ColumnaTabla("Pendiente", campo="monto_pendiente", width=90,
                 alineacion=ft.TextAlign.RIGHT, formato=_formatear_moneda),
    ColumnaTabla("Venta", campo="fecha_venta", width=85, formato=_formatear_fecha),
    ColumnaTabla("Vence", campo="fecha_vencimiento", width=85, formato=_formatear_fecha),
    ColumnaTabla("Estado", campo="estado", width=80, formato=lambda v: (v or "").capitalize()),
]

COLUMNAS_CLIENTES = [
    ColumnaTabla("Nombre", campo="nombre", width=200),
    ColumnaTabla("Cédula", campo="cedula", width=110),
    ColumnaTabla("Teléfono", campo="telefono", width=110),
    ColumnaTabla("Dirección", campo="direccion", width=200),
]


class CuentasPorCobrarView(ft.Column):
    """
    Vista principal del módulo: dos pestañas, "Cuentas por Cobrar" y
    "Clientes". Todos los diálogos (abonar, historial, alta/edición de
    cliente) los arma el módulo — esta vista solo expone la tabla, el
    buscador, el paginador y el resumen.
    """

    def __init__(
        self,
        on_buscar_cuentas,
        on_cambiar_filtro_cuentas,
        on_cambiar_pagina_cuentas,
        on_abonar,
        on_ver_historial,
        on_buscar_clientes,
        on_cambiar_pagina_clientes,
        on_nuevo_cliente,
        on_editar_cliente,
        on_eliminar_cliente,
        on_ver_deudas_cliente,
    ):
        super().__init__(expand=True, spacing=AppSpacing.SECTION_SPACING)
        self.tema = ThemeManager.theme

        # --------------------------------------------------------
        # Pestaña: Cuentas por Cobrar
        # --------------------------------------------------------
        self.tarjeta_total = TarjetaResumen(
            titulo="Total por cobrar",
            valor="$0.00",
            descripcion="Suma de deudas pendientes y parciales",
            icono=ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED,
        )

        self.campo_buscar_cuentas = CampoTexto(
            etiqueta="Buscar cliente...",
            width=260,
            on_change=lambda e: on_buscar_cuentas(e.control.value),
        )

        self.filtro_cuentas = ft.Dropdown(
            width=180,
            value="pendientes",
            options=[
                ft.dropdown.Option("pendientes", "Solo pendientes"),
                ft.dropdown.Option("todas", "Todas"),
            ],
            on_change=lambda e: on_cambiar_filtro_cuentas(e.control.value),
        )

        self.seccion_recordatorios = ft.Column(spacing=AppSpacing.SM, visible=False)

        self.tabla_cuentas = TablaDatos(
            columnas=COLUMNAS_CUENTAS,
            acciones=[
                AccionTabla(
                    icono=ft.icons.PAYMENTS_ROUNDED,
                    tooltip="Registrar abono",
                    callback=on_abonar,
                    color=self.tema.primary,
                ),
                AccionTabla(
                    icono=ft.icons.HISTORY_ROUNDED,
                    tooltip="Ver historial de abonos",
                    callback=on_ver_historial,
                ),
            ],
        )

        self.paginador_cuentas = Paginador(
            on_change=on_cambiar_pagina_cuentas, elementos_por_pagina=15
        )

        # La tabla es más ancha que muchas pantallas: se envuelve en un
        # Row con scroll horizontal en vez de dejarla desbordar el layout.
        self.contenedor_tabla_cuentas = ft.Row(
            [self.tabla_cuentas],
            scroll=ft.ScrollMode.AUTO,
        )

        self.tab_cuentas = ft.Column(
            [
                ft.Row([self.tarjeta_total]),
                ft.Row([self.campo_buscar_cuentas, self.filtro_cuentas], spacing=AppSpacing.SM),
                self.seccion_recordatorios,
                self.contenedor_tabla_cuentas,
                ft.Row([self.paginador_cuentas], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=AppSpacing.SECTION_SPACING,
            expand=True,
        )

        # --------------------------------------------------------
        # Pestaña: Clientes
        # --------------------------------------------------------
        self.campo_buscar_clientes = CampoTexto(
            etiqueta="Buscar cliente...",
            width=260,
            on_change=lambda e: on_buscar_clientes(e.control.value),
        )

        self.btn_nuevo_cliente = ft.ElevatedButton(
            "Nuevo Cliente",
            icon=ft.icons.PERSON_ADD_ROUNDED,
            on_click=lambda e: on_nuevo_cliente(),
        )

        self.tabla_clientes = TablaDatos(
            columnas=COLUMNAS_CLIENTES,
            acciones=[
                AccionTabla(
                    icono=ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED,
                    tooltip="Ver deudas",
                    callback=on_ver_deudas_cliente,
                ),
                AccionTabla(icono=ft.icons.EDIT_ROUNDED, tooltip="Editar", callback=on_editar_cliente),
                AccionTabla(
                    icono=ft.icons.PERSON_OFF_ROUNDED,
                    tooltip="Desactivar",
                    callback=on_eliminar_cliente,
                    color=ft.colors.RED_400,
                ),
            ],
        )

        self.paginador_clientes = Paginador(
            on_change=on_cambiar_pagina_clientes, elementos_por_pagina=15
        )

        self.tab_clientes = ft.Column(
            [
                ft.Row(
                    [self.campo_buscar_clientes, self.btn_nuevo_cliente],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.tabla_clientes,
                ft.Row([self.paginador_clientes], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=AppSpacing.SECTION_SPACING,
            expand=True,
        )

        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Cuentas por Cobrar",
                    content=ft.Container(self.tab_cuentas, padding=ft.padding.only(top=AppSpacing.SM)),
                ),
                ft.Tab(
                    text="Clientes",
                    content=ft.Container(self.tab_clientes, padding=ft.padding.only(top=AppSpacing.SM)),
                ),
            ],
            expand=True,
        )

        self.controls = [
            ft.Text("Cuentas por Cobrar y Clientes", weight="bold", size=22),
            self.tabs,
        ]

    # ------------------------------------------------------------
    # Métodos públicos usados por el módulo
    # ------------------------------------------------------------
    def actualizar_total(self, total: float):
        # Se reconstruye el contenido de la tarjeta en vez de asomarse a
        # su estructura interna (Column[header, body, footer]), para que
        # esta vista no dependa de detalles privados de TarjetaResumen.
        nueva = TarjetaResumen(
            titulo="Total por cobrar",
            valor=_formatear_moneda(total),
            descripcion="Suma de deudas pendientes y parciales",
            icono=ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED,
        )
        self.tarjeta_total.content = nueva.content
        self.tarjeta_total.update()

    def actualizar_recordatorios(self, recordatorios: list[str]):
        self.seccion_recordatorios.controls.clear()
        if recordatorios:
            self.seccion_recordatorios.visible = True
            self.seccion_recordatorios.controls.append(
                TarjetaAdvertencia(
                    titulo="Cuentas que necesitan seguimiento",
                    mensaje="\n".join(recordatorios),
                    icono=ft.icons.NOTIFICATIONS_ACTIVE_ROUNDED,
                )
            )
        else:
            self.seccion_recordatorios.visible = False
        self.seccion_recordatorios.update()

    def poblar_tabla_cuentas(self, cuentas: list[dict], estado_por_fila: dict):
        self.tabla_cuentas.limpiar()
        for cuenta in cuentas:
            valores = [
                col.formato(cuenta.get(col.campo)) if col.formato else cuenta.get(col.campo)
                for col in COLUMNAS_CUENTAS
            ]
            self.tabla_cuentas.agregar_fila(
                valores,
                item_id=cuenta["id_cuenta"],
                estado=estado_por_fila.get(cuenta["id_cuenta"]),
            )
        self.tabla_cuentas.actualizar()

    def poblar_tabla_clientes(self, clientes: list[dict]):
        self.tabla_clientes.limpiar()
        for cliente in clientes:
            valores = [
                col.formato(cliente.get(col.campo)) if col.formato else cliente.get(col.campo)
                for col in COLUMNAS_CLIENTES
            ]
            self.tabla_clientes.agregar_fila(valores, item_id=cliente["id_cliente"])
        self.tabla_clientes.actualizar()

    def actualizar_paginador_cuentas(self, total: int):
        self.paginador_cuentas.establecer_total(total, actualizar=False)
        self.paginador_cuentas.update()

    def actualizar_paginador_clientes(self, total: int):
        self.paginador_clientes.establecer_total(total, actualizar=False)
        self.paginador_clientes.update()