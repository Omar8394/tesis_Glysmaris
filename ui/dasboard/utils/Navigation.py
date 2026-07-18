import flet as ft


class KeyboardNavigator:

    def __init__(self, page: ft.Page):

        self.page = page

        self.focusable_controls = []

        self.focus_index = 0

    # =====================================
    # REGISTRAR CONTROLES
    # =====================================
    def set_controls(self, controls):
        self.focusable_controls = controls
        self.current_index = 0

        if self.focusable_controls:
            first = self.focusable_controls[0]

            if hasattr(first, "focus"):
                try:
                    first.focus()
                except:
                    pass

    # =====================================
    # OBTENER CONTROL ACTUAL
    # =====================================
    def get_current_control(self):

        if not self.focusable_controls:
            return None

        return self.focusable_controls[
            self.focus_index
        ]

    # =====================================
    # MOVER FOCO
    # =====================================
    def move_focus(self, direction):
        if not self.focusable_controls:
            return

        total = len(self.focusable_controls)

        for _ in range(total):
            self.current_index = (
                                         self.current_index + direction
                                 ) % total

            control = self.focusable_controls[
                self.current_index
            ]

            # Verificar si el control tiene focus()
            if hasattr(control, "focus"):
                try:
                    control.focus()
                    return
                except:
                    pass
    # =====================================
    # NAVEGACIÓN GENERAL
    # =====================================
    def handle_navigation(self, e: ft.KeyboardEvent):

        if e.key == "Arrow Down":
            self.move_focus(1)

        elif e.key == "Arrow Up":
            self.move_focus(-1)

    def trigger_current(self):

        current = self.get_current_control()

        if not current:
            return

    # BOTONES
        if hasattr(current, "on_click") and current.on_click:
            handler = getattr(current, "on_click", None)

            if callable(handler):
                handler(None)