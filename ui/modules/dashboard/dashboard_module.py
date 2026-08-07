"""
============================================================
Sistema La Dulce Tía

Archivo:
    dashboard_module.py

Responsabilidad:
    Módulo del dashboard principal.
    Coordina el sidebar y el área de contenido.

Nota de arquitectura:
    Clase plana, igual que IngredienteModule / RecetasModule /
    ProductoModule. No hereda de la jerarquía Module/DashboardModule
    base (widget_registry) ni usa module_registry: ninguno de los
    dos está implementado en ningún punto real del sistema, así que
    mantenerlos como base habría sido herencia sin funcionalidad.
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.layouts.dashboard_layout import DashboardLayout
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager
from ui.modules.operaciones.ingredientes.ingredientes import ingredientes_view
from ui.modules.operaciones.recetas.recetas import recetas_view
from ui.modules.operaciones.productos.productos import productos_view
from ui.modules.operaciones.activos.activos import activos_view
from ui.modules.operaciones.produccion.produccion import produccion_view
from ui.modules.operaciones.activos.mi_negocio import mi_negocio_view
from ui.modules.operaciones.ventas.ventas import ventas_view
from ui.modules.operaciones.estadisticas.estadisticas import estadisticas_view
from ui.modules.operaciones.cuentas_por_cobrar.cuentas_por_cobrar import cuentas_por_cobrar_view
from ui.modules.operaciones.reportes.reporte import reporte_view  # nuevo
from ui.modules.seguridad.usuario import usuarios_view 
from ui.modules.inicio_view import inicio_view

class DashboardModule:

    def __init__(self, page, content_area, usuario_actual):
        self.page = page
        self.content_area = content_area
        self.usuario_actual = usuario_actual
        self._module_ingredientes = None
        self._sidebar_expanded = True  # estado del sidebar
        self.sidebar = None
        self._crear_sidebar()

    # ============================================================
    # CONSTRUCCIÓN
    # ============================================================

    def construir(self):
        self._cargar_modulo_inicial()
        resultado = DashboardLayout(
            sidebar=self.sidebar,
            contenido=self.content_area,
        )
        resultado.dashboard_module = self
        return resultado

    def cargar_datos_iniciales(self) -> None:
        if self._module_ingredientes:
            self._module_ingredientes.cargar()

    def _cargar_modulo_inicial(self) -> None:
        layout, module = inicio_view(self.page, self.content_area,
                                    usuario_actual=self.usuario_actual,
                                    dashboard_module=self)
        self.content_area.content = layout

    

    # ============================================================
    # SIDEBAR
    # ============================================================

    def _crear_sidebar(self) -> None:
        """Crea el contenedor del sidebar y lo construye por primera vez."""
        self.sidebar = ft.Container(
            width=260 if self._sidebar_expanded else 60,
            bgcolor=ThemeManager.theme.sidebar,
            padding=AppSpacing.SIDEBAR_PADDING,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )
        self._rebuild_sidebar()

    def _rebuild_sidebar(self) -> None:
        """Reconstruye el contenido del sidebar según el estado expandido/colapsado."""
        items = self._build_items()

        if self._sidebar_expanded:
            # ... construir items expandidos ...
            self.sidebar.width = 260
            self.sidebar.padding = AppSpacing.SIDEBAR_PADDING
            self.sidebar.content = ft.Column(
                [
                    self._build_header(),
                    ft.Divider(),
                    *items,
                ],
                spacing=AppSpacing.CONTROL_SPACING,
            )
        else:
            # ... construir items colapsados ...
            self.sidebar.width = 60
            self.sidebar.padding = AppSpacing.SIDEBAR_PADDING_COLLAPSED
            self.sidebar.content = ft.Column(
                [
                    self._build_header(),
                    ft.Divider(),
                    *items,
                ],
                spacing=AppSpacing.CONTROL_SPACING,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        # Solo actualizar si el control ya está en la página
        if self.sidebar.page:
            self.sidebar.update()

    def _build_header(self):
        """Construye la fila superior del sidebar con el botón de alternar y el título."""
        toggle_icon = ft.icons.MENU if self._sidebar_expanded else ft.icons.MENU_OPEN
        toggle_button = ft.IconButton(
            icon=toggle_icon,
            icon_color=ThemeManager.theme.text_secondary,
            on_click=self._toggle_sidebar,
            tooltip="Colapsar/Expandir",
        )

        if self._sidebar_expanded:
            title = ft.Text(
                "La Dulce Tía",
                size=20,
                weight="bold",
                color=ThemeManager.theme.primary,
            )
            return ft.Row(
                [toggle_button, title],
                spacing=AppSpacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            # Solo el botón
            return ft.Row(
                [toggle_button],
                alignment=ft.MainAxisAlignment.CENTER,
            )

    def _build_items(self):
        """Construye la lista de items del menú según el estado."""
        if self._sidebar_expanded:
            return self._build_items_expanded()
        else:
            return self._build_items_collapsed()

    def _build_items_expanded(self):
        """Items para sidebar expandido."""
        items = []

        # Grupo Inventario (ExpansionTile)
        inventario_tile = ft.ExpansionTile(
            title=ft.Row(
                [
                    ft.Icon(AppIcons.INVENTARIO, color=ThemeManager.theme.text_secondary),
                    ft.Text("Inventario", color=ThemeManager.theme.text_secondary),
                ],
                spacing=AppSpacing.SM,
            ),
            controls=[
                self._crear_item_menu("Ingredientes", AppIcons.INGREDIENT, self._ir_ingredientes),
                self._crear_item_menu("Productos", AppIcons.PRODUCT, self._ir_productos),
                self._crear_item_menu("Recursos del Negocio", AppIcons.INVENTARIO, self._ir_recursos),
                self._crear_item_menu("Recetas", AppIcons.RECIPE, self._ir_recetas),
            ],
        )
        items.append(inventario_tile)

        # Items individuales
        individual_items = [
            ("Inicio", ft.icons.HOME_OUTLINED, self._ir_inicio),
            ("Mi Negocio", ft.icons.STORE_OUTLINED, self._ir_mi_negocio),
            ("Producción", AppIcons.FATORY, self._ir_produccion),
            ("Ventas", AppIcons.SALES, self._ir_ventas),
            ("Cuentas por Cobrar", ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, self._ir_cuentas_por_cobrar),
            ("Estadísticas", ft.icons.BAR_CHART_ROUNDED, self._ir_estadisticas),
            ("Reportes", ft.icons.ASSESSMENT_ROUNDED, self._ir_reportes),
            ("Usuarios", ft.icons.PEOPLE_ROUNDED, self._ir_usuarios),
            ("Cerrar Sesión", AppIcons.LOGOUT, self._logout),
        ]
        for texto, icono, callback in individual_items:
            items.append(self._crear_item_menu(texto, icono, callback))

        return items

    def _build_items_collapsed(self):
        """Items para sidebar colapsado (solo iconos con tooltips)."""
        items = []

        # Grupo Inventario: PopupMenuButton con tooltip
        inventario_popup = ft.Tooltip(
            message="Inventario",
            wait_duration=3000,
            content=ft.PopupMenuButton(
                icon=AppIcons.INVENTARIO,
                items=[
                    ft.PopupMenuItem(
                        content=ft.Row([
                            ft.Icon(AppIcons.INGREDIENT, color=ThemeManager.theme.text_secondary),
                            ft.Text("Ingredientes", color=ThemeManager.theme.text_secondary),
                        ]),
                        on_click=lambda e: self._ir_ingredientes(),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row([
                            ft.Icon(AppIcons.PRODUCT, color=ThemeManager.theme.text_secondary),
                            ft.Text("Productos", color=ThemeManager.theme.text_secondary),
                        ]),
                        on_click=lambda e: self._ir_productos(),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row([
                            ft.Icon(AppIcons.INVENTARIO, color=ThemeManager.theme.text_secondary),
                            ft.Text("Recursos del Negocio", color=ThemeManager.theme.text_secondary),
                        ]),
                        on_click=lambda e: self._ir_recursos(),
                    ),

                    ft.PopupMenuItem(
                        content=ft.Row([ft.Icon(AppIcons.RECIPE, color=ThemeManager.theme.text_secondary),
                                        ft.Text("Recetas", color=ThemeManager.theme.text_secondary)]),
                        on_click=lambda e: self._ir_recetas(),
                    ),
                ],
            ),
        )
        items.append(inventario_popup)

        # Items individuales
        individual_items = [
            ("Inicio", ft.icons.HOME_OUTLINED, self._ir_inicio),
            ("Mi Negocio", ft.icons.STORE_OUTLINED, self._ir_mi_negocio),
            ("Producción", AppIcons.FATORY, self._ir_produccion),
            ("Ventas", AppIcons.SALES, self._ir_ventas),
            ("Cuentas por Cobrar", ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, self._ir_cuentas_por_cobrar),
            ("Estadísticas", ft.icons.BAR_CHART_ROUNDED, self._ir_estadisticas),
            ("Reportes", ft.icons.ASSESSMENT_ROUNDED, self._ir_reportes),
            ("Usuarios", ft.icons.PEOPLE_ROUNDED, self._ir_usuarios),
            ("Cerrar Sesión", AppIcons.LOGOUT, self._logout),
        ]
        for texto, icono, callback in individual_items:
            items.append(
                ft.Tooltip(
                    message=texto,
                    wait_duration=3000,
                    content=ft.Container(
                        content=ft.IconButton(
                            icon=icono,
                            icon_color=ThemeManager.theme.text_secondary,
                            on_click=callback,
                        ),
                        padding=10,
                    ),
                )
            )

        return items

    def _crear_item_menu(self, texto, icono, on_click):
        """Crea un item de menú para modo expandido."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icono, color=ThemeManager.theme.text_secondary),
                    ft.Text(texto, color=ThemeManager.theme.text_secondary),
                ],
                spacing=AppSpacing.SM,
            ),
            padding=10,
            on_click=on_click,
            ink=True,
            border_radius=8,
        )

    def _toggle_sidebar(self, e=None) -> None:
        """Alterna el estado expandido/colapsado del sidebar."""
        self._sidebar_expanded = not self._sidebar_expanded
        self._rebuild_sidebar()
        self.page.update()  # Refresca toda la página para que el cambio sea visible

    # ============================================================
    # NAVEGACIÓN ENTRE MÓDULOS
    # ============================================================

    def _ir_inicio(self, e=None):
        layout, module = inicio_view(self.page, self.content_area,
                                    usuario_actual=self.usuario_actual,
                                    dashboard_module=self)
        self.content_area.content = layout
        self.content_area.update()

    def _ir_ingredientes(self, e=None):
        layout, module = ingredientes_view(self.page, self.content_area)
        self._module_ingredientes = module
        self.content_area.content = layout
        self.content_area.update()

    def _ir_recetas(self, e=None):
        layout, module = recetas_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()

    def _ir_productos(self, e=None):
        layout, module = productos_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()

    def _ir_recursos(self, e=None):
        layout, module = activos_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()
        if hasattr(module, 'cargar') and callable(module.cargar):
            module.cargar()

    def _ir_mi_negocio(self, e=None):
        import traceback, sys
        try:
            layout, module = mi_negocio_view(
                self.page,
                self.content_area,
                on_ir_a_activos=self._ir_recursos,
            )
            self.content_area.content = layout
            self.content_area.update()

            if hasattr(module, 'cargar') and callable(module.cargar):
                module.cargar()

            self.page.update()
            print("MI NEGOCIO: cargado sin errores", flush=True)
        except Exception:
            print("MI NEGOCIO: ERROR", flush=True)
            traceback.print_exc()
            sys.stdout.flush()

    def _ir_produccion(self, e=None):
        layout, module = produccion_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()

    def _ir_ventas(self, e=None) -> None:
        layout, module = ventas_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()
        if hasattr(module, 'cargar') and callable(module.cargar):
            module.cargar()

    def _ir_cuentas_por_cobrar(self, e=None):
        layout, module = cuentas_por_cobrar_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()
        if hasattr(module, 'cargar') and callable(module.cargar):
            module.cargar()

    def _ir_estadisticas(self, e=None) -> None:
        layout, module = estadisticas_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()

    def _ir_reportes(self, e=None) -> None:
        layout, module = reporte_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()
        if hasattr(module, 'cargar') and callable(module.cargar):
            module.cargar()

    def _ir_usuarios(self, e=None) -> None:
        layout, module = usuarios_view(self.page, self.content_area)
        self.content_area.content = layout
        self.content_area.update()
        if hasattr(module, 'cargar') and callable(module.cargar):
            module.cargar()

    def _logout(self, e=None) -> None:
        """Cierra sesión y vuelve al login."""
        from ui.modules.login.login_view import login_view
        from ui.core.services.factory import ServiceFactory

        auth_service = ServiceFactory.get_auth_service()

        def on_login_success(role):
            self.page.controls.clear()
            from ui.modules.dashboard.dashboard_view import dashboard_view
            dashboard = dashboard_view(self.page, self.content_area, role)
            self.page.controls.clear()
            self.page.add(dashboard)
            self.page.update()
            if hasattr(dashboard, "dashboard_module"):
                dashboard.dashboard_module.cargar_datos_iniciales()

        login = login_view(self.page, auth_service, on_login_success)
        self.page.controls.clear()
        self.page.add(login)
        self.page.update()