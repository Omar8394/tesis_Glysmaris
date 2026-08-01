from typing import Callable, Optional

import flet as ft
from datetime import date, timedelta
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.campo_texto import CampoTexto
from ui.components.autocompletado import AutoCompletado
from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography

class PanelPago(ft.Column):
    def __init__(self, total, on_finalizar, on_volver, buscar_clientes: Optional[Callable[[str], list]] = None):
        # scroll=AUTO: al mostrarse los datos del cliente el contenido puede
        # superar el alto visible del panel; sin scroll, el botón "Finalizar
        # Venta" queda fuera de pantalla y no se puede pulsar.
        super().__init__(expand=True, spacing=AppSpacing.SECTION_SPACING, scroll=ft.ScrollMode.AUTO)
        self.total = total
        self.on_finalizar = on_finalizar
        self.on_volver = on_volver
        # Callback opcional (id_cliente/nombre/cedula/telefono) para que el
        # campo de nombre del cliente sugiera clientes ya registrados.
        self.buscar_clientes = buscar_clientes

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

        # Nombre del cliente con autocompletado: si ya existe en CLIENTES,
        # al elegirlo de la lista se rellenan cédula y teléfono solos.
        self.campo_cliente_nombre = AutoCompletado(
            etiqueta="Nombre del cliente",
            width=220,
            buscar=self._buscar_clientes_wrapper,
            seleccionar=self._cliente_seleccionado,
            on_change=lambda texto: self.actualizar_total_pagado(),
        )
        self.campo_cliente_cedula = CampoTexto(
            etiqueta="Cédula",
            width=180,
            on_change=lambda e: self.actualizar_total_pagado(),
        )
        self.campo_cliente_telefono = CampoTexto(etiqueta="Teléfono (opcional)", width=180)
        self.campo_dias_credito = CampoTexto(
            etiqueta="Días para pagar",
            value="15",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Datos del cliente: se piden SIEMPRE (nombre y cédula como
        # mínimo), sin importar el método de pago, para llevar un
        # registro de ventas adecuado.
        self.seccion_cliente = ft.Container(
            content=ft.Column([
                ft.Text("Datos del cliente", weight="bold", size=AppTypography.BODY),
                ft.Row(
                    [self.campo_cliente_nombre, self.campo_cliente_cedula, self.campo_cliente_telefono],
                    wrap=True, spacing=AppSpacing.SM,
                ),
            ], spacing=AppSpacing.SM),
            padding=ft.padding.only(top=AppSpacing.SM, bottom=AppSpacing.SM),
        )

        # Esto sí es exclusivo de la venta a crédito: cuántos días de
        # plazo tiene el cliente para pagar la deuda.
        self.seccion_credito = ft.Container(
            content=ft.Column([
                ft.Text("Plazo de crédito", weight="bold", size=AppTypography.BODY),
                self.campo_dias_credito,
            ], spacing=AppSpacing.SM),
            visible=False,
            padding=ft.padding.only(top=AppSpacing.SM, bottom=AppSpacing.SM),
        )

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
            self.seccion_cliente,
            self.seccion_credito,
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
        self.seccion_credito.visible = "Crédito" in self.montos
        self.actualizar_campos()

    def actualizar_campos(self):
        self.campos_montos.controls.clear()
        for metodo, monto in self.montos.items():
            campo = CampoTexto(
                etiqueta=f"Monto ({metodo})",
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

    def _buscar_clientes_wrapper(self, texto):
        """
        Adapta el resultado de ClienteService.buscar() (dicts con
        id_cliente/nombre/cedula/telefono) al formato que espera
        AutoCompletado (necesita una clave "id", no "id_cliente").
        """
        if not self.buscar_clientes:
            return []
        resultados = self.buscar_clientes(texto) or []
        adaptados = []
        for r in resultados:
            if isinstance(r, dict):
                adaptados.append({**r, "id": r.get("id_cliente", r.get("id"))})
            else:
                adaptados.append(r)
        return adaptados

    def _cliente_seleccionado(self, valor):
        """
        Al elegir un cliente ya existente de las sugerencias, se
        autocompletan cédula y teléfono para no tener que volver a
        escribirlos.
        """
        if isinstance(valor, dict):
            self.campo_cliente_cedula.value = valor.get("cedula") or ""
            self.campo_cliente_telefono.value = valor.get("telefono") or ""
            self.campo_cliente_cedula.update()
            self.campo_cliente_telefono.update()
        self.actualizar_total_pagado()

    def actualizar_total_pagado(self):
        pagado = sum(self.montos.values())
        self.total_pagado.value = f"Total pagado: ${pagado:.2f}"

        # Nombre y cédula del cliente son obligatorios sin importar el
        # método de pago elegido, para llevar un registro de ventas
        # adecuado (no solo para crédito).
        nombre_ok = bool(self.campo_cliente_nombre.obtener())
        cedula_ok = bool((self.campo_cliente_cedula.value or "").strip())
        cliente_ok = nombre_ok and cedula_ok

        self.btn_finalizar.disabled = (pagado < self.total - 0.01) or not cliente_ok
        self.update()

    def _finalizar(self, e):
        if sum(self.montos.values()) < self.total - 0.01:
            return

        nombre = self.campo_cliente_nombre.obtener()
        cedula = (self.campo_cliente_cedula.value or "").strip()
        if not nombre or not cedula:
            # El botón ya debería estar deshabilitado en este caso,
            # pero se valida de nuevo por seguridad.
            return

        datos_pago = {m: v for m, v in self.montos.items() if v > 0}

        cliente = {
            "id_cliente": self.campo_cliente_nombre.obtener_id(),
            "nombre": nombre,
            "cedula": cedula,
            "telefono": (self.campo_cliente_telefono.value or "").strip(),
        }

        fecha_vencimiento = None
        if "Crédito" in datos_pago:
            try:
                dias = int(self.campo_dias_credito.value or 0)
            except ValueError:
                dias = 0
            if dias > 0:
                fecha_vencimiento = (date.today() + timedelta(days=dias)).isoformat()

        self.on_finalizar({
            "pagos": datos_pago,
            "cliente": cliente,
            "fecha_vencimiento": fecha_vencimiento,
        })