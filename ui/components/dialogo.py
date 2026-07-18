"""
============================================================
Sistema La Dulce Tía

Archivo:
    dialogo.py

Responsabilidad:
    Biblioteca oficial de diálogos reutilizables.

Contiene:
    - _DialogoBase
    - Dialogo

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.boton import (
    BotonPrimario,
    BotonSecundario,
)

from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing
from ui.core.radius import AppRadius
from ui.components.campo_texto import CampoTexto

class _DialogoBase:
    """
    Clase base para todos los diálogos del sistema.

    Encapsula la creación, apertura y cierre de un
    AlertDialog utilizando el estilo oficial del sistema.
    """

    def __init__(

        self,

        page: ft.Page,

        titulo: str,

        contenido,

        icono=None,

        acciones=None,

        modal=True,

    ):

        self.page = page

        self.tema = ThemeManager.theme

        acciones = acciones or []

        encabezado = ft.Row(

            [

                ft.Icon(

                    icono,

                    color=self.tema.primary,

                    size=28,

                ) if icono else ft.Container(),

                ft.Text(

                    titulo,

                    size=AppTypography.SECTION_TITLE,

                    weight=AppTypography.BOLD,

                ),

            ],

            spacing=12,

        )

        self.dialogo = ft.AlertDialog(

            modal=modal,

            bgcolor=self.tema.card,

            shape=ft.RoundedRectangleBorder(

                radius=AppRadius.DIALOG,

            ),

            title=encabezado,

            content=contenido,

            actions=acciones,

            actions_alignment=ft.MainAxisAlignment.END,

        )
    def abrir(self):

        self.page.dialog = self.dialogo

        self.dialogo.open = True

        self.page.update()

    def cerrar(self, e=None):

        self.dialogo.open = False

        self.page.update()

class Dialogo:
    """
    Punto de acceso oficial para los diálogos del sistema.
    """

    @staticmethod
    def informacion(

        page,

        mensaje,

        titulo="Información",

    ):

        contenido = ft.Container(

            content=ft.Text(

                mensaje,

                size=AppTypography.BODY,

            ),

            width=420,

            padding=10,

        )

        dialogo = _DialogoBase(

            page=page,

            titulo=titulo,

            icono=ft.icons.INFO,

            contenido=contenido,

            acciones=[],

        )

        boton = BotonPrimario(

            texto="Aceptar",

            icono=ft.icons.CHECK,

            on_click=dialogo.cerrar,

        )

        dialogo.dialogo.actions = [boton]

        dialogo.abrir()

    @staticmethod
    def error(

        page,

        mensaje,

        titulo="Error",

    ):

        contenido = ft.Container(

            content=ft.Text(

                mensaje,

                size=AppTypography.BODY,

                color=ThemeManager.theme.error,

            ),

            width=420,

            padding=10,

        )

        dialogo = _DialogoBase(

            page=page,

            titulo=titulo,

            icono=ft.icons.ERROR,

            contenido=contenido,

        )

        boton = BotonPrimario(

            texto="Cerrar",

            icono=ft.icons.CLOSE,

            on_click=dialogo.cerrar,

        )

        dialogo.dialogo.actions = [boton]

        dialogo.abrir()

    @staticmethod
    def advertencia(

        page,

        mensaje,

        titulo="Advertencia",

    ):

        contenido = ft.Container(

            content=ft.Text(

                mensaje,

                size=AppTypography.BODY,

            ),

            width=420,

            padding=10,

        )

        dialogo = _DialogoBase(

            page=page,

            titulo=titulo,

            icono=ft.icons.WARNING,

            contenido=contenido,

        )

        boton = BotonSecundario(

            texto="Entendido",

            icono=ft.icons.CHECK,

            on_click=dialogo.cerrar,

        )

        dialogo.dialogo.actions = [boton]

        dialogo.abrir()

    @staticmethod
    def confirmacion(
        page,
        mensaje,
        on_confirmar,
        titulo="Confirmación",
        texto_confirmar="Aceptar",
        texto_cancelar="Cancelar",
    ):

        contenido = ft.Container(

            content=ft.Text(

                mensaje,

                size=AppTypography.BODY,

            ),

            width=450,

            padding=10,

        )

        dialogo = _DialogoBase(

            page=page,

            titulo=titulo,

            icono=ft.icons.HELP,

            contenido=contenido,

        )

        def confirmar(e):

            dialogo.cerrar()

            if callable(on_confirmar):

                on_confirmar(e)

        btn_cancelar = BotonSecundario(

            texto=texto_cancelar,

            icono=ft.icons.CLOSE,

            on_click=dialogo.cerrar,

        )

        btn_confirmar = BotonPrimario(

            texto=texto_confirmar,

            icono=ft.icons.CHECK,

            on_click=confirmar,

        )

        dialogo.dialogo.actions = [

            btn_cancelar,

            btn_confirmar,

        ]

        dialogo.abrir()

    @staticmethod
    def personalizado(

        page,

        titulo,

        contenido,

        acciones=None,

        icono=None,

        ancho=650,

        modal=True,

    ):

        cuerpo = ft.Container(

            content=contenido,

            width=ancho,

            padding=10,

        )

        dialogo = _DialogoBase(

            page=page,

            titulo=titulo,

            icono=icono,

            contenido=cuerpo,

            acciones=acciones or [],

            modal=modal,

        )

        dialogo.abrir()

        return dialogo

    @staticmethod
    def preguntar(

        page,

        pregunta,

        aceptar,

    ):

        Dialogo.confirmacion(

            page=page,

            titulo="Confirmación",

            mensaje=pregunta,

            on_confirmar=aceptar,

        )

    # ✅ Reemplazá el método 'eliminar_ingrediente' completo de tu clase
    # Dialogo por este. El resto del archivo (imports, _DialogoBase, etc.)
    # queda igual.
    @staticmethod
    def eliminar_ingrediente(
        page,
        nombre_ingrediente: str,
        cantidad_disponible: float,
        on_eliminar,
        titulo="Eliminar Ingrediente",
        texto_confirmar="Eliminar",
        texto_cancelar="Cancelar",
    ):
        """
        Diálogo para registrar una pérdida/merma de un lote: pide la
        cantidad (obligatoria, sin valor por defecto) y el motivo
        (selección única, vía RadioGroup).

        Args:
            page: Página de Flet.
            nombre_ingrediente: Nombre del ingrediente a eliminar.
            cantidad_disponible: Cantidad total disponible (para validar el máximo).
            on_eliminar: Callback que se ejecutará al confirmar.
                         Recibe (cantidad: float, motivo: str).
            titulo: Título del diálogo.
            texto_confirmar: Texto del botón de confirmación.
            texto_cancelar: Texto del botón de cancelar.
        """
        # --- Estado del diálogo ---
        cantidad_error = ft.Text("", color=ThemeManager.theme.error, size=12)
        motivo_error = ft.Text("", color=ThemeManager.theme.error, size=12)

        # ✅ Campo de cantidad: SIEMPRE arranca en "0" (inválido a propósito).
        # Antes se dejaba vacío o al máximo por defecto, y si el usuario
        # estaba distraído podía confirmar sin darse cuenta de que estaba
        # eliminando todo el lote. Ahora es obligatorio que el usuario
        # escriba (o use el botón de "lote completo") un valor > 0.
        campo_cantidad = ft.TextField(
            label="Cantidad a eliminar",
            value="0",
            hint_text=f"Máximo {cantidad_disponible}",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
            dense=True,
            on_change=lambda e: _validar_cantidad(),
        )

        def _usar_lote_completo(e):
            # ✅ Nuevo: botón explícito que autocompleta la cantidad con el
            # total disponible, en vez de dejar ese valor precargado por
            # defecto (que el usuario podía pasar por alto).
            campo_cantidad.value = str(cantidad_disponible)
            _validar_cantidad()
            page.update()

        btn_lote_completo = ft.TextButton(
            text="Usar cantidad total (eliminar lote completo)",
            icon=ft.icons.INVENTORY_2_OUTLINED,
            on_click=_usar_lote_completo,
        )

        # ✅ RadioGroup en vez de checkboxes: el motivo es de selección
        # única (antes se podían marcar varios a la vez, lo cual no
        # encaja con un ENUM de un solo valor en la base de datos).
        motivos_opciones = [
            "Caducado",
            "Deteriorado",
            "Error de inventario",
            "Otro",
        ]
        radio_motivos = ft.RadioGroup(
            content=ft.Column(
                [ft.Radio(value=m, label=m) for m in motivos_opciones],
                spacing=5,
            ),
        )

        # Campo "Otro" (texto) solo se muestra si se selecciona "Otro"
        otro_texto = ft.TextField(
            label="Especificar otro motivo",
            hint_text="Escriba el motivo...",
            width=300,
            dense=True,
            visible=False,
        )

        def on_motivo_change(e):
            otro_texto.visible = (radio_motivos.value == "Otro")
            motivo_error.value = ""
            page.update()

        radio_motivos.on_change = on_motivo_change

        # Función de validación interna
        def _validar_cantidad():
            try:
                val = float(campo_cantidad.value) if campo_cantidad.value else 0
                if val <= 0:
                    cantidad_error.value = "Ingrese una cantidad mayor a 0."
                elif val > cantidad_disponible:
                    cantidad_error.value = f"No puede eliminar más de {cantidad_disponible}."
                else:
                    cantidad_error.value = ""
            except ValueError:
                cantidad_error.value = "Cantidad inválida."
            page.update()

        def _validar_motivo():
            seleccionado = radio_motivos.value
            if not seleccionado:
                motivo_error.value = "Seleccione un motivo."
                return False, None
            if seleccionado == "Otro" and not otro_texto.value.strip():
                motivo_error.value = "Debe especificar el motivo en 'Otro'."
                return False, None
            motivo_error.value = ""
            if seleccionado == "Otro":
                return True, f"Otro: {otro_texto.value.strip()}"
            return True, seleccionado

        # Contenido del diálogo
        contenido = ft.Column(
            [
                ft.Text(
                    f"Ingrediente: {nombre_ingrediente}",
                    size=AppTypography.BODY,
                    weight=AppTypography.BOLD,
                ),
                ft.Text(
                    f"Cantidad disponible: {cantidad_disponible}",
                    size=AppTypography.BODY,
                ),
                ft.Divider(height=20),
                ft.Row(
                    [
                        campo_cantidad,
                        ft.Container(width=10),
                        ft.Column([cantidad_error], spacing=0),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                btn_lote_completo,
                ft.Text("Motivo de eliminación:", size=AppTypography.BODY),
                radio_motivos,
                otro_texto,
                ft.Container(
                    content=ft.Column([motivo_error], spacing=0),
                    padding=ft.padding.only(top=5),
                ),
            ],
            spacing=10,
            width=500,
        )

        # Acciones
        def on_confirmar(e):
            # Validar cantidad
            try:
                cantidad = float(campo_cantidad.value) if campo_cantidad.value else 0
            except ValueError:
                cantidad = 0
            if cantidad <= 0 or cantidad > cantidad_disponible:
                _validar_cantidad()
                page.update()
                return

            # Validar motivo (selección única)
            ok, motivo = _validar_motivo()
            if not ok:
                page.update()
                return

            # Cerrar diálogo y llamar callback
            dialogo.cerrar()
            if callable(on_eliminar):
                on_eliminar(cantidad, motivo)

        dialogo = _DialogoBase(
            page=page,
            titulo=titulo,
            icono=ft.icons.DELETE,
            contenido=contenido,
            acciones=[],
            modal=True,
        )

        btn_cancelar = BotonSecundario(
            texto=texto_cancelar,
            icono=ft.icons.CLOSE,
            on_click=dialogo.cerrar,
        )

        btn_confirmar = BotonPrimario(
            texto=texto_confirmar,
            icono=ft.icons.CHECK,
            on_click=on_confirmar,
        )

        dialogo.dialogo.actions = [
            btn_cancelar,
            btn_confirmar,
        ]

        dialogo.abrir()

    @staticmethod
    def recuperar_password(
        page,
        on_solicitar_pregunta,
        on_verificar_respuesta,
        on_resetear,
        titulo="Recuperar contraseña",
    ):
        """
        Diálogo de recuperación de contraseña en 3 pasos:
            1) Usuario -> pide la pregunta de seguridad.
            2) Respuesta a la pregunta -> se verifica.
            3) Nueva contraseña (+confirmación) -> se guarda.

        Por diseño, SIEMPRE se pide el usuario de cero en este diálogo
        (no se reutiliza lo que haya escrito en la pantalla de login).

        Args (los tres son callables desacoplados de cualquier service
        concreto — este diálogo no conoce AuthService ni ServiceResult):
            on_solicitar_pregunta(username) -> (ok: bool, pregunta_o_error: str)
            on_verificar_respuesta(username, respuesta) -> (ok: bool, mensaje_error: str)
            on_resetear(username, respuesta, nueva_password) -> (ok: bool, mensaje: str)
        """
        # --- Estado del flujo (mutable, compartido por los closures) ---
        estado = {"paso": 1, "username": "", "pregunta": "", "respuesta": ""}

        # --- Controles de cada paso (se crean una sola vez, se reutilizan) ---
        # ✅ CampoTexto en vez de ft.TextField crudo: es el componente oficial
        # del sistema para campos de texto, y ya trae su propio error_text
        # (no hace falta un ft.Text de error aparte por cada campo).
        campo_usuario = CampoTexto(etiqueta="Usuario", width=320)
        texto_pregunta = ft.Text("", size=AppTypography.BODY, weight=AppTypography.BOLD)
        campo_respuesta = CampoTexto(etiqueta="Respuesta", width=320)
        campo_password_nueva = CampoTexto(etiqueta="Nueva contraseña", password=True, width=320)
        campo_password_confirmar = CampoTexto(etiqueta="Confirmar contraseña", password=True, width=320)

        contenido_dinamico = ft.Column(spacing=10, width=380)

        def _mostrar_paso_1():
            campo_usuario.error_text = None
            contenido_dinamico.controls = [
                ft.Text("Ingresá tu usuario para comenzar.", size=AppTypography.BODY),
                campo_usuario,
            ]

        def _mostrar_paso_2():
            campo_respuesta.error_text = None
            contenido_dinamico.controls = [
                ft.Text("Pregunta de seguridad:", size=AppTypography.BODY),
                texto_pregunta,
                campo_respuesta,
            ]

        def _mostrar_paso_3():
            campo_password_nueva.error_text = None
            campo_password_confirmar.error_text = None
            contenido_dinamico.controls = [
                ft.Text("Elegí tu nueva contraseña.", size=AppTypography.BODY),
                campo_password_nueva,
                campo_password_confirmar,
            ]

        def _renderizar(paso):
            estado["paso"] = paso
            if paso == 1:
                _mostrar_paso_1()
            elif paso == 2:
                _mostrar_paso_2()
            else:
                _mostrar_paso_3()
            dialogo.dialogo.actions = _acciones_para_paso(paso)
            page.update()

        def _volver(e=None):
            _renderizar(estado["paso"] - 1)

        def _siguiente_desde_1(e=None):
            username = campo_usuario.value.strip() if campo_usuario.value else ""
            if not username:
                campo_usuario.error_text = "Ingrese su usuario."
                page.update()
                return
            ok, pregunta_o_error = on_solicitar_pregunta(username)
            if not ok:
                campo_usuario.error_text = pregunta_o_error
                page.update()
                return
            estado["username"] = username
            estado["pregunta"] = pregunta_o_error
            texto_pregunta.value = pregunta_o_error
            campo_respuesta.value = ""
            _renderizar(2)

        def _siguiente_desde_2(e=None):
            respuesta = campo_respuesta.value.strip() if campo_respuesta.value else ""
            if not respuesta:
                campo_respuesta.error_text = "Ingrese una respuesta."
                page.update()
                return
            ok, mensaje = on_verificar_respuesta(estado["username"], respuesta)
            if not ok:
                campo_respuesta.error_text = mensaje
                page.update()
                return
            estado["respuesta"] = respuesta
            campo_password_nueva.value = ""
            campo_password_confirmar.value = ""
            _renderizar(3)

        def _guardar_desde_3(e=None):
            nueva = campo_password_nueva.value or ""
            confirmar = campo_password_confirmar.value or ""
            if nueva != confirmar:
                campo_password_confirmar.error_text = "Las contraseñas no coinciden."
                page.update()
                return
            ok, mensaje = on_resetear(estado["username"], estado["respuesta"], nueva)
            if not ok:
                campo_password_confirmar.error_text = mensaje
                page.update()
                return
            dialogo.cerrar()
            Dialogo.informacion(page, mensaje or "Contraseña actualizada correctamente.")

        def _acciones_para_paso(paso):
            btn_cancelar = BotonSecundario(
                texto="Cancelar", icono=ft.icons.CLOSE, on_click=dialogo.cerrar,
            )
            if paso == 1:
                return [
                    btn_cancelar,
                    BotonPrimario(texto="Siguiente", icono=ft.icons.ARROW_FORWARD, on_click=_siguiente_desde_1),
                ]
            if paso == 2:
                return [
                    btn_cancelar,
                    BotonSecundario(texto="Volver", icono=ft.icons.ARROW_BACK, on_click=_volver),
                    BotonPrimario(texto="Verificar", icono=ft.icons.CHECK, on_click=_siguiente_desde_2),
                ]
            return [
                btn_cancelar,
                BotonSecundario(texto="Volver", icono=ft.icons.ARROW_BACK, on_click=_volver),
                BotonPrimario(texto="Guardar", icono=ft.icons.SAVE, on_click=_guardar_desde_3),
            ]

        # ✅ Orden correcto: primero se puebla el contenido del paso 1...
        _mostrar_paso_1()

        # ...y RECIÉN ACÁ se crea el diálogo, ya con ese contenido y esas
        # acciones listos. Crearlo antes (con contenido vacío y acciones=[])
        # es exactamente lo que hacía que se viera "abierto pero sin nada".
        dialogo = _DialogoBase(
        page=page,
        titulo=titulo,
        icono=ft.icons.LOCK_RESET,
        contenido=contenido_dinamico,
        acciones=[],
        modal=True,
    )
        dialogo.dialogo.actions = _acciones_para_paso(1)

        dialogo.abrir()