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


class DashboardModule:

    def __init__(self, page, content_area, usuario_actual):
        self.page = page
        self.content_area = content_area
        self.usuario_actual = usuario_actual
        self._module_ingredientes = None
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

        # Guardamos una referencia al módulo en el propio control devuelto
        # para poder llamar a cargar_datos_iniciales() una vez que quien
        # nos invoque (App.py) ya haya hecho page.add(resultado) + page.update().
        resultado.dashboard_module = self
        return resultado

    def cargar_datos_iniciales(self) -> None:
        """Debe llamarse DESPUÉS de que este control ya fue agregado a la
        página (page.add(...) + page.update()). Antes de eso, cargar()
        no puede refrescar la UI porque los controles no tienen `.page`."""
        if self._module_ingredientes:
            self._module_ingredientes.cargar()

    def _cargar_modulo_inicial(self) -> None:
        """Carga el módulo inicial (Ingredientes) sin llamar a update()
        de content_area -- todavía no fue agregado a la página en este
        punto (construir() se ejecuta ANTES de page.add()). Llamar
        update() acá provoca:
        AssertionError: Control must be added to the page first."""
        layout, module = ingredientes_view(self.page, self.content_area)
        self._module_ingredientes = module
        self.content_area.content = layout

    # ============================================================
    # SIDEBAR
    # ============================================================

    def _crear_sidebar(self) -> None:

        self._sidebar_items = [
            ("Ingredientes", AppIcons.INGREDIENT, self._ir_ingredientes),
            ("Recetas", AppIcons.RECIPE, self._ir_recetas),
            ("Productos", AppIcons.PRODUCT, self._ir_productos),
            ("Recursos del Negocio", AppIcons.INVENTARIO, self._ir_recursos),
            ("Mi Negocio", ft.icons.STORE_OUTLINED, self._ir_mi_negocio),
            ("Producción", AppIcons.FATORY, self._ir_produccion),
            ("Ventas", AppIcons.SALES, self._ir_ventas),
            ("Cerrar Sesión", AppIcons.LOGOUT, self._logout),
        ]

        items = [
            self._crear_item_menu(texto, icono, callback)
            for texto, icono, callback in self._sidebar_items
        ]

        self.sidebar = ft.Container(
            width=260,
            bgcolor=ThemeManager.theme.sidebar,
            padding=AppSpacing.SIDEBAR_PADDING,
            content=ft.Column(
                [
                    ft.Text(
                        "La Dulce Tía",
                        size=20,
                        weight="bold",
                        color=ThemeManager.theme.primary,
                    ),
                    ft.Divider(),
                    *items,
                ],
                spacing=AppSpacing.CONTROL_SPACING,
            ),
        )

    def _crear_item_menu(self, texto, icono, on_click):
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

    # ============================================================
    # NAVEGACIÓN ENTRE MÓDULOS
    # ============================================================
    #
    # ✅ Ya no se llama a module.cargar() después de content_area.update().
    # *_view() crea una instancia nueva del módulo, y su construir()
    # YA hace la carga inicial de datos (población de la tabla en
    # memoria) antes de devolver el layout. content_area.update() solo
    # renderiza ese árbol ya poblado. Llamar a module.cargar() otra vez
    # acá disparaba una segunda consulta idéntica al service/BD en CADA
    # clic del sidebar -- trabajo duplicado sin ningún beneficio visual.

    def _ir_ingredientes(self, e=None):
        layout, module = ingredientes_view(self.page, self.content_area)
        self._module_ingredientes = module  # ✅ antes no se actualizaba esta referencia
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
        # ✅ Cargar datos después de que la vista esté en la página
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

            self.page.update()  # ✅ Forzar actualización de toda la página

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