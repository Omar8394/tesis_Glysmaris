"""
Panel de costos para recetas.
Muestra el costo de materia prima (suma de ingredientes según la
cantidad utilizada).

Antes también mostraba un "Precio sugerido (x3)" -- un campo de solo
lectura que multiplicaba el subtotal por un margen fijo de 3. Ese
cálculo ya no se usa en ningún lado del flujo de recetas (el módulo
solo pasa el costo de ingredientes), así que el campo era código
muerto: se eliminó junto con el segundo parámetro de `actualizar()`.
"""

import flet as ft


class CostosPanel(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 10
        self.border = ft.border.all(1, "#2D3748")
        self.border_radius = 5

        self.txt_subtotal = ft.TextField(
            label="Costo materia prima",
            read_only=True,
            value="$0.00",
            width=200,
        )

        self.content = ft.Column(
            [
                ft.Text("Resumen de costos", weight=ft.FontWeight.BOLD, size=14),
                self.txt_subtotal,
            ],
            spacing=10,
        )

    def actualizar(self, costo_ingredientes: float):
        """Actualiza el costo de materia prima mostrado."""
        self.txt_subtotal.value = f"${costo_ingredientes:.2f}"
        self.update()