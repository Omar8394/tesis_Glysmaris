"""
============================================================
Sistema La Dulce Tía

Archivo:
    dialogo_usuario.py

Responsabilidad:
    Diálogo (AlertDialog) para crear o editar un usuario del
    sistema: username, contraseña, rol y pregunta/respuesta
    de seguridad.

    Un mismo diálogo cubre ambos modos:
        - Crear: se pasa `usuario_existente=None`. Username,
          contraseña, pregunta y respuesta son obligatorios.
        - Editar: se pasa `usuario_existente={"username":..,
          "role":..}`. El username queda fijo (no se puede
          renombrar) y contraseña/respuesta son opcionales:
          si se dejan vacías, se conserva lo que ya había
          guardado (la respuesta actual está hasheada y no se
          puede mostrar).

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft


class DialogoUsuario:
    """Encapsula el AlertDialog de creación/edición de usuario."""

    ROLES = ["admin", "visitante"]

    def __init__(
        self,
        page: ft.Page,
        tema,
        preguntas: list[str],
        on_guardar,
        usuario_existente: dict | None = None,
    ):
        self.page = page
        self.tema = tema
        self.on_guardar = on_guardar
        self.usuario_existente = usuario_existente
        self.es_edicion = usuario_existente is not None

        username_actual = usuario_existente["username"] if self.es_edicion else ""
        role_actual = usuario_existente["role"] if self.es_edicion else "visitante"

        self.txt_username = ft.TextField(
            label="Nombre de usuario",
            value=username_actual,
            autofocus=not self.es_edicion,
            max_length=50,
            disabled=self.es_edicion,
        )
        self.txt_password = ft.TextField(
            label="Contraseña" if not self.es_edicion else "Nueva contraseña",
            password=True,
            can_reveal_password=True,
            autofocus=self.es_edicion,
            helper_text=(
                "Mínimo 6 caracteres, una mayúscula y un número"
                if not self.es_edicion
                else "Dejar en blanco para no cambiarla"
            ),
        )
        self.dd_rol = ft.Dropdown(
            label="Rol",
            options=[ft.dropdown.Option(r) for r in self.ROLES],
            value=role_actual,
            # No se permite bajarle el rol al admin desde acá; el
            # servicio también lo valida, esto es solo UX.
            disabled=(username_actual == "admin"),
        )
        self.dd_pregunta = ft.Dropdown(
            label="Pregunta de seguridad",
            options=[ft.dropdown.Option(p) for p in preguntas],
            value=preguntas[0] if preguntas else None,
        )
        self.txt_respuesta = ft.TextField(
            label="Respuesta de seguridad",
            helper_text="Dejar en blanco para no cambiarla" if self.es_edicion else None,
        )
        self.txt_error = ft.Text(
            value="",
            color=ft.colors.RED,
            visible=False,
        )

        self.control = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar usuario" if self.es_edicion else "Nuevo usuario"),
            content=ft.Container(
                width=380,
                content=ft.Column(
                    controls=[
                        self.txt_username,
                        self.txt_password,
                        self.dd_rol,
                        self.dd_pregunta,
                        self.txt_respuesta,
                        self.txt_error,
                    ],
                    tight=True,
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cerrar),
                ft.FilledButton("Guardar", on_click=self._guardar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _cerrar(self, e=None):
        self.control.open = False
        self.page.update()

    def _mostrar_error(self, mensaje: str):
        self.txt_error.value = mensaje
        self.txt_error.visible = True
        self.control.update()

    def _guardar(self, e=None):
        self.txt_error.visible = False

        username = (self.txt_username.value or "").strip()
        password = self.txt_password.value or ""
        role = self.dd_rol.value
        question = self.dd_pregunta.value
        answer = (self.txt_respuesta.value or "").strip()

        if not question:
            self._mostrar_error("Seleccione una pregunta de seguridad.")
            return

        if self.es_edicion:
            resultado = self.on_guardar(
                username=username,
                password=password,  # puede venir vacío -> no se cambia
                role=role,
                question=question,
                answer=answer,       # puede venir vacío -> no se cambia
            )
        else:
            if not answer:
                self._mostrar_error("Ingrese la respuesta de seguridad.")
                return
            resultado = self.on_guardar(
                username=username,
                password=password,
                role=role,
                question=question,
                answer=answer,
            )

        # on_guardar devuelve un ServiceResult; si falló, mostramos el
        # error dentro del propio diálogo en vez de cerrarlo.
        if resultado is not None and getattr(resultado, "fallo", False):
            self._mostrar_error(resultado.mensaje)
            return

        self._cerrar()