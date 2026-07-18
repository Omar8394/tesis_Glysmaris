import flet as ft

# =========================================================
# VISTAS
# =========================================================
from ui.modules.operacones.ingredientes.ingredientes import ingredientes_view
from ui.dasboard.views.productos import productos_view
from ui.dasboard.views.usuarios_view import gestion_usuarios_view
from ui.dasboard.views.produccion import produccion_view
from ui.dasboard.views.inicio import inicio_view
from ui.dasboard.views.recetas import recetas_view
from ui.dasboard.views.ventas import ventas_view
from ui.dasboard.views.catalogo_ventas import catalogo_ventas_view
from ui.dasboard.views.compras import compras_view

# =========================================================
# COMPONENTES
# =========================================================
from ui.dasboard.components.nav_item import create_nav_item
from ui.dasboard.components.hover_effect import handle_hover
from ui.dasboard.dialogs.exit_dialog import salir_app

# =========================================================
# UTILS
# =========================================================
from ui.dasboard.utils.Navigation import KeyboardNavigator


def dashboard_view(page: ft.Page, navigator: KeyboardNavigator):
    page.title = "Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0D1117"
    page.window_full_screen = True
    page.padding = 0

    # ÁREA CENTRAL
    content = ft.Container(expand=True, content=inicio_view(page, None))

    # ========== FUNCIONES DE CAMBIO DE VISTA (sin cambios) ==========
    def mostrar_inicio(e=None):
        content.content = inicio_view(page, content)
        page.update()

    def mostrar_ingredientes(e=None):
        content.content = ingredientes_view(page, content)
        page.update()

    def mostrar_productos(e=None):
        content.content = productos_view(page, content)
        page.update()

    def mostrar_gestion_usuarios(e=None):
        content.content = gestion_usuarios_view(page, navigator)
        page.update()

    def mostrar_produccion(e=None):
        content.content = produccion_view(page, content)
        page.update()

    def mostrar_recetas(e=None):
        content.content = recetas_view(page, content)
        page.update()

    def mostrar_ventas(e=None):
        content.content = ventas_view(page, content)
        page.update()

    def mostra_catalogo_ventas(e=None):
        content.content = catalogo_ventas_view(page, content)
        page.update()

    def mostrar_compras(e=None):
        content.content = compras_view(page, content)
        page.update()

    # ========== ESTADO DEL SIDEBAR ==========
    sidebar_expanded = True
    open_menu = None  # 'inventario', 'ventas', 'configuracion'

    # ========== FUNCIÓN AUXILIAR PARA CREAR ÍTEM CON TOOLTIP ==========
    def _make_nav_item(label, icon, on_click, show_label=True):
        icon_ctrl = ft.Icon(icon, color="white")
        row_controls = [icon_ctrl]
        if show_label:
            row_controls.append(ft.Text(label, size=14, color="white"))
        container = ft.Container(
            content=ft.Row(row_controls, alignment=ft.MainAxisAlignment.START),
            on_click=on_click,
            padding=10,
            border_radius=8,
            ink=True,
        )
        return ft.Tooltip(message=label, content=container)

    # ========== CONSTRUCCIÓN DINÁMICA DEL SIDEBAR ==========
    def build_sidebar():
        # Submenús
        inventario_menu = ft.Column(
            controls=[
                _make_nav_item("Productos", ft.icons.LIST, mostrar_productos, show_label=sidebar_expanded),
                _make_nav_item("Ingredientes", ft.icons.CATEGORY, mostrar_ingredientes, show_label=sidebar_expanded),
                _make_nav_item("Producción", ft.icons.BAKERY_DINING, mostrar_produccion, show_label=sidebar_expanded),

            ],
            visible=(open_menu == "inventario")
        )

        ventas_menu = ft.Column(
            controls=[
                _make_nav_item("Registro", ft.icons.POINT_OF_SALE, mostrar_ventas, show_label=sidebar_expanded),
                _make_nav_item("Reportes", ft.icons.BAR_CHART, None, show_label=sidebar_expanded),
                _make_nav_item("Catalogo", ft.icons.SUBDIRECTORY_ARROW_LEFT_ROUNDED, mostra_catalogo_ventas, show_label=sidebar_expanded),
            ],
            visible=(open_menu == "ventas")
        )


        configuracion_menu = ft.Column(
            controls=[
                _make_nav_item("Gestión de Usuarios", ft.icons.PEOPLE, mostrar_gestion_usuarios, show_label=sidebar_expanded),
            ],
            visible=(open_menu == "configuracion")
        )

        # Botón colapsar/expandir
        toggle_btn = ft.IconButton(
            icon=ft.icons.MENU_OPEN if sidebar_expanded else ft.icons.MENU,
            on_click=toggle_sidebar,
            tooltip="Colapsar barra" if sidebar_expanded else "Expandir barra",
            icon_color="white",
        )

        # Lista de controles principales
        controls_list = [
            toggle_btn,
            ft.Text("SISTEMA DULCE TÍA", size=12, weight="BOLD", color="blue400", visible=sidebar_expanded),
            _make_nav_item("Inicio", ft.icons.HOME, mostrar_inicio, show_label=sidebar_expanded),
            _make_nav_item("Inventario", ft.icons.STORAGE, toggle_menu("inventario"), show_label=sidebar_expanded),
            inventario_menu,
            _make_nav_item("Ventas", ft.icons.ATTACH_MONEY, toggle_menu("ventas"), show_label=sidebar_expanded),
            ventas_menu,
            _make_nav_item("Compras", ft.icons.SHOPPING_CART, mostrar_compras, show_label=sidebar_expanded),
            _make_nav_item("Recetas", ft.icons.RESTAURANT, mostrar_recetas, show_label=sidebar_expanded),
            _make_nav_item("Configuración", ft.icons.SETTINGS, toggle_menu("configuracion"), show_label=sidebar_expanded),
            configuracion_menu,
            ft.Divider(height=20, color="white10", visible=sidebar_expanded),
            _make_nav_item("Salir", ft.icons.EXIT_TO_APP, lambda e: salir_app(page), show_label=sidebar_expanded),
        ]

        return ft.Container(
            width=280 if sidebar_expanded else 70,
            bgcolor="#161B22",
            padding=ft.padding.only(top=10, left=10, right=10) if sidebar_expanded else ft.padding.only(top=10, left=5, right=5),
            border=ft.border.only(right=ft.BorderSide(1, "#30363D")),
            content=ft.Column(controls_list, spacing=5, alignment=ft.MainAxisAlignment.START)
        )

    # ========== FUNCIONES PARA ALTERNAR EXPANSIÓN Y MENÚS ==========
    def toggle_sidebar(e=None):
        nonlocal sidebar_expanded
        sidebar_expanded = not sidebar_expanded
        # Reconstruir el sidebar y reemplazarlo en la fila principal
        main_row.controls[0] = build_sidebar()
        page.update()

    def toggle_menu(menu_name):
        def handler(e):
            nonlocal open_menu
            if open_menu == menu_name:
                open_menu = None
            else:
                open_menu = menu_name
            main_row.controls[0] = build_sidebar()
            page.update()
        return handler

    # ========== CONSTRUCCIÓN INICIAL ==========
    sidebar = build_sidebar()
    main_row = ft.Row(controls=[sidebar, content], expand=True, spacing=0)

    # Navegación por teclado (opcional, ya que al colapsar los botones se reconstruyen)
    def dashboard_keyboard(e: ft.KeyboardEvent):
        # Puedes implementar navegación si lo deseas
        pass

    page.on_keyboard_event = dashboard_keyboard

    return main_row