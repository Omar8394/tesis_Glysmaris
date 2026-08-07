"""
============================================================
Sistema La Dulce Tía

Archivo:
    inicio.py

Responsabilidad:
    Vista de bienvenida / inicio. Se muestra como módulo
    inicial del dashboard justo después de iniciar sesión.

Nota de arquitectura:
    No tiene service ni repository: es una vista de
    presentación pura, no lee ni escribe datos propios.
    Sigue el mismo patrón plano que ingredientes_view,
    ventas_view, etc.: expone una función `inicio_view`
    que devuelve (layout, module).
============================================================
"""

from __future__ import annotations

from datetime import datetime
import flet as ft

from ui.core.theme_manager import ThemeManager
from ui.core.spacing import AppSpacing


# ---------------------------------------------------------------------------
# Accesos rápidos que se muestran como tarjetas.
# "callback_attr" es el nombre del método correspondiente en
# DashboardModule (self._ir_xxx), para conectarlos con on_navegar.
# ---------------------------------------------------------------------------
MODULOS = [
    {"titulo": "Producción", "icono": ft.icons.FACTORY_OUTLINED,
     "descripcion": "Órdenes de producción y mermas", "callback_attr": "_ir_produccion"},
    {"titulo": "Ventas", "icono": ft.icons.POINT_OF_SALE_OUTLINED,
     "descripcion": "Registro de ventas y stock", "callback_attr": "_ir_ventas"},
    {"titulo": "Ingredientes", "icono": ft.icons.INVENTORY_2_OUTLINED,
     "descripcion": "Inventario y lotes (PEPS)", "callback_attr": "_ir_ingredientes"},
    {"titulo": "Productos", "icono": ft.icons.CAKE_OUTLINED,
     "descripcion": "Catálogo de productos", "callback_attr": "_ir_productos"},
    {"titulo": "Recetas", "icono": ft.icons.MENU_BOOK_OUTLINED,
     "descripcion": "Recetas y preparación", "callback_attr": "_ir_recetas"},
    {"titulo": "Recursos del Negocio", "icono": ft.icons.HANDYMAN_OUTLINED,
     "descripcion": "Empaques, utensilios y herramientas", "callback_attr": "_ir_recursos"},
    {"titulo": "Cuentas por Cobrar", "icono": ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED,
     "descripcion": "Clientes, abonos y deudas", "callback_attr": "_ir_cuentas_por_cobrar"},
    {"titulo": "Mi Negocio", "icono": ft.icons.STORE_OUTLINED,
     "descripcion": "Costos de mano de obra y hora", "callback_attr": "_ir_mi_negocio"},
]


def _saludo_segun_hora() -> str:
    hora = datetime.now().hour
    if hora < 12:
        return "Buenos días"
    elif hora < 19:
        return "Buenas tardes"
    else:
        return "Buenas noches"


def inicio_view(page: ft.Page, content_area: ft.Container,
                 usuario_actual=None, dashboard_module=None):
    """
    Punto de entrada del módulo, con la misma firma que el resto
    de las vistas (ingredientes_view, ventas_view, ...).

    dashboard_module: referencia a la instancia de DashboardModule,
    para poder invocar sus métodos _ir_xxx al hacer clic en una
    tarjeta. Si no se pasa, las tarjetas simplemente no navegan.
    """
    nombre_usuario = getattr(usuario_actual, "nombre", None) if usuario_actual else None
    layout = _construir_layout(page, nombre_usuario, dashboard_module)
    return layout, None  # sin "module" porque no hay nada que precargar


def _construir_layout(page: ft.Page, nombre_usuario, dashboard_module) -> ft.Control:
    logo = ft.Image(
        src="logo.png",
        width=150,
        height=150,
        fit=ft.ImageFit.CONTAIN,
    )

    saludo = _saludo_segun_hora()
    saludo_texto = f"{saludo}{', ' + nombre_usuario if nombre_usuario else ''}!"

    encabezado = ft.Column(
        controls=[
            logo,
            ft.Text(saludo_texto, size=26, weight=ft.FontWeight.BOLD,
                     color=ThemeManager.theme.primary),
            ft.Text("Bienvenido/a al sistema de La Dulce Tía",
                     size=16, color=ThemeManager.theme.text_secondary),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )

    tarjetas = [_crear_tarjeta(m, dashboard_module) for m in MODULOS]
    grid = ft.GridView(
        expand=False,
        runs_count=3,
        max_extent=260,
        child_aspect_ratio=1.6,
        spacing=AppSpacing.SM if hasattr(AppSpacing, "SM") else 14,
        run_spacing=14,
        controls=tarjetas,
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(height=24),
            encabezado,
            ft.Container(height=24),
            ft.Text("Accesos rápidos", size=18, weight=ft.FontWeight.W_600,
                     color=ThemeManager.theme.text_secondary),
            ft.Container(height=8),
            grid,
        ],
    )


def _crear_tarjeta(modulo: dict, dashboard_module) -> ft.Control:
    def _on_click(e):
        if dashboard_module is not None:
            callback = getattr(dashboard_module, modulo["callback_attr"], None)
            if callable(callback):
                callback(e)

    return ft.Card(
        elevation=2,
        content=ft.Container(
            padding=16,
            ink=True,
            on_click=_on_click,
            content=ft.Column(
                controls=[
                    ft.Icon(modulo["icono"], size=32, color=ThemeManager.theme.primary),
                    ft.Text(modulo["titulo"], weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(modulo["descripcion"], size=12,
                             color=ThemeManager.theme.text_secondary),
                ],
                spacing=6,
            ),
        ),
    )