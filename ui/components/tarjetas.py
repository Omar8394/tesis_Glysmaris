"""
============================================================
Sistema La Dulce Tía

Archivo:
    tarjetas.py

Responsabilidad:
    Biblioteca oficial de tarjetas reutilizables.

Contiene:
    - _TarjetaBase
    - TarjetaFormulario
    - TarjetaResumen
    - TarjetaHistorial
    - TarjetaInformacion
    - TarjetaAdvertencia
    - TarjetaEstadistica
    - TarjetaAccion

Arquitectura:
    Todas las tarjetas heredan de _TarjetaBase.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.core.radius import AppRadius
from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography

class _TarjetaBase(ft.Container):
    """
    Clase base para todas las tarjetas del sistema.

    Implementa automáticamente:

        • Icono
        • Título
        • Subtítulo
        • Acciones
        • Contenido
        • Pie

    Las clases derivadas únicamente deberán modificar
    apariencia o comportamiento.
    """

    def __init__(

        self,

        titulo: str = "",

        subtitulo: str = "",

        icono=None,

        acciones=None,

        contenido=None,

        pie=None,

        bgcolor=None,

        border_color=None,

        expand=False,

        width=None,

        height=None,

    ):

        self.tema = ThemeManager.theme

        self._titulo = titulo

        self._subtitulo = subtitulo

        self._icono = icono

        self._acciones = acciones or []

        self._contenido = contenido or []

        self._pie = pie

        super().__init__(

            expand=expand,

            width=width,

            height=height,

            bgcolor=bgcolor or self.tema.card,

            border=ft.border.all(

                1,

                border_color or self.tema.border,

            ),

            border_radius=AppRadius.CARD,

            padding=AppSpacing.CARD_PADDING,

        )

        self.content = self._crear_layout()

    # =====================================================
    # CONSTRUCCIÓN
    # =====================================================

    def _crear_layout(self):

        return ft.Column(

            controls=[

                self._crear_header(),

                self._crear_body(),

                self._crear_footer(),

            ],

            spacing=AppSpacing.SECTION_SPACING,

            expand=True,

        )
    # =====================================================
    # HEADER
    # =====================================================

    def _crear_header(self):

        controles_izquierda = []

        if self._icono:

            controles_izquierda.append(

                ft.Icon(

                    self._icono,

                    size=26,

                    color=self.tema.primary,

                )

            )

        textos = []

        if self._titulo:

            textos.append(

                ft.Text(

                    self._titulo,

                    size=AppTypography.SECTION_TITLE,

                    weight=AppTypography.BOLD,

                    color=self.tema.primary,

                )

            )

        if self._subtitulo:

            textos.append(

                ft.Text(

                    self._subtitulo,

                    size=AppTypography.SMALL,

                    color=self.tema.text_secondary,

                )

            )

        controles_izquierda.append(

            ft.Column(

                textos,

                spacing=2,

            )

        )

        return ft.Column(

            [

                ft.Row(

                    [

                        ft.Row(

                            controles_izquierda,

                            spacing=12,

                            expand=True,

                        ),

                        ft.Row(

                            self._acciones,

                            spacing=8,

                        ),

                    ]

                ),

                ft.Divider(),

            ],

            spacing=8,

        )
    #=======================================
    # BODY
    #=======================================

    def _crear_body(self):

        if isinstance(

            self._contenido,

            list,

        ):

            contenido = ft.Column(

                self._contenido,

                spacing=AppSpacing.CONTROL_SPACING,

            )

        else:

            contenido = self._contenido

        return contenido
    
    #=================================
    # FOOTER
    #=================================

    def _crear_footer(self):

        if self._pie is None:

            return ft.Container()

        return ft.Column(

            [

                ft.Divider(),

                self._pie,

            ],

            spacing=8,

        )
    
    #===============================
    # TARJETAS
    #===============================

class TarjetaFormulario(_TarjetaBase):
    """
    Tarjeta utilizada para agrupar controles de captura
    de información.

    Es la tarjeta más utilizada del sistema.
    """

    def __init__(
        self,
        titulo: str,
        contenido,
        subtitulo: str = "",
        icono=None,
        acciones=None,
        pie=None,
        expand=True,
        width= None,
        height=None,
    ):

        super().__init__(

            titulo=titulo,

            subtitulo=subtitulo,

            icono=icono,

            acciones=acciones,

            contenido=contenido,

            pie=pie,

            expand=expand,
            
            width=width,
            height=height,

        )

class TarjetaResumen(_TarjetaBase):
    """
    Tarjeta para mostrar indicadores y resúmenes.
    """

    def __init__(

        self,

        titulo: str,

        valor,

        descripcion: str = "",

        icono=None,

        color=None,

        width=260,

    ):

        tema = ThemeManager.theme

        contenido = [

            ft.Text(

                str(valor),

                size=30,

                weight=AppTypography.BOLD,

                color=color or tema.primary,

            )

        ]

        if descripcion:

            contenido.append(

                ft.Text(

                    descripcion,

                    size=AppTypography.SMALL,

                    color=tema.text_secondary,

                )

            )

        super().__init__(

            titulo=titulo,

            icono=icono,

            contenido=contenido,

            width=width,

        )

class TarjetaHistorial(_TarjetaBase):
    """
    Tarjeta destinada a mostrar historial o tablas.
    """

    def __init__(

        self,

        contenido,

        titulo="Historial",

        subtitulo="",

        icono=None,

        acciones=None,

        expand=True,

    ):

        super().__init__(

            titulo=titulo,

            subtitulo=subtitulo,

            icono=icono,

            acciones=acciones,

            contenido=contenido,

            expand=expand,

        )

class TarjetaInformacion(_TarjetaBase):
    """
    Tarjeta utilizada para mostrar información al usuario.
    """

    def __init__(

        self,

        mensaje,

        titulo="Información",

        icono=None,

        expand=False,

    ):

        tema = ThemeManager.theme

        contenido = [

            ft.Text(

                mensaje,

                size=AppTypography.BODY,

                color=tema.text,

            )

        ]

        super().__init__(

            titulo=titulo,

            icono=icono,

            contenido=contenido,

            expand=expand,

            bgcolor=tema.info + "15",

            border_color=tema.info,

        )

class TarjetaAdvertencia(_TarjetaBase):
    """
    Tarjeta para mostrar advertencias importantes.
    """

    def __init__(

        self,

        mensaje,

        titulo="Advertencia",

        icono=None,

        expand=False,

    ):

        tema = ThemeManager.theme

        contenido = [

            ft.Text(

                mensaje,

                size=AppTypography.BODY,

                color=tema.text,

            )

        ]

        super().__init__(

            titulo=titulo,

            icono=icono,

            contenido=contenido,

            expand=expand,

            bgcolor=tema.warning + "15",

            border_color=tema.warning,

        )
class TarjetaEstadistica(_TarjetaBase):
    """
    Tarjeta para indicadores del Dashboard.
    """

    def __init__(

        self,

        titulo,

        valor,

        porcentaje=None,

        icono=None,

        color=None,

        width=280,

    ):

        tema = ThemeManager.theme

        controles = [

            ft.Text(

                str(valor),

                size=32,

                weight=AppTypography.EXTRA_BOLD,

                color=color or tema.primary,

            )

        ]

        if porcentaje is not None:

            signo = "+" if porcentaje >= 0 else ""

            controles.append(

                ft.Text(

                    f"{signo}{porcentaje}%",

                    color=tema.success if porcentaje >= 0 else tema.error,

                    size=AppTypography.BODY,

                    weight=AppTypography.BOLD,

                )

            )

        super().__init__(

            titulo=titulo,

            icono=icono,

            contenido=controles,

            width=width,

        )

class TarjetaAccion(_TarjetaBase):
    """
    Tarjeta utilizada para agrupar acciones del usuario.
    """

    def __init__(

        self,

        titulo,

        botones,

        icono=None,

        subtitulo="",

        expand=False,

    ):

        contenido = [

            ft.Row(

                botones,

                wrap=True,

                spacing=AppSpacing.BUTTON_SPACING,

            )

        ]

        super().__init__(

            titulo=titulo,

            subtitulo=subtitulo,

            icono=icono,

            contenido=contenido,

            expand=expand,

        )
