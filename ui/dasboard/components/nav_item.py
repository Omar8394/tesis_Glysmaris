import flet as ft

from ui.dasboard.components.hover_effect import handle_hover


def create_nav_item(text,
                    icon,
                    on_click=None):

        btn = ft.Container(

            ink=True,

            content=ft.Row(
                [
                    ft.Icon(
                        icon,
                        color="white54",
                        size=22
                    ),

                    ft.Text(
                        text,
                        color="white54",
                        size=14
                    ),
                ]
            ),

            padding=12,

            border_radius=10,

            on_hover=handle_hover,

            on_click=on_click
        )

        return btn