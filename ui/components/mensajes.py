"""
============================================================
Sistema La Dulce Tía

Archivo:
    mensajes.py

Responsabilidad:
    Mostrar mensajes del sistema.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

import flet as ft

from ui.core.theme_manager import ThemeManager

class MensajeSistema:
    """
    Muestra mensajes oficiales del sistema.
    """

    @staticmethod
    def _mostrar(

        page,

        mensaje,

        color,

        icono,

    ):

        page.snack_bar = ft.SnackBar(

            bgcolor=color,

            content=ft.Row(

                [

                    ft.Icon(

                        icono,

                        color="white",

                    ),

                    ft.Text(

                        mensaje,

                        color="white",

                        expand=True,

                    ),

                ],

                spacing=12,

            ),

            behavior=ft.SnackBarBehavior.FLOATING,

        )

        page.snack_bar.open = True

        page.update()

    @staticmethod
    def exito(page, mensaje):

        MensajeSistema._mostrar(

            page,

            mensaje,

            ThemeManager.theme.success,

            ft.icons.CHECK_CIRCLE,

        )

    @staticmethod
    def error(page, mensaje):

        MensajeSistema._mostrar(

            page,

            mensaje,

            ThemeManager.theme.error,

            ft.icons.ERROR,

        )

    @staticmethod
    def advertencia(page, mensaje):

        MensajeSistema._mostrar(

            page,

            mensaje,

            ThemeManager.theme.warning,

            ft.icons.WARNING,

        )

    @staticmethod
    def informacion(page, mensaje):

        MensajeSistema._mostrar(

            page,

            mensaje,

            ThemeManager.theme.info,

            ft.icons.INFO,

        )



