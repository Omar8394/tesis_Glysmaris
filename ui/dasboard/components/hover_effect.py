import flet as ft

def handle_hover(e):

    is_hover = e.data == "true"

    e.control.bgcolor = (
        "white10"
        if is_hover
        else None
    )

    icon = e.control.content.controls[0]
    text = e.control.content.controls[1]

    icon.color = (
        "white"
        if is_hover
        else "white54"
    )

    text.color = (
        "white"
        if is_hover
        else "white54"
    )

    e.control.update()
