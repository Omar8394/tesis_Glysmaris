import flet as ft



def create_security_question_dialog(
    page,
    random_question,
    on_save
):

    answer_field = ft.TextField(
        label="Respuesta",
        width=300
    )

    def guardar(e):

        respuesta = answer_field.value.strip()

        on_save(respuesta)

        dialog.open = False

        page.update()

    def cerrar(e):

        dialog.open = False

        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text(
            "Pregunta de seguridad"
        ),

        content=ft.Column(
            [
                ft.Text(
                    random_question,
                    size=16
                ),

                answer_field
            ],
            spacing=10,
            tight=True
        ),

        actions=[
            ft.TextButton(
                "Cancelar",
                on_click=cerrar
            ),

            ft.TextButton(
                "Guardar",
                on_click=guardar
            )
        ]
    )

    return dialog