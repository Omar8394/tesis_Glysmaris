import flet as ft

class ResumenVenta(ft.Container):
    def __init__(self, total=0, descuento=0):
        self.total = total
        self.descuento = descuento

        self.txt_subtotal = ft.Text(f"${total:.2f}", weight="w500")
        self.txt_descuento = ft.Text(f"-${descuento:.2f}", color="green-600", weight="w500")
        self.txt_total = ft.Text(f"${total - descuento:.2f}", weight="bold", size=20, color=ft.colors.PRIMARY)

        super().__init__(
            padding=14,
            border_radius=10,
            bgcolor="grey-100",
            border=ft.border.all(1, "grey-300")
        )

        self.content = ft.Column([
            ft.Row([ft.Text("Subtotal", color="grey-700"), self.txt_subtotal], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([ft.Text("Descuento", color="grey-700"), self.txt_descuento], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=8, color="grey-300"),
            ft.Row([ft.Text("Total:", weight="bold", size=16), self.txt_total], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=4)

    def actualizar(self, total, descuento):
        self.total = total
        self.descuento = descuento
        self.txt_subtotal.value = f"${total:.2f}"
        self.txt_descuento.value = f"-${descuento:.2f}"
        self.txt_total.value = f"${total - descuento:.2f}"
        self.update()