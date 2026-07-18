"""
Panel de costos para recetas.
Solo muestra subtotal de ingredientes y precio sugerido.
"""

import flet as ft


class CostosPanel(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 10
        self.border = ft.border.all(1, "#2D3748")
        self.border_radius = 5

        self.txt_subtotal = ft.TextField(
            label="Subtotal ingredientes",
            read_only=True,
            value="$0.00",
            width=200,
        )
        self.txt_precio_sugerido = ft.TextField(
            label="Precio sugerido (x3)",
            read_only=True,
            value="$0.00",
            width=200,
        )

        self.content = ft.Column(
            [
                ft.Text("Resumen de costos", weight=ft.FontWeight.BOLD, size=14),
                ft.Row(
                    [self.txt_subtotal, self.txt_precio_sugerido],
                    spacing=20,
                ),
            ],
            spacing=10,
        )

    def actualizar(self, subtotal: float, sugerido: float):
        """Actualiza los valores mostrados."""
        self.txt_subtotal.value = f"${subtotal:.2f}"
        self.txt_precio_sugerido.value = f"${sugerido:.2f}"
        self.update()