import flet as ft
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.campo_texto import CampoTexto
from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography

class PanelPago(ft.Column):
    def __init__(self, total, on_finalizar, on_volver):
        super().__init__(expand=True, spacing=AppSpacing.SECTION_SPACING)
        self.total = total
        self.on_finalizar = on_finalizar
        self.on_volver = on_volver

        self.metodos_pago = [
            {"nombre": "Efectivo", "icono": ft.icons.MONEY_ROUNDED},
            {"nombre": "Débito", "icono": ft.icons.CREDIT_CARD_ROUNDED},
            {"nombre": "Crédito", "icono": ft.icons.PAYMENT_ROUNDED},
            {"nombre": "Transferencia", "icono": ft.icons.ACCOUNT_BALANCE_ROUNDED},
            {"nombre": "Pago móvil", "icono": ft.icons.PHONE_ANDROID_ROUNDED},
        ]
        self.montos = {}  # método -> monto
        self.tarjetas_ui = {}

        # Grid de métodos
        self.grid_pagos = ft.Row(wrap=True, spacing=10)
        
        for metodo in self.metodos_pago:
            btn = self._crear_tarjeta_metodo(metodo)
            self.tarjetas_ui[metodo['nombre']] = btn
            self.grid_pagos.controls.append(btn)

        self.campos_montos = ft.Column(spacing=AppSpacing.SM)
        self.total_pagado = ft.Text("Total pagado: $0.00", weight="bold", size=16)

        self.btn_finalizar = BotonPrimario(
            texto="Finalizar Venta",
            icono=ft.icons.CHECK_CIRCLE_OUTLINED,
            on_click=self._finalizar,
            disabled=True,
            height=45
        )
        self.btn_volver = BotonSecundario(
            texto="Volver al Carrito",
            icono=ft.icons.ARROW_BACK_ROUNDED,
            on_click=lambda e: self.on_volver(),
            height=45
        )

        self.controls = [
            ft.Text("Cobro & Pago", weight="bold", size=22),
            ft.Container(
                content=ft.Row([
                    ft.Text("Total a pagar:", size=16),
                    ft.Text(f"${self.total:.2f}", size=24, weight="bold", color=ft.colors.PRIMARY)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=ft.colors.PRIMARY_CONTAINER,
                padding=15,
                border_radius=10
            ),
            ft.Text("Selecciona método(s) de pago:", size=AppTypography.BODY, weight="bold"),
            self.grid_pagos,
            ft.Divider(color="grey-200"),
            self.campos_montos,
            ft.Row([self.total_pagado], alignment=ft.MainAxisAlignment.END),
            ft.Row([self.btn_volver, self.btn_finalizar], alignment=ft.MainAxisAlignment.END, spacing=AppSpacing.BUTTON_SPACING)
        ]

    def _crear_tarjeta_metodo(self, metodo):
        nombre = metodo['nombre']
        return ft.Container(
            content=ft.Column([
                ft.Icon(metodo['icono'], size=26, color="grey-700"),
                ft.Text(nombre, size=12, weight="w500", color="grey-800")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
            width=110,
            height=80,
            bgcolor="white",
            border=ft.border.all(1, "grey-300"),
            border_radius=10,
            ink=True,
            on_click=lambda e, m=metodo: self.seleccionar_metodo(m)
        )

    def seleccionar_metodo(self, metodo):
        nombre = metodo['nombre']
        tarjeta = self.tarjetas_ui[nombre]

        if nombre in self.montos:
            del self.montos[nombre]
            # Estado Desactivado
            tarjeta.bgcolor = "white"
            tarjeta.border = ft.border.all(1, "grey-300")
            tarjeta.content.controls[0].color = "grey-700"
        else:
            # Si es el primer método agregado, autocompletar con el restante de la venta
            pendiente = max(0.0, self.total - sum(self.montos.values()))
            self.montos[nombre] = pendiente

            # Estado Activo
            tarjeta.bgcolor = ft.colors.PRIMARY_CONTAINER
            tarjeta.border = ft.border.all(1.5, ft.colors.PRIMARY)
            tarjeta.content.controls[0].color = ft.colors.PRIMARY

        tarjeta.update()
        self.actualizar_campos()

    def actualizar_campos(self):
        self.campos_montos.controls.clear()
        for metodo, monto in self.montos.items():
            campo = CampoTexto(
                label=f"Monto ({metodo})",
                value=str(monto) if monto > 0 else "",
                width=200,
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e, m=metodo: self.actualizar_monto(m, e.control.value)
            )
            self.campos_montos.controls.append(ft.Row([campo], spacing=AppSpacing.SM))
        self.actualizar_total_pagado()
        self.update()

    def actualizar_monto(self, metodo, valor):
        try:
            self.montos[metodo] = float(valor)
        except ValueError:
            self.montos[metodo] = 0.0
        self.actualizar_total_pagado()

    def actualizar_total_pagado(self):
        pagado = sum(self.montos.values())
        self.total_pagado.value = f"Total pagado: ${pagado:.2f}"
        self.btn_finalizar.disabled = (pagado < self.total - 0.01)
        self.update()

    def _finalizar(self, e):
        if sum(self.montos.values()) >= self.total - 0.01:
            datos_pago = {m: v for m, v in self.montos.items() if v > 0}
            self.on_finalizar(datos_pago)