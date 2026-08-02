# ui/modules/operaciones/cuentas_por_cobrar/cuentas_por_cobrar_module.py
"""
============================================================
Sistema La Dulce Tía — CuentasPorCobrarModule

Orquesta el módulo de Cuentas por Cobrar y Clientes: trae los datos
desde CuentaPorCobrarService / ClienteService, arma los diálogos
(abonar, historial, alta/edición de cliente) y calcula los
recordatorios de deudas vencidas o próximas a vencer. La vista
(cuentas_por_cobrar_view.py) solo dibuja lo que este módulo le pasa.
============================================================
"""

from __future__ import annotations

from datetime import date, datetime

import flet as ft

from ui.modules.base.module import Module
from ui.modules.operaciones.cuentas_por_cobrar.cuentas_por_cobrar_view import (
    CuentasPorCobrarView,
    METODOS_ABONO,
)
from ui.core.services.factory import ServiceFactory
from ui.components.tabla import EstadoFila
from ui.components.campo_texto import CampoTexto


def _a_date(valor):
    """Normaliza date/datetime/str ISO a un objeto date, o None."""
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue
    return None


class CuentasPorCobrarModule(Module):
    """
    Módulo de Cuentas por Cobrar y Clientes.
    """

    def __init__(self, page: ft.Page, usuario=None):
        super().__init__(page, usuario=usuario)
        self.cuenta_service = ServiceFactory.get_cuenta_por_cobrar_service()
        self.cliente_service = ServiceFactory.get_cliente_service()

        self.view = None

        # Cuentas por cobrar: estado en memoria (paginación client-side,
        # igual que el resto del sistema: los repos no paginan en SQL)
        self._filtro_cuentas = "pendientes"
        self._texto_busqueda_cuentas = ""
        self._cuentas_filtradas = []
        self._pagina_cuentas = 1
        self._por_pagina_cuentas = 15

        # Clientes: estado en memoria
        self._texto_busqueda_clientes = ""
        self._clientes_filtrados = []
        self._pagina_clientes = 1
        self._por_pagina_clientes = 15

    # ------------------------------------------------------------
    # Ciclo de vida (Module)
    # ------------------------------------------------------------
    def construir(self) -> ft.Control:
        self.view = CuentasPorCobrarView(
            on_buscar_cuentas=self._buscar_cuentas,
            on_cambiar_filtro_cuentas=self._cambiar_filtro_cuentas,
            on_cambiar_pagina_cuentas=self._cambiar_pagina_cuentas,
            on_ver_detalle=self._click_ver_detalle_cuentas,
            on_buscar_clientes=self._buscar_clientes,
            on_cambiar_pagina_clientes=self._cambiar_pagina_clientes,
            on_nuevo_cliente=self._abrir_form_cliente,
            on_editar_cliente=self._click_editar_cliente,
            on_eliminar_cliente=self._click_eliminar_cliente,
            on_ver_deudas_cliente=self._click_ver_deudas_cliente,
        )
        
        return self.view

    def cargar(self):
        """Module.on_show() la llama automáticamente al mostrar el módulo."""
        self._cargar_cuentas()
        self._cargar_clientes()

    # ------------------------------------------------------------
    # Cuentas por cobrar: carga, filtrado y recordatorios
    # ------------------------------------------------------------
    def _cargar_cuentas(self):
        if self._texto_busqueda_cuentas.strip():
            cuentas = self.cuenta_service.buscar(self._texto_busqueda_cuentas.strip())
        elif self._filtro_cuentas == "todas":
            cuentas = self.cuenta_service.listar()
        else:
            cuentas = self.cuenta_service.listar_deudas_pendientes()

        self._cuentas_filtradas = cuentas
        self.view.actualizar_total(self.cuenta_service.total_por_cobrar())
        self.view.actualizar_recordatorios(self._construir_recordatorios(cuentas))
        self._refrescar_tabla_cuentas()

    def _refrescar_tabla_cuentas(self):
        grupos = self._agrupar_por_cliente(self._cuentas_filtradas)
        self.view.actualizar_paginador_cuentas(len(grupos))

        inicio = (self._pagina_cuentas - 1) * self._por_pagina_cuentas
        pagina = grupos[inicio: inicio + self._por_pagina_cuentas]

        estado_por_fila = {g["id_cliente"]: g["peor_estado"] for g in pagina}
        self.view.poblar_tabla_cuentas(pagina, estado_por_fila)

    def _agrupar_por_cliente(self, cuentas):
        """
        Convierte la lista de deudas (una fila por venta a crédito) en
        una fila por cliente, sumando montos y quedándose con el
        vencimiento más próximo entre las deudas activas. El detalle
        de cada venta individual se consulta aparte al abrir "Ver
        detalle" (_click_ver_detalle_cuentas), no se pierde.
        """
        prioridad_estado = {
            None: 0,
            EstadoFila.ALERTA: 1,
            EstadoFila.VENCIDO: 2,
            EstadoFila.VENCIDO_CRITICO: 3,
        }

        grupos = {}
        orden = []
        for cuenta in cuentas:
            # Con id_cliente ausente (deudas antiguas de antes de que
            # el cliente fuera obligatorio) se agrupa por nombre para
            # no perder la fila, aunque no tendrá "Ver detalle" activo.
            clave = cuenta.get("id_cliente") or f"__sin_id__{cuenta.get('cliente_nombre')}"

            if clave not in grupos:
                grupos[clave] = {
                    "id_cliente": cuenta.get("id_cliente"),
                    "cliente_nombre": cuenta.get("cliente_nombre") or "Cliente sin nombre",
                    "cliente_telefono": cuenta.get("cliente_telefono"),
                    "monto_total": 0.0,
                    "monto_abonado": 0.0,
                    "monto_pendiente": 0.0,
                    "cantidad_deudas": 0,
                    "fecha_vencimiento_proxima": None,
                    "peor_estado": None,
                }
                orden.append(clave)

            grupo = grupos[clave]
            grupo["monto_total"] += float(cuenta.get("monto_total") or 0)
            grupo["monto_abonado"] += float(cuenta.get("monto_abonado") or 0)
            grupo["monto_pendiente"] += float(cuenta.get("monto_pendiente") or 0)
            grupo["cantidad_deudas"] += 1

            if cuenta.get("estado") in ("pendiente", "parcial"):
                venc = _a_date(cuenta.get("fecha_vencimiento"))
                venc_actual = _a_date(grupo["fecha_vencimiento_proxima"])
                if venc and (venc_actual is None or venc < venc_actual):
                    grupo["fecha_vencimiento_proxima"] = cuenta.get("fecha_vencimiento")

            estado_fila = self._estado_fila(cuenta)
            if prioridad_estado.get(estado_fila, 0) > prioridad_estado.get(grupo["peor_estado"], 0):
                grupo["peor_estado"] = estado_fila

        return [grupos[clave] for clave in orden]

    def _estado_fila(self, cuenta):
        """Traduce la deuda a un EstadoFila semántico para resaltar la
        fila: ALERTA si vence pronto, VENCIDO/VENCIDO_CRITICO si ya venció."""
        if cuenta.get("estado") in ("pagada", "anulada"):
            return None

        vencimiento = _a_date(cuenta.get("fecha_vencimiento"))
        if vencimiento is None:
            return None

        dias = (date.today() - vencimiento).days
        if dias > 7:
            return EstadoFila.VENCIDO_CRITICO
        if dias > 0:
            return EstadoFila.VENCIDO
        if dias >= -3:
            return EstadoFila.ALERTA
        return None

    def _construir_recordatorios(self, cuentas):
        """
        Arma los mensajes tipo 'recuérdale a X que debe $Y' para las
        deudas vencidas o a punto de vencer (3 días o menos), ordenados
        por urgencia — lo más vencido primero.
        """
        candidatos = []
        for cuenta in cuentas:
            if cuenta.get("estado") not in ("pendiente", "parcial"):
                continue
            vencimiento = _a_date(cuenta.get("fecha_vencimiento"))
            if vencimiento is None:
                continue

            dias = (date.today() - vencimiento).days
            nombre = cuenta.get("cliente_nombre") or "Cliente sin nombre"
            monto = float(cuenta.get("monto_pendiente") or 0)

            if dias > 0:
                texto = (
                    f"⚠️ {nombre} debe ${monto:.2f} — venció hace "
                    f"{dias} día{'s' if dias != 1 else ''}."
                )
            elif dias >= -3:
                texto = (
                    f"🔔 {nombre} debe ${monto:.2f} — vence en "
                    f"{abs(dias)} día{'s' if abs(dias) != 1 else ''}."
                )
            else:
                continue

            candidatos.append((dias, texto))

        # Más vencido (dias más grande) primero.
        candidatos.sort(key=lambda par: -par[0])
        return [texto for _, texto in candidatos]

    def _buscar_cuentas(self, texto):
        self._texto_busqueda_cuentas = texto or ""
        self._pagina_cuentas = 1
        self._cargar_cuentas()

    def _cambiar_filtro_cuentas(self, filtro):
        self._filtro_cuentas = filtro
        self._pagina_cuentas = 1
        self._cargar_cuentas()

    def _cambiar_pagina_cuentas(self, pagina, por_pagina):
        self._pagina_cuentas = pagina
        self._por_pagina_cuentas = por_pagina
        self._refrescar_tabla_cuentas()

    # ------------------------------------------------------------
    # Abonar / historial de abonos
    # ------------------------------------------------------------
    def _abrir_dialogo_abono_si_activa(self, cuenta):
        if cuenta["estado"] in ("pagada", "anulada"):
            self.mensaje("Esta cuenta ya no tiene saldo pendiente.", tipo="info")
            return
        self._abrir_dialogo_abono(cuenta)

    def _abrir_dialogo_abono(self, cuenta):
        campo_monto = CampoTexto(
            etiqueta=f"Monto (pendiente: ${float(cuenta['monto_pendiente']):.2f})",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=280,
        )
        dropdown_metodo = ft.Dropdown(
            label="Método de pago",
            width=280,
            value=METODOS_ABONO[0][0],
            options=[ft.dropdown.Option(valor, texto) for valor, texto in METODOS_ABONO],
        )
        campo_referencia = CampoTexto(etiqueta="Referencia (opcional)", width=280)
        campo_observaciones = CampoTexto(etiqueta="Observaciones (opcional)", width=280)

        def _guardar(ev):
            try:
                monto = float(campo_monto.value or 0)
            except ValueError:
                monto = 0.0

            exito, mensaje = self.cuenta_service.abonar(
                id_cuenta=cuenta["id_cuenta"],
                monto=monto,
                metodo_pago=dropdown_metodo.value,
                referencia=campo_referencia.value or "",
                observaciones=campo_observaciones.value or "",
                usuario_registro=self.usuario or "",
            )
            self._cerrar_dialogo()
            self.mensaje(mensaje, tipo="exito" if exito else "error")
            if exito:
                self._cargar_cuentas()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Registrar abono — {cuenta.get('cliente_nombre') or 'Cliente'}"),
            content=ft.Column(
                [campo_monto, dropdown_metodo, campo_referencia, campo_observaciones],
                tight=True, spacing=12, width=300,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self._cerrar_dialogo()),
                ft.ElevatedButton("Registrar", on_click=_guardar),
            ],
        )
        self._mostrar_dialogo(dialogo)

    def _abrir_dialogo_historial(self, cuenta):
        abonos = self.cuenta_service.historial_abonos(cuenta["id_cuenta"])
        fecha_venta = _a_date(cuenta.get("fecha_venta"))
        subtitulo = f"venta del {fecha_venta.strftime('%d/%m/%Y')}" if fecha_venta else "esta venta"

        if abonos:
            filas = [
                ft.Row([
                    ft.Text(
                        _a_date(a.get("fecha_abono")).strftime("%d/%m/%Y")
                        if _a_date(a.get("fecha_abono")) else "—",
                        width=90,
                    ),
                    ft.Text(f"${float(a['monto']):.2f}", width=90),
                    ft.Text(a.get("metodo_pago", ""), width=100),
                    ft.Text(a.get("referencia") or "—", expand=True),
                ])
                for a in abonos
            ]
        else:
            filas = [ft.Text("Todavía no hay abonos registrados.")]

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Historial de abonos — {subtitulo}"),
            content=ft.Column(
                filas, tight=True, spacing=8, width=380,
                scroll=ft.ScrollMode.AUTO, height=300,
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda ev: self._cerrar_dialogo())],
        )
        self._mostrar_dialogo(dialogo)

    def _click_ver_detalle_cuentas(self, e):
        """
        Abre el detalle de TODAS las deudas (una por venta a crédito)
        de un cliente, cada una con sus propios botones de Abonar e
        Historial. La tabla principal solo muestra el total agrupado
        por cliente; este diálogo es el "expandible" con el desglose
        por venta y su fecha.
        """
        id_cliente = e.control.data
        if id_cliente is None:
            self.mensaje(
                "Esta deuda no tiene un cliente registrado asociado "
                "(dato antiguo); no se puede abrir el detalle.",
                tipo="error",
            )
            return

        cliente = self.cliente_service.obtener(id_cliente)
        deudas = self.cuenta_service.listar_por_cliente(id_cliente)

        def _fila_deuda(cuenta):
            activa = cuenta.get("estado") in ("pendiente", "parcial")
            fecha_venta = _a_date(cuenta.get("fecha_venta"))

            botones = []
            if activa:
                botones.append(
                    ft.IconButton(
                        icon=ft.icons.PAYMENTS_ROUNDED,
                        tooltip="Registrar abono",
                        on_click=lambda ev, c=cuenta: self._abrir_dialogo_abono_si_activa(c),
                    )
                )
            botones.append(
                ft.IconButton(
                    icon=ft.icons.HISTORY_ROUNDED,
                    tooltip="Ver historial de abonos",
                    on_click=lambda ev, c=cuenta: self._abrir_dialogo_historial(c),
                )
            )

            return ft.Row(
                [
                    ft.Text(fecha_venta.strftime("%d/%m/%Y") if fecha_venta else "—", width=80),
                    ft.Text(f"${float(cuenta.get('monto_total') or 0):.2f}", width=75),
                    ft.Text(f"${float(cuenta.get('monto_pendiente') or 0):.2f}", width=80),
                    ft.Text((cuenta.get("estado") or "").capitalize(), width=75),
                    ft.Row(botones, spacing=0, tight=True),
                ],
                alignment=ft.MainAxisAlignment.START,
            )

        if deudas:
            filas = [_fila_deuda(d) for d in deudas]
        else:
            filas = [ft.Text("Este cliente no tiene deudas registradas.")]

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Deudas de {cliente.get('nombre') if cliente else 'cliente'}"),
            content=ft.Column(
                filas, tight=True, spacing=10, width=420,
                scroll=ft.ScrollMode.AUTO, height=340,
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda ev: self._cerrar_dialogo())],
        )
        self._mostrar_dialogo(dialogo)

    # ------------------------------------------------------------
    # Clientes: carga y filtrado
    # ------------------------------------------------------------
    def _cargar_clientes(self):
        if self._texto_busqueda_clientes.strip():
            self._clientes_filtrados = self.cliente_service.buscar(self._texto_busqueda_clientes.strip())
        else:
            self._clientes_filtrados = self.cliente_service.listar()
        self._refrescar_tabla_clientes()

    def _refrescar_tabla_clientes(self):
        self.view.actualizar_paginador_clientes(len(self._clientes_filtrados))
        inicio = (self._pagina_clientes - 1) * self._por_pagina_clientes
        pagina = self._clientes_filtrados[inicio: inicio + self._por_pagina_clientes]
        self.view.poblar_tabla_clientes(pagina)

    def _buscar_clientes(self, texto):
        self._texto_busqueda_clientes = texto or ""
        self._pagina_clientes = 1
        self._cargar_clientes()

    def _cambiar_pagina_clientes(self, pagina, por_pagina):
        self._pagina_clientes = pagina
        self._por_pagina_clientes = por_pagina
        self._refrescar_tabla_clientes()

    # ------------------------------------------------------------
    # Alta / edición / baja de clientes
    # ------------------------------------------------------------
    def _abrir_form_cliente(self, cliente=None):
        es_edicion = cliente is not None
        datos_previos = cliente or {}

        campo_nombre = CampoTexto(etiqueta="Nombre*", width=280, value=datos_previos.get("nombre", ""))
        campo_cedula = CampoTexto(etiqueta="Cédula", width=280, value=datos_previos.get("cedula") or "")
        campo_telefono = CampoTexto(etiqueta="Teléfono", width=280, value=datos_previos.get("telefono") or "")
        campo_direccion = CampoTexto(etiqueta="Dirección", width=280, value=datos_previos.get("direccion") or "")
        campo_observaciones = CampoTexto(
            etiqueta="Observaciones", width=280, value=datos_previos.get("observaciones") or ""
        )

        def _guardar(ev):
            datos = {
                "nombre": campo_nombre.value,
                "cedula": campo_cedula.value,
                "telefono": campo_telefono.value,
                "direccion": campo_direccion.value,
                "observaciones": campo_observaciones.value,
            }
            if es_edicion:
                exito, mensaje = self.cliente_service.actualizar(cliente["id_cliente"], datos)
            else:
                exito, mensaje = self.cliente_service.crear(datos)

            self._cerrar_dialogo()
            self.mensaje(mensaje, tipo="exito" if exito else "error")
            if exito:
                self._cargar_clientes()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Cliente" if es_edicion else "Nuevo Cliente"),
            content=ft.Column(
                [campo_nombre, campo_cedula, campo_telefono, campo_direccion, campo_observaciones],
                tight=True, spacing=12, width=300,
                scroll=ft.ScrollMode.AUTO, height=320,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self._cerrar_dialogo()),
                ft.ElevatedButton("Guardar", on_click=_guardar),
            ],
        )
        self._mostrar_dialogo(dialogo)

    def _click_editar_cliente(self, e):
        id_cliente = e.control.data
        cliente = self.cliente_service.obtener(id_cliente)
        if cliente:
            self._abrir_form_cliente(cliente)

    def _click_eliminar_cliente(self, e):
        id_cliente = e.control.data

        def _confirmar(ev):
            exito, mensaje = self.cliente_service.eliminar(id_cliente)
            self._cerrar_dialogo()
            self.mensaje(mensaje, tipo="exito" if exito else "error")
            if exito:
                self._cargar_clientes()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Desactivar cliente"),
            content=ft.Text(
                "El cliente no se elimina para conservar su historial de "
                "ventas y deudas; solo se desactiva. ¿Continuar?"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self._cerrar_dialogo()),
                ft.ElevatedButton("Desactivar", on_click=_confirmar),
            ],
        )
        self._mostrar_dialogo(dialogo)

    def _click_ver_deudas_cliente(self, e):
        id_cliente = e.control.data
        cliente = self.cliente_service.obtener(id_cliente)
        deudas = self.cuenta_service.listar_por_cliente(id_cliente)

        if deudas:
            filas = [
                ft.Row([
                    ft.Text(
                        _a_date(d.get("fecha_venta")).strftime("%d/%m/%Y")
                        if _a_date(d.get("fecha_venta")) else "—",
                        width=90,
                    ),
                    ft.Text(f"${float(d['monto_pendiente']):.2f}", width=90),
                    ft.Text((d.get("estado") or "").capitalize(), width=90),
                ])
                for d in deudas
            ]
        else:
            filas = [ft.Text("Este cliente no tiene deudas registradas.")]

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Deudas de {cliente.get('nombre') if cliente else ''}"),
            content=ft.Column(
                filas, tight=True, spacing=8, width=320,
                scroll=ft.ScrollMode.AUTO, height=280,
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda ev: self._cerrar_dialogo())],
        )
        self._mostrar_dialogo(dialogo)

    # ------------------------------------------------------------
    # Utilidad de diálogos
    # ------------------------------------------------------------
    def _mostrar_dialogo(self, dialogo: ft.AlertDialog):
        self.page.dialog = dialogo
        dialogo.open = True
        self.page.update()

    def _cerrar_dialogo(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()