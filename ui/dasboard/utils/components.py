import flet as ft
# =========================================
# INPUT BASE REUTILIZABLE
# =========================================
def create_input(
    label,
    icon,
    password=False,
    width=320,
    on_submit=None
):

    field = ft.TextField(
        label=label,
        prefix_icon=icon,

        password=password,
        can_reveal_password=False,

        width=width,
        height=55,

        border_radius=12,

        filled=True,
        bgcolor="#0D1117",

        border_color="#2A2F3A",
        focused_border_color="#4C8DFF",

        text_size=15,

        on_submit=on_submit,
    )

    return field


# =========================================
# PASSWORD FIELD CON TOGGLE
# =========================================
def make_password_field(
    label="Contraseña",
    width=320,
    on_enter=None
):

    password_field = create_input(
        label=label,
        icon=ft.icons.LOCK,
        password=True,
        width=width,
        on_submit=on_enter
    )

    toggle_btn = ft.IconButton(
        icon=ft.icons.VISIBILITY_OFF,
        icon_color="white70",
        icon_size=20,
        tooltip="Mostrar/Ocultar contraseña",
        on_click=lambda e: toggle_password(e, password_field)
    )

    row = ft.Row(
        [
            password_field,
            toggle_btn
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    return row, password_field, toggle_btn


# =========================================
# TOGGLE PASSWORD
# =========================================
def toggle_password(e, password_field):

    password_field.password = not password_field.password

    e.control.icon = (
        ft.icons.VISIBILITY
        if not password_field.password
        else ft.icons.VISIBILITY_OFF
    )

    password_field.update()
    e.control.update()