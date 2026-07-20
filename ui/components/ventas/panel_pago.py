import flet as ft
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.campo_texto import CampoTexto
from ui.components.selector import Selector
from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography

class PanelPago(ft.Column):
    def __init__(self, total, on_finalizar, on_volver):
        super().__init__(expand=True, spacing=AppSpacing.SECTION_SPACING)
        self.total = total
        self.on_finalizar = on_finalizar
        self.on_volver = on_volver

        # Métodos de pago (selección múltiple para pago mixto)
        self.metodos_pago = [
            {"nombre": "Efectivo", "icono": ft.icons.CASH},
            {"nombre": "Débito", "icono": ft.icons.CREDIT_CARD},
            {"nombre": "Crédito", "icono": ft.icons.CREDIT_CARD},
            {"nombre": "Transferencia", "icono": ft.icons.ACCOUNT_BALANCE},
            {"nombre": "Pago móvil", "icono": ft.icons.PHONE_ANDROID},
        ]
        self.montos = {}  # método -> monto

        # Grid de métodos
        self.grid_pagos = ft.GridView(
            max_extent=120,
            spacing=AppSpacing.SM,
            run_spacing=AppSpacing.SM,
            child_aspect_ratio=1.2,
        )
        for metodo in self.metodos_pago:
            btn = ft.Container(
                content=ft.Column([
                    ft.Icon(metodo['icono'], size=30),
                    ft.Text(metodo['nombre'], size=AppTypography.SMALL)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=AppSpacing.MD,
                bgcolor="white",
                border=ft.border.all(1, "gray"),
                border_radius=5,
                ink=True,
                on_click=lambda e, m=metodo: self.seleccionar_metodo(m)
            )
            self.grid_pagos.controls.append(btn)

        # Campos de montos (se añaden dinámicamente)
        self.campos_montos = ft.Column(spacing=AppSpacing.SM)

        # Resumen de total pagado
        self.total_pagado = ft.Text(f"Total pagado: $0.00", weight="bold")

        # Botones
        self.btn_finalizar = BotonPrimario(
            texto="Finalizar venta",
            icono=ft.icons.CHECK,
            on_click=self._finalizar,
            disabled=True
        )
        self.btn_volver = BotonSecundario(
            texto="Volver al carrito",
            icono=ft.icons.ARROW_BACK,
            on_click=lambda e: self.on_volver()
        )

        self.controls = [
            ft.Text("Cobro", weight="bold", size=20),
            ft.Text(f"Total a pagar: ${self.total:.2f}", size=AppTypography.SECTION_TITLE),
            ft.Text("Selecciona método(s) de pago:", size=AppTypography.BODY),
            self.grid_pagos,
            self.campos_montos,
            self.total_pagado,
            ft.Row([self.btn_volver, self.btn_finalizar], alignment=ft.MainAxisAlignment.END, spacing=AppSpacing.BUTTON_SPACING)
        ]

    def seleccionar_metodo(self, metodo):
        # Si el método ya está seleccionado, lo quitamos
        if metodo['nombre'] in self.montos:
            del self.montos[metodo['nombre']]
            self.actualizar_campos()
            return
        # Agregar campo de monto
        self.montos[metodo['nombre']] = 0.0
        self.actualizar_campos()

    def actualizar_campos(self):
        self.campos_montos.controls.clear()
        for metodo, monto in self.montos.items():
            campo = CampoTexto(
                label=metodo,
                value=str(monto) if monto else "",
                width=150,
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
        self.btn_finalizar.disabled = (pagado < self.total - 0.01)  # tolerancia
        self.update()

    def _finalizar(self, e):
        if sum(self.montos.values()) >= self.total - 0.01:
            # Registrar pago mixto
            datos_pago = {m: v for m, v in self.montos.items() if v > 0}
            self.on_finalizar(datos_pago)