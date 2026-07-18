import flet as ft

from ui.core.database.schema.migrator import migrar_todas_las_tablas
from ui.core.services.factory import ServiceFactory
from ui.modules.login.login_view import login_view
from ui.modules.dashboard.dashboard_view import dashboard_view
from ui.core.theme_manager import ThemeManager


def main(page: ft.Page):
    # 1. Crear tablas si no existen
    migrar_todas_las_tablas()

    # 2. Configuración de la página
    page.title = "La Dulce Tía ERP"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # ✅ Tamaño chico y fijo SOLO para la pantalla de login — evita el
    # espacio vacío alrededor de la tarjeta que se ve en una ventana
    # de 1200x700 pensada para el dashboard.
    page.window_width = 470
    page.window_height = 600
    page.window_resizable = False
    page.window_center()

    # 3. Tema por defecto
    ThemeManager.set_theme("dulce_tia")
    page.bgcolor = ThemeManager.theme.background

    # 4. Área donde se montarán los módulos
    content_area = ft.Container(expand=True)

    # 5. Callback para login exitoso
    def on_login_success(role):
        # ✅ Recién acá, al pasar al dashboard, la ventana vuelve a su
        # tamaño grande (y ahora sí redimensionable/maximizada).
        page.window_resizable = True
        page.window_width = 1250
        page.window_height = 700
        page.window_full_screen = True, #page.window_maximized = True
        page.window_center()

        page.controls.clear()
        dashboard = dashboard_view(page, content_area, role)
        page.add(dashboard)
        page.update()
        if hasattr(dashboard, "dashboard_module"):
            dashboard.dashboard_module.cargar_datos_iniciales()

    # 6. Servicio de autenticación
    auth_service = ServiceFactory.get_auth_service()

    # 7. Mostrar login
    login = login_view(page, auth_service, on_login_success)
    page.add(login)
    page.update()


ft.app(target=main)