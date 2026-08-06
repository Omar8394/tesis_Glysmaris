"""
============================================================
Sistema La Dulce Tía

Archivo:
    usuario_module.py

Responsabilidad:
    Módulo de gestión de usuarios del sistema:
        - Listar usuarios (username, rol)
        - Buscar por nombre de usuario
        - Crear un nuevo usuario (vía DialogoUsuario)
        - Editar rol/pregunta/respuesta/contraseña de un usuario
        - Eliminar un usuario (con confirmación; el admin
          está protegido por UsuarioService.eliminar_usuario)

Nota de arquitectura:
    Clase plana, igual que IngredienteModule / RecetasModule /
    ProductoModule. No hereda de la jerarquía Module base: esa
    jerarquía no se usa en ningún punto real del sistema (ver
    dashboard_module.py).

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import sys
import traceback

import flet as ft

from ui.core.services.factory import ServiceFactory
from ui.modules.seguridad.dialogo_usuario import DialogoUsuario


def _debug(msg: str) -> None:
    """Print de diagnóstico. Sacar una vez encontrado el problema."""
    print(f"[UsuarioModule] {msg}", flush=True)
    sys.stdout.flush()


class UsuarioModule:
    """Módulo de administración de usuarios."""

    def __init__(self, page: ft.Page, content_area: ft.Container):
        self.page = page
        self.content_area = content_area

        self.usuario_service = ServiceFactory.get_usuario_service()
        self.pregunta_service = ServiceFactory.get_pregunta_service()

        self._usuarios: list[dict] = []
        self._filtro_actual = ""

        self.buscador = ft.TextField(
            label="Buscar usuario...",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_change=self._on_buscar,
        )

        self.btn_nuevo = ft.FilledButton(
            text="Nuevo usuario",
            icon=ft.icons.PERSON_ADD,
            on_click=self._abrir_dialogo_nuevo,
        )

        self.tabla = ft.Column(
            spacing=4,
            controls=[],
        )

        self.txt_vacio = ft.Text(
            "No hay usuarios que coincidan con la búsqueda.",
            italic=True,
            visible=False,
        )

        self.view = None

    # ------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------

    def construir(self) -> ft.Control:
        self.view = ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Gestión de usuarios", size=22, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Row(
                    controls=[self.buscador, self.btn_nuevo],
                    spacing=12,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[self._encabezado_tabla(), ft.Divider(height=1), self.tabla, self.txt_vacio],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                ),
            ],
        )
        return self.view

    def cargar(self) -> None:
        """Recarga la lista de usuarios desde el servicio."""
        resultado = self.usuario_service.listar_usuarios()
        if resultado.fallo:
            self._mensaje(resultado.mensaje, error=True)
            self._usuarios = []
        else:
            self._usuarios = resultado.datos or []

        self._refrescar_tabla()

    # ------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------

    def _on_buscar(self, e):
        self._filtro_actual = (self.buscador.value or "").strip().lower()
        self._refrescar_tabla()

    def _usuarios_filtrados(self) -> list[dict]:
        if not self._filtro_actual:
            return self._usuarios
        return [
            u for u in self._usuarios
            if self._filtro_actual in u["username"].lower()
        ]

    # ------------------------------------------------------------
    # Tabla (armada a mano con Row/Container -- NO ft.DataTable,
    # porque en flet 22.1 el DataRow tapa los clics de los botones
    # que van adentro de sus celdas con su propia capa de gestos)
    # ------------------------------------------------------------

    def _encabezado_tabla(self) -> ft.Control:
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            content=ft.Row(
                controls=[
                    ft.Text("Usuario", weight=ft.FontWeight.BOLD, expand=2),
                    ft.Text("Rol", weight=ft.FontWeight.BOLD, expand=1),
                    ft.Text("Acciones", weight=ft.FontWeight.BOLD, expand=1, text_align=ft.TextAlign.RIGHT),
                ],
            ),
        )

    def _refrescar_tabla(self) -> None:
        filtrados = self._usuarios_filtrados()
        _debug(f"_refrescar_tabla(): {len(filtrados)} usuario(s) a mostrar")

        self.tabla.controls = [self._fila_usuario(u) for u in filtrados]
        self.tabla.visible = len(filtrados) > 0
        self.txt_vacio.visible = len(filtrados) == 0

        if self.view and self.view.page:
            _debug("_refrescar_tabla(): actualizando self.view (está en la página)")
            self.view.update()
        else:
            _debug(
                f"_refrescar_tabla(): NO se actualizó self.view "
                f"(self.view={self.view is not None}, self.view.page={getattr(self.view, 'page', 'N/A')})"
            )

    def _fila_usuario(self, usuario: dict) -> ft.Control:
        es_admin = usuario["username"] == "admin"
        _debug(f"Construyendo fila para '{usuario['username']}' (admin={es_admin})")

        def _click_editar(e, u=usuario):
            _debug(f"CLICK editar recibido para '{u['username']}'")
            try:
                self._abrir_dialogo_editar(u)
            except Exception:
                _debug("EXCEPCION en _abrir_dialogo_editar:")
                traceback.print_exc()

        def _click_eliminar(e, u=usuario["username"]):
            _debug(f"CLICK eliminar recibido para '{u}'")
            try:
                self._confirmar_eliminar(u)
            except Exception:
                _debug("EXCEPCION en _confirmar_eliminar:")
                traceback.print_exc()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
            content=ft.Row(
                controls=[
                    ft.Text(usuario["username"], expand=2),
                    ft.Text(usuario["role"], expand=1),
                    ft.Row(
                        expand=1,
                        alignment=ft.MainAxisAlignment.END,
                        spacing=0,
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.EDIT_OUTLINED,
                                tooltip="Editar usuario",
                                on_click=_click_editar,
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                tooltip="No se puede eliminar al administrador" if es_admin else "Eliminar usuario",
                                disabled=es_admin,
                                icon_color=ft.colors.RED if not es_admin else None,
                                on_click=_click_eliminar,
                            ),
                        ],
                    ),
                ],
            ),
        )

    # ------------------------------------------------------------
    # Crear / editar usuario
    # ------------------------------------------------------------

    def _obtener_preguntas(self) -> list[str] | None:
        try:
            resultado = self.pregunta_service.listar_preguntas()
        except Exception:
            _debug("_obtener_preguntas(): EXCEPCION llamando a pregunta_service.listar_preguntas:")
            traceback.print_exc()
            self._mensaje("Error inesperado al cargar preguntas de seguridad.", error=True)
            return None

        if resultado.fallo:
            self._mensaje(resultado.mensaje, error=True)
            return None

        preguntas = [p["question_text"] for p in resultado.datos]
        if not preguntas:
            self._mensaje("No hay preguntas de seguridad configuradas.", error=True)
            return None

        return preguntas

    def _abrir_dialogo_nuevo(self, e=None):
        preguntas = self._obtener_preguntas()
        if preguntas is None:
            return

        dialogo = DialogoUsuario(
            page=self.page,
            tema=None,
            preguntas=preguntas,
            on_guardar=self._on_guardar_nuevo,
        )
        self._abrir_dialogo(dialogo.control)

    def _abrir_dialogo_editar(self, usuario: dict):
        _debug(f"_abrir_dialogo_editar() para '{usuario.get('username')}'")
        preguntas = self._obtener_preguntas()
        _debug(f"_abrir_dialogo_editar(): preguntas obtenidas = {preguntas}")
        if preguntas is None:
            _debug("_abrir_dialogo_editar(): abortando, no hay preguntas")
            return

        dialogo = DialogoUsuario(
            page=self.page,
            tema=None,
            preguntas=preguntas,
            on_guardar=self._on_guardar_edicion,
            usuario_existente=usuario,
        )
        _debug("_abrir_dialogo_editar(): DialogoUsuario creado, abriendo...")
        self._abrir_dialogo(dialogo.control)
        _debug("_abrir_dialogo_editar(): _abrir_dialogo() retornó sin excepción")

    def _on_guardar_nuevo(self, username, password, role, question, answer):
        resultado = self.usuario_service.crear_usuario(
            username=username,
            password=password,
            role=role,
            question=question,
            answer=answer,
        )
        if not resultado.fallo:
            self._mensaje("Usuario creado exitosamente.")
            self.cargar()
        return resultado

    def _on_guardar_edicion(self, username, password, role, question, answer):
        resultado = self.usuario_service.actualizar_usuario(
            username=username,
            role=role,
            question=question,
            answer=answer,
            password=password,
        )
        if not resultado.fallo:
            self._mensaje("Usuario actualizado correctamente.")
            self.cargar()
        return resultado

    # ------------------------------------------------------------
    # Eliminar usuario
    # ------------------------------------------------------------

    def _confirmar_eliminar(self, username: str):
        _debug(f"_confirmar_eliminar() para '{username}'")

        def _cerrar(e=None):
            _debug("_confirmar_eliminar(): click en Cancelar")
            self._cerrar_dialogo(dialogo)

        def _eliminar(e=None):
            _debug(f"_confirmar_eliminar(): click en Eliminar para '{username}'")
            self._cerrar_dialogo(dialogo)
            try:
                resultado = self.usuario_service.eliminar_usuario(username)
                _debug(f"_confirmar_eliminar(): resultado.fallo={resultado.fallo}, mensaje={resultado.mensaje}")
            except Exception:
                _debug("_confirmar_eliminar(): EXCEPCION llamando a usuario_service.eliminar_usuario:")
                traceback.print_exc()
                return
            if resultado.fallo:
                self._mensaje(resultado.mensaje, error=True)
            else:
                self._mensaje(resultado.mensaje)
                self.cargar()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar usuario"),
            content=ft.Text(f"¿Seguro que querés eliminar al usuario '{username}'? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=_cerrar),
                ft.FilledButton(
                    "Eliminar",
                    style=ft.ButtonStyle(bgcolor=ft.colors.RED),
                    on_click=_eliminar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        _debug("_confirmar_eliminar(): AlertDialog creado, abriendo...")
        self._abrir_dialogo(dialogo)
        _debug("_confirmar_eliminar(): _abrir_dialogo() retornó sin excepción")

    # ------------------------------------------------------------
    # Diálogos y mensajes (API vieja de flet 22.1: no existen
    # page.open()/page.close(), hay que usar page.dialog + .open)
    # ------------------------------------------------------------

    def _abrir_dialogo(self, dialogo: ft.AlertDialog) -> None:
        _debug(f"_abrir_dialogo(): page={self.page!r}, page.update existe={hasattr(self.page, 'update')}")
        try:
            self.page.dialog = dialogo
            dialogo.open = True
            self.page.update()
            _debug(f"_abrir_dialogo(): OK, dialogo.open={dialogo.open}")
        except Exception:
            _debug("_abrir_dialogo(): EXCEPCION:")
            traceback.print_exc()

    def _cerrar_dialogo(self, dialogo: ft.AlertDialog) -> None:
        _debug("_cerrar_dialogo()")
        try:
            dialogo.open = False
            self.page.update()
        except Exception:
            _debug("_cerrar_dialogo(): EXCEPCION:")
            traceback.print_exc()

    def _mensaje(self, texto: str, error: bool = False) -> None:
        """
        Muestra un SnackBar simple. Se evita depender de MensajeSistema
        acá porque IngredienteModule y el resto de módulos "planos" no
        siempre lo usan de la misma forma; si tu proyecto ya tiene un
        helper común (como el `self.mensaje()` de Module), reemplazá
        este método por esa llamada.
        """
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(texto),
            bgcolor=ft.colors.RED if error else None,
            open=True,
        )
        self.page.update()