"""
============================================================
Sistema La Dulce Tía

Archivo:
    login_module.py

Responsabilidad:
    Coordinador del módulo de inicio de sesión.

    Ensambla el layout de login y maneja la autenticación.
    No contiene lógica de negocio, solo coordinación.
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.boton import BotonPrimario, BotonEnlace
from ui.components.dialogo import Dialogo
from ui.components.campo_texto import CampoTexto
from ui.components.mensajes import MensajeSistema
from ui.components.tarjetas import TarjetaFormulario
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing
from ui.core.sizes import AppSize
from ui.core.theme_manager import ThemeManager
from ui.layouts.login_layout import LoginLayout
from ui.modules.base.module import Module


class LoginModule(Module):
    """
    Módulo de inicio de sesión.

    Coordina:
        - Captura de usuario y contraseña.
        - Llamada al servicio de autenticación.
        - Navegación al dashboard en caso de éxito.
    """

    def __init__(
        self,
        page: ft.Page,
        auth_service,
        on_login_success,
        usuario=None,
    ):
        """
        Inicializa el módulo de login.

        Args:
            page: Página de Flet.
            auth_service: Servicio de autenticación.
            on_login_success: Callback al hacer login exitoso (recibe role).
            usuario: Usuario actual (None para login).
        """
        super().__init__(page, usuario)
        self.auth_service = auth_service
        self.on_login_success = on_login_success

        # Componentes del formulario
        self.campo_usuario = CampoTexto(
            etiqueta="Usuario",
            icono=AppIcons.USER,
            width=AppSize.FIELD_LARGE,
        )
        self.campo_password = CampoTexto(
            etiqueta="Contraseña",
            icono=AppIcons.LOGIN,
            password=True,
            width=AppSize.FIELD_LARGE,
        )
        self.btn_ingresar = BotonPrimario(
            texto="Ingresar",
            icono=AppIcons.LOGIN,
            on_click=self._login,
            width=AppSize.FIELD_LARGE,
        )
        # ✅ Por ahora solo el botón + un stub: el flujo real de recuperación
        # (mostrar la pregunta de seguridad correcta del usuario, verificarla
        # y resetear la contraseña) se conecta en un paso siguiente, una vez
        # que se resuelva cómo auth_repository expone security_question.
        self.btn_olvido_password = BotonEnlace(
            texto="¿Olvidaste tu contraseña?",
            on_click=self._olvido_password,
        )

    # ============================================================
    # CONSTRUCCIÓN
    # ============================================================

    def construir(self) -> ft.Control:
        """
        Ensambla el layout de login y devuelve el control.
        """
        # Tarjeta que agrupa el formulario
        tarjeta = TarjetaFormulario(
            titulo="Iniciar Sesión",
            subtitulo="Sistema La Dulce Tía",
            icono=AppIcons.HOME,
            contenido=ft.Column(
                [
                    self.campo_usuario,
                    self.campo_password,
                    ft.Divider(height=10),
                    self.btn_ingresar,
                    self.btn_olvido_password,
                ],
                spacing=AppSpacing.CONTROL_SPACING,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=420,
            height=520,
            expand=False,
        )

        # Envolver en LoginLayout (centra y da fondo)
        layout = LoginLayout(
            formulario=tarjeta,
        )
        return layout

    # ============================================================
    # COORDINACIÓN
    # ============================================================

    def _login(self, e) -> None:
        """
        Captura credenciales, llama al servicio y maneja el resultado.
        """
        usuario = self.campo_usuario.value
        password = self.campo_password.value

        resultado = self.auth_service.login(usuario, password)

        if resultado.exito:
            self.on_login_success(resultado.datos["role"])
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _olvido_password(self, e) -> None:
        """Abre el diálogo de recuperación de 3 pasos. Siempre pide el
        usuario de cero dentro del diálogo (no se reutiliza lo que haya
        en self.campo_usuario), por seguridad."""
        Dialogo.recuperar_password(
            page=self.page,
            on_solicitar_pregunta=self._solicitar_pregunta,
            on_verificar_respuesta=self._verificar_respuesta,
            on_resetear=self._resetear_password,
        )

    def _solicitar_pregunta(self, username: str) -> tuple[bool, str]:
        """Traduce ServiceResult -> (ok, pregunta_o_error), que es lo que
        espera Dialogo.recuperar_password (que no conoce ServiceResult)."""
        resultado = self.auth_service.obtener_pregunta_seguridad(username)
        if resultado.exito:
            return True, resultado.datos["question"]
        return False, resultado.mensaje

    def _verificar_respuesta(self, username: str, respuesta: str) -> tuple[bool, str]:
        resultado = self.auth_service.verificar_respuesta_seguridad(username, respuesta)
        return resultado.exito, resultado.mensaje

    def _resetear_password(self, username: str, respuesta: str, nueva_password: str) -> tuple[bool, str]:
        resultado = self.auth_service.resetear_password(username, respuesta, nueva_password)
        return resultado.exito, resultado.mensaje

    # ============================================================
    # CICLO DE VIDA (sobrescritura opcional)
    # ============================================================

    def on_show(self) -> None:
        """Al mostrar, limpia campos y enfoca usuario."""
        self.campo_usuario.value = ""
        self.campo_password.value = ""
        self.campo_usuario.focus()
        self.actualizar()