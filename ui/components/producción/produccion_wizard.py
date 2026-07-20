"""
============================================================
Sistema La Dulce Tía

Archivo:
    produccion_wizard.py

Responsabilidad:
    Asistente (Wizard) de 5 pasos para crear una orden de producción.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft
from datetime import datetime, date
from typing import Callable, Optional, Dict, List, Any

from ui.components.campo_texto import CampoTexto
from ui.components.selector import Selector
from ui.components.buscador import Buscador
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.tarjetas import TarjetaResumen, TarjetaAdvertencia
from ui.components.productos.stepper import Stepper
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing
from ui.core.icons import AppIcons
from ui.core.services.factory import ServiceFactory


class ProduccionWizard(ft.Container):
    """
    Asistente de 5 pasos para crear órdenes de producción.
    """

    def __init__(
        self,
        on_guardar: Callable[[Dict], None] | None = None,
        on_cancelar: Callable | None = None,
    ):
        super().__init__()
        self.on_guardar = on_guardar
        self.on_cancelar = on_cancelar

        # Servicios
        self.producto_service = ServiceFactory.get_producto_service()
        self.produccion_service = ServiceFactory.get_produccion_service()

        # Estado del wizard
        self.paso_actual = 0
        self.productos_seleccionados: List[Dict] = []
        self.analisis_realizado = False
        self.analisis_resultados: Dict = {}
        # id_producto -> "reducir" | "mantener", para recordar qué eligió
        # el usuario en el Paso 2 cuando el análisis dio resultado parcial.
        self._decisiones_analisis: Dict[int, str] = {}
        self.datos_planificacion: Dict = {}

        # --- Construir componentes por paso ---
        self._crear_paso1()
        self._crear_paso2()
        self._crear_paso3()
        self._crear_paso4()
        self._crear_paso5()

        # --- Stepper ---
        self.stepper = Stepper(
            pasos=[
                "Seleccionar productos",
                "Validación",
                "Planificación",
                "Resumen",
                "Confirmación"
            ],
            paso_actual=0,
        )

        # --- Contenedor de contenido del paso ---
        self.contenido_paso = ft.Container(
            content=self.paso1_contenido,
            padding=AppSpacing.MD,
            expand=True,
        )

        # --- Botones de navegación ---
        self.btn_siguiente = BotonPrimario(
            texto="Siguiente",
            icono=ft.icons.ARROW_FORWARD,
            on_click=self._siguiente,
        )
        self.btn_anterior = BotonSecundario(
            texto="Atrás",
            icono=ft.icons.ARROW_BACK,
            on_click=self._anterior,
        )
        self.btn_anterior.visible = False

        self.btn_guardar = BotonPrimario(
            texto="Crear Orden",
            icono=ft.icons.SAVE,
            on_click=self._guardar,
        )
        self.btn_guardar.visible = False

        self.btn_cancelar = BotonSecundario(
            texto="Cancelar",
            icono=ft.icons.CLOSE,
            on_click=self._cancelar,
        )

        self.botones_row = ft.Row(
            [self.btn_anterior, self.btn_siguiente, self.btn_guardar, self.btn_cancelar],
            spacing=AppSpacing.BUTTON_SPACING,
            alignment=ft.MainAxisAlignment.END,
        )

        # --- Layout principal ---
        self.content = ft.Column(
            [
                self.stepper,
                ft.Divider(height=10),
                self.contenido_paso,
                ft.Divider(height=10),
                self.botones_row,
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            width=750,
        )

        # ❌ NO llamar a update() aquí
        # self._actualizar_botones()  # <-- ELIMINADO

    # =========================================================
    #  CONSTRUCCIÓN DE PASOS
    # =========================================================

    def _crear_paso1(self):
        self.buscador_productos = Buscador(
            buscar=self._buscar_productos,
            placeholder="Buscar producto...",
            width=350,
            mostrar_limpiar=True,
            mostrar_actualizar=False,
        )

        self.resultados_busqueda = ft.Column(spacing=5, visible=False)

        self.cantidad_input = CampoTexto(
            etiqueta="Cantidad",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="1",
        )

        self.btn_agregar = BotonPrimario(
            texto="Agregar",
            icono=AppIcons.ADD,
            on_click=self._agregar_producto,
            width=120,
        )

        self.lista_agregados = ft.Column(spacing=5)

        self.paso1_contenido = ft.Column(
            [
                ft.Text(
                    "Buscar y seleccionar los productos a fabricar",
                    size=AppTypography.SECTION_TITLE,
                    weight="bold",
                ),
                ft.Row(
                    [self.buscador_productos, self.cantidad_input, self.btn_agregar],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                self.resultados_busqueda,
                ft.Divider(height=10),
                ft.Text("Productos agregados:", weight="bold"),
                self.lista_agregados,
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            expand=True,
        )

    def _crear_paso2(self):
        self.analisis_contenido = ft.Column(
            [
                ft.Text(
                    "Análisis de disponibilidad",
                    size=AppTypography.SECTION_TITLE,
                    weight="bold",
                ),
                ft.Text(
                    "Verificando inventario de ingredientes y activos...",
                    size=AppTypography.BODY,
                ),
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            expand=True,
        )
        self.paso2_contenido = self.analisis_contenido

    def _crear_paso3(self):
        self.fecha_input = CampoTexto(
            etiqueta="Fecha planificada",
            width=200,
            value=date.today().strftime("%d/%m/%Y"),
            hint="DD/MM/AAAA",
        )
        self.hora_input = CampoTexto(
            etiqueta="Hora estimada",
            width=150,
            hint="HH:MM",
        )
        self.prioridad_selector = Selector(
            etiqueta="Prioridad",
            opciones=["baja", "media", "alta", "urgente"],
            valor="media",
            width=180,
        )
        self.responsable_input = CampoTexto(
            etiqueta="Responsable",
            width=250,
        )
        self.observaciones_input = CampoTexto(
            etiqueta="Observaciones",
            multiline=True,
            width=500,
        )

        self.paso3_contenido = ft.Column(
            [
                ft.Text(
                    "Planificación de la orden",
                    size=AppTypography.SECTION_TITLE,
                    weight="bold",
                ),
                ft.Row([self.fecha_input, self.hora_input, self.prioridad_selector]),
                ft.Row([self.responsable_input]),
                ft.Row([self.observaciones_input]),
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            expand=True,
        )

    def _crear_paso4(self):
        self.resumen_contenido = ft.Column(
            [
                ft.Text(
                    "Resumen de la orden",
                    size=AppTypography.SECTION_TITLE,
                    weight="bold",
                ),
                ft.Text("Cargando resumen...", size=AppTypography.BODY),
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            expand=True,
        )
        self.paso4_contenido = self.resumen_contenido

    def _crear_paso5(self):
        self.paso5_contenido = ft.Column(
            [
                ft.Icon(ft.icons.CHECK_CIRCLE, size=64, color=ft.colors.GREEN),
                ft.Text(
                    "¡Orden creada exitosamente!",
                    size=AppTypography.SECTION_TITLE,
                    weight="bold",
                ),
                ft.Text(
                    "La orden ha sido creada y está pendiente de producción.",
                    size=AppTypography.BODY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=AppSpacing.CONTROL_SPACING,
            expand=True,
        )

    # =========================================================
    #  NAVEGACIÓN ENTRE PASOS
    # =========================================================

    def _siguiente(self, e):
        if self.paso_actual == 0:
            if not self.productos_seleccionados:
                self._mostrar_error("Debe agregar al menos un producto.")
                return
            self._ejecutar_analisis()
        elif self.paso_actual == 1:
            if not self.analisis_realizado:
                self._mostrar_error("Debe ejecutar el análisis de disponibilidad.")
                return
        elif self.paso_actual == 2:
            if not self._validar_planificacion():
                return
            self._preparar_resumen()

        if self.paso_actual < 4:
            self.paso_actual += 1
            self._actualizar_paso()
            self._actualizar_botones()
            if self.page:
                self.update()

    def _anterior(self, e):
        if self.paso_actual > 0:
            self.paso_actual -= 1
            self._actualizar_paso()
            self._actualizar_botones()
            if self.page:
                self.update()

    def _actualizar_paso(self):
        self.stepper.ir_a(self.paso_actual)
        contenidos = [
            self.paso1_contenido,
            self.paso2_contenido,
            self.paso3_contenido,
            self.paso4_contenido,
            self.paso5_contenido,
        ]
        self.contenido_paso.content = contenidos[self.paso_actual]
        if self.page:
            self.contenido_paso.update()

    def _actualizar_botones(self):
        self.btn_anterior.visible = self.paso_actual > 0 and self.paso_actual < 4
        self.btn_siguiente.visible = self.paso_actual < 3
        self.btn_guardar.visible = self.paso_actual == 3
        if self.page:
            self.update()

    def _mostrar_error(self, mensaje: str):
        from ui.components.dialogo import Dialogo
        Dialogo.error(self.page, mensaje)

    # =========================================================
    #  LÓGICA DEL PASO 1: SELECCIÓN DE PRODUCTOS
    # =========================================================

    def _buscar_productos(self, texto: str):
        if not texto:
            self.resultados_busqueda.visible = False
            if self.page:
                self.update()
            return

        resultado_busqueda = self.producto_service.buscar(texto)
        productos = resultado_busqueda.datos if resultado_busqueda.exito else []
        self.resultados_busqueda.controls.clear()
        for p in productos[:10]:
            item = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(p["nombre"], expand=True),
                        ft.Text(f"${p.get('precio_venta', 0):.2f}", size=12, color=ft.colors.GREY),
                    ],
                    spacing=10,
                ),
                padding=8,
                on_click=lambda e, prod=p: self._seleccionar_producto(prod),
                ink=True,
                border_radius=5,
            )
            self.resultados_busqueda.controls.append(item)

        self.resultados_busqueda.visible = bool(productos)
        if self.page:
            self.update()

    def _seleccionar_producto(self, producto: Dict):
        for p in self.productos_seleccionados:
            if p["id_producto"] == producto["id_producto"]:
                self._mostrar_error("El producto ya está en la lista.")
                return

        self.productos_seleccionados.append({
            "id_producto": producto["id_producto"],
            "nombre": producto["nombre"],
            "cantidad": 1,
            "id_presentacion": None,
            "precio": producto.get("precio_venta", 0),
        })
        self._refrescar_lista_agregados()
        self.resultados_busqueda.visible = False
        self.buscador_productos.limpiar()
        if self.page:
            self.update()

    def _agregar_producto(self, e):
        texto = self.buscador_productos.obtener() or ""
        if not texto:
            self._mostrar_error("Busque un producto primero.")
            return

        resultado_busqueda = self.producto_service.buscar(texto)
        productos = resultado_busqueda.datos if resultado_busqueda.exito else []
        if not productos:
            self._mostrar_error("Producto no encontrado.")
            return

        self._seleccionar_producto(productos[0])

    def _refrescar_lista_agregados(self):
        self.lista_agregados.controls.clear()
        for idx, p in enumerate(self.productos_seleccionados):
            fila = ft.Row(
                [
                    ft.Text(f"{p['nombre']}", expand=True, weight="bold"),
                    ft.Text(f"Cantidad: {p['cantidad']}", width=100),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        icon_color=ft.colors.RED,
                        tooltip="Quitar",
                        on_click=lambda e, i=idx: self._eliminar_producto(i),
                    ),
                ],
                spacing=10,
            )
            self.lista_agregados.controls.append(fila)
        if self.page:
            self.update()

    def _eliminar_producto(self, idx: int):
        if 0 <= idx < len(self.productos_seleccionados):
            self.productos_seleccionados.pop(idx)
            self._refrescar_lista_agregados()
            if not self.productos_seleccionados:
                self.analisis_realizado = False
            if self.page:
                self.update()

    # =========================================================
    #  LÓGICA DEL PASO 2: ANÁLISIS
    # =========================================================

    def _ejecutar_analisis(self):
        datos_orden = {
            "fecha_planificada": date.today().isoformat(),
            "prioridad": "media",
            "detalles": [
                {
                    "id_producto": p["id_producto"],
                    "cantidad": p["cantidad"],
                    "id_presentacion": p.get("id_presentacion"),
                }
                for p in self.productos_seleccionados
            ],
        }

        resultado = self.produccion_service.analizar_orden_temporal(datos_orden)
        if resultado.fallo:
            self._mostrar_error(f"Error en el análisis: {resultado.mensaje}")
            return

        self.analisis_resultados = resultado.datos
        self.analisis_realizado = True
        self._mostrar_analisis()
        if self.page:
            self.update()

    def _resolver_parcial(self, id_producto: int, decision: str, cantidad: int):
        """
        Aplica la decisión del usuario ante un resultado parcial:
        - "reducir": ajusta la cantidad solicitada a la cantidad máxima
          posible calculada por el análisis.
        - "mantener": deja la cantidad como estaba (la orden queda
          pendiente igual; si llega más stock antes de iniciarla, se
          podrá fabricar completa).
        En ambos casos se re-ejecuta el análisis para reflejar el estado
        actualizado en pantalla.
        """
        self._decisiones_analisis[id_producto] = decision

        if decision == "reducir":
            for p in self.productos_seleccionados:
                if p["id_producto"] == id_producto:
                    p["cantidad"] = cantidad
                    break

        self._ejecutar_analisis()

    def _mostrar_analisis(self):
        self.analisis_contenido.controls.clear()
        self.analisis_contenido.controls.append(
            ft.Text(
                "Resultados del análisis de disponibilidad",
                size=AppTypography.SECTION_TITLE,
                weight="bold",
            )
        )

        for producto in self.analisis_resultados.get("resultados", []):
            card = self._crear_tarjeta_analisis(producto)
            self.analisis_contenido.controls.append(card)

        total_faltantes = self.analisis_resultados.get("total_faltantes", 0)
        if total_faltantes > 0:
            self.analisis_contenido.controls.append(ft.Divider(height=20))
            self.analisis_contenido.controls.append(
                TarjetaAdvertencia(
                    mensaje=f"Se encontraron {total_faltantes} faltantes.",
                    titulo="⚠️ Atención",
                )
            )

        if self.analisis_contenido.page:
            self.analisis_contenido.update()

    def _crear_tarjeta_analisis(self, datos: Dict) -> ft.Card:
        nombre = datos.get("nombre", "Producto")
        solicitado = datos.get("cantidad_solicitada", 0)
        posible = datos.get("cantidad_posible", 0)
        resultado = datos.get("resultado", "inviable")

        if resultado == "completo":
            color = ft.colors.GREEN
            icono = ft.icons.CHECK_CIRCLE
            estado_texto = "✅ Puede fabricarse completamente"
        elif resultado == "parcial":
            color = ft.colors.ORANGE
            icono = ft.icons.WARNING
            estado_texto = f"⚠️ Solo pueden fabricarse {posible} unidades"
        else:
            color = ft.colors.RED
            icono = ft.icons.ERROR
            estado_texto = "❌ No se puede fabricar"

        contenido = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icono, color=color, size=24),
                        ft.Text(nombre, size=16, weight="bold", expand=True),
                        ft.Text(f"Solicitado: {solicitado}", size=14),
                    ],
                    spacing=10,
                ),
                ft.Row(
                    [
                        ft.Text(f"Cantidad máxima posible: {posible}", size=14),
                        ft.Text(estado_texto, color=color, weight="bold"),
                    ],
                    spacing=20,
                ),
            ],
            spacing=5,
        )

        faltantes = datos.get("faltantes", [])
        if faltantes:
            faltantes_col = ft.Column(spacing=2)
            for falta in faltantes:
                tipo = "Empaque" if falta.get("tipo") == "empaque" else "Ingrediente"
                nombre_falta = falta.get("nombre", "Desconocido")
                faltantes_col.controls.append(
                    ft.Text(
                        f"❌ {tipo}: {nombre_falta} - Necesario: {falta['necesario']:.2f}, "
                        f"Disponible: {falta['disponible']:.2f}, Faltan: {falta['faltante']:.2f}",
                        size=12,
                        color=ft.colors.RED,
                    )
                )
            contenido.controls.append(ft.Divider(height=5))
            contenido.controls.append(ft.Text("Faltantes:", weight="bold"))
            contenido.controls.append(faltantes_col)

        # ✅ Cuando el resultado es parcial, el usuario tiene que decidir:
        # reducir la orden a lo que realmente se puede fabricar, o
        # mantener la cantidad solicitada a sabiendas de que puede
        # llegar más stock antes de iniciar la producción (la orden
        # queda "pendiente" hasta ese momento).
        if resultado == "parcial" and posible > 0:
            id_producto = datos.get("id_producto")
            decision = self._decisiones_analisis.get(id_producto)

            texto_decision = None
            if decision == "reducir":
                texto_decision = f"✅ Se va a fabricar {posible} (ajustado)."
            elif decision == "mantener":
                texto_decision = f"↪️ Se mantiene la solicitud de {solicitado}."

            contenido.controls.append(ft.Divider(height=5))
            contenido.controls.append(
                ft.Row(
                    [
                        BotonPrimario(
                            texto=f"Fabricar solamente {posible}",
                            on_click=lambda e, ip=id_producto, p=posible: self._resolver_parcial(ip, "reducir", p),
                            expand=True,
                            width=None,
                        ),
                        BotonSecundario(
                            texto=f"Conservar solicitud de {solicitado}",
                            on_click=lambda e, ip=id_producto: self._resolver_parcial(ip, "mantener", solicitado),
                            expand=True,
                            width=None,
                        ),
                    ],
                    spacing=AppSpacing.SM,
                )
            )
            if texto_decision:
                contenido.controls.append(ft.Text(texto_decision, size=12, color=ft.colors.GREY_700))

        return ft.Card(
            content=ft.Container(
                content=contenido,
                padding=AppSpacing.MD,
            ),
            elevation=2,
            margin=5,
        )

    # =========================================================
    #  LÓGICA DEL PASO 3: PLANIFICACIÓN
    # =========================================================

    def _validar_planificacion(self) -> bool:
        fecha = self.fecha_input.value or ""
        if not fecha:
            self._mostrar_error("La fecha planificada es obligatoria.")
            return False

        try:
            datetime.strptime(fecha, "%d/%m/%Y")
        except ValueError:
            self._mostrar_error("Formato de fecha inválido. Use DD/MM/AAAA.")
            return False

        return True

    # =========================================================
    #  LÓGICA DEL PASO 4: RESUMEN
    # =========================================================

    def _preparar_resumen(self):
        self.resumen_contenido.controls.clear()

        self.resumen_contenido.controls.append(
            ft.Text(
                "Resumen de la orden",
                size=AppTypography.SECTION_TITLE,
                weight="bold",
            )
        )

        productos_texto = ft.Column(spacing=5)
        for p in self.productos_seleccionados:
            productos_texto.controls.append(
                ft.Text(f"• {p['nombre']} x {p['cantidad']} unidades")
            )

        self.resumen_contenido.controls.append(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Productos:", weight="bold"),
                            productos_texto,
                        ],
                        spacing=5,
                    ),
                    ft.Container(expand=True),
                    ft.Column(
                        [
                            ft.Text("Costos estimados:", weight="bold"),
                            ft.Text(f"Total: ${self.analisis_resultados.get('costo_estimado', 0):.2f}"),
                            ft.Text(f"Tiempo estimado: {self.analisis_resultados.get('tiempo_estimado', 0)} min"),
                        ],
                        spacing=5,
                    ),
                ],
                spacing=20,
                expand=True,
            )
        )

        self.resumen_contenido.controls.append(ft.Divider(height=10))
        self.resumen_contenido.controls.append(
            ft.Row(
                [
                    ft.Text(f"Fecha: {self.fecha_input.value}", expand=True),
                    ft.Text(f"Hora: {self.hora_input.value or 'No especificada'}", expand=True),
                    ft.Text(f"Prioridad: {self.prioridad_selector.value}", expand=True),
                ],
                spacing=20,
            )
        )

        if self.responsable_input.value:
            self.resumen_contenido.controls.append(
                ft.Text(f"Responsable: {self.responsable_input.value}")
            )

        if self.observaciones_input.value:
            self.resumen_contenido.controls.append(
                ft.Text(f"Observaciones: {self.observaciones_input.value}")
            )

        total_faltantes = self.analisis_resultados.get("total_faltantes", 0)
        if total_faltantes == 0:
            self.resumen_contenido.controls.append(
                ft.Row(
                    [ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN),
                     ft.Text("✅ Todos los recursos están disponibles")],
                    spacing=10,
                )
            )
        else:
            self.resumen_contenido.controls.append(
                ft.Row(
                    [ft.Icon(ft.icons.WARNING, color=ft.colors.ORANGE),
                     ft.Text(f"⚠️ {total_faltantes} recursos faltantes (producción parcial)")],
                    spacing=10,
                )
            )

        if self.resumen_contenido.page:
            self.resumen_contenido.update()

    # =========================================================
    #  GUARDAR Y CANCELAR
    # =========================================================

    def _guardar(self, e):
        datos_orden = {
            "fecha_planificada": datetime.strptime(self.fecha_input.value, "%d/%m/%Y").date().isoformat(),
            "hora_estimada": self.hora_input.value if self.hora_input.value else None,
            "prioridad": self.prioridad_selector.value,
            "responsable": self.responsable_input.value or "",
            "notas": self.observaciones_input.value or "",
            "detalles": [
                {
                    "id_producto": p["id_producto"],
                    "cantidad": p["cantidad"],
                    "id_presentacion": p.get("id_presentacion"),
                }
                for p in self.productos_seleccionados
            ],
            "costo_estimado": self.analisis_resultados.get("costo_estimado", 0),
            "tiempo_estimado_minutos": self.analisis_resultados.get("tiempo_estimado", 0),
            "creado_por": self.page.session.get("usuario", "admin") if self.page else "admin",
        }

        resultado = self.produccion_service.crear_orden(datos_orden)
        if resultado.exito:
            self.paso_actual = 4
            self._actualizar_paso()
            self._actualizar_botones()
            if self.page:
                self.update()
            if self.on_guardar:
                self.on_guardar(resultado.datos)
        else:
            from ui.components.dialogo import Dialogo
            Dialogo.error(self.page, f"Error al crear la orden: {resultado.mensaje}")

    def _cancelar(self, e):
        if self.on_cancelar:
            self.on_cancelar()