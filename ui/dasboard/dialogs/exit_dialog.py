import flet as ft


def salir_app(page: ft.Page):

    def cerrar(e):

        page.window_close()

    def cerrar_dialog(e):

        dialog.open = False

        page.update()

    dialog = ft.AlertDialog(

        title=ft.Text("Salir"),

        content=ft.Text(
            "¿Seguro que quieres salir?"
        ),

        actions=[

            ft.TextButton(
                "Cancelar",
                on_click=cerrar_dialog
            ),

            ft.TextButton(
                "Salir",
                on_click=cerrar
            ),
        ]
    )

    page.dialog = dialog

    dialog.open = True

    page.update()