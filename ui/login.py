import flet as ft
import bcrypt

from DATABASE.init_db import create_all_tables

from DATABASE.seguridad.init_seguridad import (
    connect_db_seguridad
)

from DATABASE.seguridad.auth_db import (
        verify_login,
        validar_password,
        verify_and_reset_password
)

from DATABASE.seguridad.preguntas_db import (
        get_user_question,
)

from ui.dasboard.dashboard_flet import dashboard_view

from ui.dasboard.utils.Navigation import KeyboardNavigator
from ui.dasboard.utils.components import make_password_field


class App:

    # =========================================================
    # INIT
    # =========================================================
    def __init__(self, page: ft.Page):

        self.page = page

        # navegación teclado
        self.navigator = KeyboardNavigator(page)

        # acción actual
        self.current_action = None

        # =====================================================
        # CONFIGURACIÓN VENTANA
        # =====================================================
        page.title = "Sistema Dulce Tía"

        page.window_width = 500
        page.window_height = 600

        page.window_resizable = False
        page.window_maximizable = False

        page.window_title_bar_hidden = True

        page.window_center()

        page.theme_mode = ft.ThemeMode.DARK

        page.bgcolor = "#0D1117"

        # =====================================================
        # TOP BAR
        # =====================================================
        self.top_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Sistema Dulce Tía",
                        weight="bold",
                        size=13
                    ),

                    ft.Row(
                        [
                            ft.IconButton(
                                ft.icons.REMOVE,
                                icon_size=16,
                                tooltip="Minimizar",
                                on_click=lambda e: setattr(self.page.window, "minimized", True)
                            ),

                            ft.IconButton(
                                ft.icons.CLOSE,
                                icon_size=16,
                                tooltip="Cerrar",
                                on_click=lambda e: self.page.window_close()
                            ),
                        ],
                        spacing=5
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),

            height=40,
            bgcolor="#161B22",
            padding=ft.padding.symmetric(horizontal=10),
        )

        # =====================================================
        # BASE DE DATOS
        # =====================================================
        create_all_tables()
        # =====================================================
        # CONTENEDOR PRINCIPAL
        # =====================================================
        self.main_container = ft.Container(expand=True)

        page.add(self.main_container)

        # =====================================================
        # TECLADO GLOBAL
        # =====================================================
        page.on_keyboard_event = self.handle_keyboard

        # =====================================================
        # LOGIN
        # =====================================================
        self.show_login()

    # =========================================================
    # TECLADO GLOBAL
    # =========================================================
    def handle_keyboard(self, e: ft.KeyboardEvent):

        self.navigator.handle_navigation(e)

        # 🔥 ERROR CORREGIDO:
        # Antes usabas "ENTER"
        # Flet usa "Enter"
        if e.key == "Enter":

            current = self.navigator.get_current_control()

            # LOGIN
            if current == self.password:
                self.login(None)

            elif current == self.username:
                self.navigator.move_focus(1)

            else:
                self.navigator.trigger_current()

    # =========================================================
    # LOGIN UI
    # =========================================================
    def show_login(self):

        # =====================================================
        # INPUTS
        # =====================================================
        self.username = ft.TextField(
            label="Usuario",
            prefix_icon=ft.icons.PERSON,
            width=300
        )

        pwd_row, self.password, toggle_btn = make_password_field(
            "Contraseña",
            width=260
        )

        # =====================================================
        # BOTONES
        # =====================================================
        login_btn = ft.ElevatedButton(
            "Iniciar Sesión",
            width=300,
            height=45,
            on_click=self.login
        )

        forgot_btn = ft.TextButton(
            "¿Olvidaste tu contraseña?",
            on_click=self.open_recovery
        )

        # =====================================================
        # NAVEGACIÓN TECLADO
        # =====================================================
        self.navigator.set_controls(
            [
                self.username,
                self.password,
                login_btn,
                forgot_btn
            ]
        )

        # =====================================================
        # CARD
        # =====================================================
        card = ft.Container(

            width=380,

            padding=30,

            border_radius=20,

            bgcolor="#161B22",

            shadow=ft.BoxShadow(
                blur_radius=20,
                color="black"
            ),

            content=ft.Column(
                [
                    ft.Text(
                        "Iniciar Sesión",
                        size=30,
                        weight="bold"
                    ),

                    ft.Text(
                        "Bienvenido de nuevo",
                        color="grey"
                    ),

                    self.username,

                    pwd_row,

                    login_btn,

                    forgot_btn
                ],

                spacing=15,

                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        # =====================================================
        # LAYOUT
        # =====================================================
        layout = ft.Column(
            [
                self.top_bar,

                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=card
                )
            ],

            spacing=0,
            expand=True
        )

        self.main_container.content = layout

        self.page.update()

        self.username.focus()
    # =========================================================
    # LOGIN
    # =========================================================
    def login(self, e):

        user = self.username.value.strip()

        pwd = self.password.value.strip()

        role = verify_login(user, pwd)

        if role:

            self.show_dashboard()

        else:

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    "Usuario o contraseña incorrectos"
                ),

                bgcolor=ft.colors.RED
            )

            self.page.snack_bar.open = True

            self.page.update()

    # =========================================================
    # DASHBOARD
    # =========================================================
    def show_dashboard(self):

        dashboard = dashboard_view(
            self.page,
            self.navigator
        )

        self.main_container.content = dashboard

        self.page.update()

    # =========================================================
    # RECUPERAR CONTRASEÑA
    # =========================================================
    def open_recovery(self, e):

        # =====================================================
        # STEP 1
        # =====================================================
        username_input = ft.TextField(
            label="Usuario",
            width=300
        )

        # =====================================================
        # STEP 2
        # =====================================================
        question_text = ft.Text(
            "",
            size=14
        )

        answer_input = ft.TextField(
            label="Respuesta",
            width=300
        )

        # =====================================================
        # STEP 3
        # =====================================================
        new_pass_row, new_pass_field, _ = make_password_field(
            "Nueva contraseña",
            width=260
        )

        confirm_pass_row, confirm_pass_field, _ = make_password_field(
            "Confirmar contraseña",
            width=260
        )

        # =====================================================
        # STATUS
        # =====================================================
        status_text = ft.Text(
            "",
            color="red"
        )

        # =====================================================
        # STEPS
        # =====================================================
        step1 = ft.Column(
            [
                username_input
            ],
            spacing=10
        )

        step2 = ft.Column(
            [
                question_text,
                answer_input
            ],

            spacing=10,

            visible=False
        )

        step3 = ft.Column(
            [
                new_pass_row,
                confirm_pass_row
            ],

            spacing=10,

            visible=False
        )

        current_step = 1

        # =====================================================
        # NEXT STEP
        # =====================================================
        def next_step(ev):

            nonlocal current_step

            # =================================================
            # STEP 1
            # =================================================
            if current_step == 1:

                username = username_input.value.strip()

                if not username:

                    status_text.value = (
                        "Ingrese un usuario"
                    )

                    self.page.update()

                    return

                question = get_user_question(username)

                if not question:

                    status_text.value = (
                        "Usuario no encontrado"
                    )

                    self.page.update()

                    return

                question_text.value = (
                    f"Pregunta de seguridad:\n{question}"
                )

                step1.visible = False
                step2.visible = True

                current_step = 2

                status_text.value = ""

                self.page.update()

            # =================================================
            # STEP 2
            # =================================================
            elif current_step == 2:

                username = username_input.value.strip()

                answer = answer_input.value.strip()

                if not answer:

                    status_text.value = (
                        "Responda la pregunta"
                    )

                    self.page.update()

                    return

                conn = connect_db_seguridad()

                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT security_answer
                    FROM users
                    WHERE username = %s
                    """,
                    (username,)
                )

                result = cursor.fetchone()

                conn.close()

                if (
                    result
                    and bcrypt.checkpw(
                        answer.lower().encode("utf-8"),
                        result[0].encode("utf-8")
                    )
                ):

                    step2.visible = False
                    step3.visible = True

                    current_step = 3

                    status_text.value = ""

                    self.page.update()

                else:

                    status_text.value = (
                        "Respuesta incorrecta"
                    )

                    self.page.update()

            # =================================================
            # STEP 3
            # =================================================
            elif current_step == 3:

                new_pass = new_pass_field.value

                confirm_pass = confirm_pass_field.value

                if not new_pass or not confirm_pass:

                    status_text.value = (
                        "Complete todos los campos"
                    )

                    self.page.update()

                    return

                if new_pass != confirm_pass:

                    status_text.value = (
                        "Las contraseñas no coinciden"
                    )

                    self.page.update()

                    return

                valido, mensaje = validar_password(
                    new_pass
                )

                if not valido:

                    status_text.value = mensaje

                    self.page.update()

                    return

                username = username_input.value.strip()

                success, mensaje = (
                    verify_and_reset_password(
                        username,
                        answer_input.value.strip(),
                        new_pass
                    )
                )

                if success:

                    dialog.open = False

                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            "Contraseña actualizada"
                        ),

                        bgcolor="green"
                    )

                    self.page.snack_bar.open = True

                    self.page.update()

                else:

                    status_text.value = mensaje

                    self.page.update()

        # =====================================================
        # CLOSE
        # =====================================================
        def close_dialog(ev):

            dialog.open = False

            self.page.update()

        # =====================================================
        # DIALOG
        # =====================================================
        dialog = ft.AlertDialog(

            title=ft.Text(
                "Recuperar contraseña"
            ),

            content=ft.Container(

                width=400,

                padding=10,

                content=ft.Column(
                    [
                        step1,
                        step2,
                        step3,
                        status_text
                    ],

                    spacing=15,

                    tight=True
                )
            ),

            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=close_dialog
                ),

                ft.TextButton(
                    "Siguiente",
                    on_click=next_step
                )
            ],

            actions_alignment=ft.MainAxisAlignment.END
        )

        # =====================================================
        # NAVEGACIÓN RECOVERY
        # =====================================================
        self.navigator.set_controls(
            [
                username_input,
                answer_input,
                new_pass_field,
                confirm_pass_field
            ]
        )

        self.page.dialog = dialog

        dialog.open = True

        self.page.update()


# =============================================================
# MAIN
# =============================================================
def main(page: ft.Page):

    App(page)


if __name__ == "__main__":
    ft.app(target=main)