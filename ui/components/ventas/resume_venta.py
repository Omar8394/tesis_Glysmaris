import flet as ft
from ui.core.typography import AppTypography

class ResumenVenta(ft.Column):
    def __init__(self, total=0, descuento=0):
        super().__init__(spacing=2)
        self.total = total
        self.descuento = descuento

        self.txt_total = ft.Text(f"Total: ${total:.2f}", weight="bold", size=AppTypography.SECTION_TITLE)
        self.txt_descuento = ft.Text(f"Descuento: ${descuento:.2f}", size=AppTypography.BODY)

        self.controls = [
            ft.Row([ft.Text("Resumen", weight="bold"), ft.Container(expand=True), self.txt_total]),
            ft.Row([self.txt_descuento], alignment=ft.MainAxisAlignment.END),
        ]

    def actualizar(self, total, descuento):
        self.total = total
        self.descuento = descuento
        self.txt_total.value = f"Total: ${total:.2f}"
        self.txt_descuento.value = f"Descuento: ${descuento:.2f}"
        self.update()