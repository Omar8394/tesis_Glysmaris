"""
============================================================
Sistema La Dulce Tía

Archivo:
    activo_wizard.py

Responsabilidad:
    Asistente (Stepper) de dos pasos para crear/editar un activo.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.campo_texto import CampoTexto
from ui.components.selector import Selector
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.productos.stepper import Stepper
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing


class ActivoWizard(ft.Container):
    """
    Asistente de dos pasos:
    1. Información general.
    2. Configuración de costo.

    El tipo de recurso determina qué campos tienen sentido mostrar:

    - TIPOS_CON_STOCK: cosas físicas que se compran y se cuentan
      (cajas de presentación, utensilios, herramientas, mobiliario).
      Estas siempre se cobran "por unidad" y sí manejan cantidad
      en inventario.

    - TIPOS_RECURRENTES: costos del negocio que no se "cuentan"
      (agua, gas, transporte, otros gastos indirectos). Estas no
      tienen cantidad en inventario, pero sí varias modalidades
      de costo (mensual, por hora, por uso, porcentaje).
    """

    TIPOS_CON_STOCK = {"empaque", "utensilio", "herramienta", "mobiliario"}
    TIPOS_RECURRENTES = {"servicio", "costo_indirecto", "transporte", "otro"}
    # Subconjunto de TIPOS_CON_STOCK que sí se deprecia (empaque se consume,
    # no se deprecia, por eso queda fuera de este grupo).
    TIPOS_DEPRECIABLES = {"utensilio", "herramienta", "mobiliario"}
    # Herramienta y mobiliario pueden ser propios (se deprecian) o
    # alquilados (no se deprecian, se pagan como un costo recurrente).
    # Utensilio y empaque siempre se compran, por eso no entran aquí.
    TIPOS_CON_MODO_ADQUISICION = {"herramienta", "mobiliario"}

    # Unidad de medida válida según el tipo de recurso. Una lista vacía
    # significa que ese tipo no se mide en unidades físicas (ej. servicio,
    # que se describe con la modalidad de costo y "unidad_costo").
    UNIDADES_POR_TIPO = {
        "empaque": ["unidad", "kg", "g", "l", "ml", "Metro", "Centimetro"],
        "utensilio": ["unidad"],
        "herramienta": ["unidad"],
        "mobiliario": ["unidad"],
        "servicio": [],
        "transporte": ["litro", "galón", "km", "viaje"],
        "otro": ["unidad"],
    }

    def __init__(
        self,
        datos_iniciales: dict | None = None,
        on_guardar: callable | None = None,
        on_cancelar: callable | None = None,
        tipos_disponibles: list | None = None,
    ):
        super().__init__()
        self.datos_iniciales = datos_iniciales or {}
        self.on_guardar = on_guardar
        self.on_cancelar = on_cancelar
        self.tipos_disponibles = tipos_disponibles or [
            "empaque", "utensilio", "herramienta",
            "servicio", "transporte", "mobiliario", "otro"
        ]

        # --- Paso 1: Información ---
        self.nombre = CampoTexto(
            etiqueta="Nombre *",
            width=350,
            value=self.datos_iniciales.get("nombre", ""),
        )
        self.tipo = Selector(
            etiqueta="Tipo *",
            opciones=self.tipos_disponibles,
            valor=self.datos_iniciales.get("tipo"),
            width=250,
            on_change=self._actualizar_campos_por_tipo,
        )
        self.descripcion = CampoTexto(
            etiqueta="Descripción",
            multiline=True,
            width=350,
            value=self.datos_iniciales.get("descripcion", ""),
        )
        self.unidad = Selector(
            etiqueta="Unidad de medida",
            opciones=["unidad", "kg", "g", "l", "ml", "hora", "mes", "año", "servicio", "Metro", "Centimetro"],
            valor=self.datos_iniciales.get("unidad", "unidad"),
            width=200,
        )
        self.estado = Selector(
            etiqueta="Estado",
            opciones=["activo", "inactivo"],
            valor=self.datos_iniciales.get("estado", "activo"),
            width=150,
        )
        self.modo_adquisicion = Selector(
            etiqueta="Modo de adquisición",
            opciones=["comprado", "alquilado"],
            valor=self.datos_iniciales.get("modo_adquisicion", "comprado"),
            width=180,
            on_change=self._actualizar_campos_por_tipo,
        )
        self.proveedor = CampoTexto(
            etiqueta="Proveedor",
            width=250,
            value=self.datos_iniciales.get("proveedor", ""),
        )
        self.codigo_interno = CampoTexto(
            etiqueta="Código interno",
            width=200,
            value=self.datos_iniciales.get("codigo_interno", ""),
        )
        self.observaciones = CampoTexto(
            etiqueta="Observaciones",
            multiline=True,
            width=350,
            value=self.datos_iniciales.get("observaciones", ""),
        )
        self.cantidad = CampoTexto(
            etiqueta="Cantidad en inventario *",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(self.datos_iniciales.get("stock_actual", 0)),
            hint="Ej: 50 (cuánto tienes en stock)",
        )

        # --- Paso 2: Configuración de costo ---
        self.modalidad = Selector(
            etiqueta="Modalidad de costo *",
            opciones=["por_unidad", "mensual", "por_hora", "por_uso", "porcentaje"],
            valor=self.datos_iniciales.get("modalidad_costo", "por_unidad"),
            width=220,
            on_change=self._actualizar_campos_costo,
        )
        self.costo = CampoTexto(
            etiqueta="Costo unitario *",
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(self.datos_iniciales.get("costo_unitario", 0)),
        )
        self.unidad_costo = CampoTexto(
            etiqueta="Unidad de costo",
            width=180,
            value=self.datos_iniciales.get("unidad_costo", ""),
            hint="ej: hora, uso, %",
        )
        self.periodo = CampoTexto(
            etiqueta="Periodo (mensual)",
            width=180,
            value=self.datos_iniciales.get("periodo", ""),
            hint="ej: mes, trimestre",
            
        )
        self.periodo.visible = (self.modalidad.value == "mensual")
        self.ayuda_costo = ft.Text(
            "",
            size=AppTypography.SMALL,
            color="gray",
        )

        # --- Depreciación (solo utensilio/herramienta/mobiliario) ---
        self.vida_util_meses = CampoTexto(
            etiqueta="Vida útil (meses) *",
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(self.datos_iniciales.get("vida_util_meses") or ""),
            hint="Ej: 24 (2 años de uso estimado)",
        )
        self.valor_residual = CampoTexto(
            etiqueta="Valor residual",
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(self.datos_iniciales.get("valor_residual", 0) or 0),
            hint="Valor al final de su vida útil (0 si no aplica)",
        )
        self.ayuda_depreciacion = ft.Text(
            "Con esto se calcula cuánto se deprecia este activo cada mes, "
            "para repartir ese costo entre los productos que lo usan.",
            size=AppTypography.SMALL,
            color="gray",
        )
        self._actualizar_campos_costo(None)
        self._actualizar_campos_por_tipo(None)

        # --- Construcción de pasos ---
        self.paso1 = ft.Column(
            [
                ft.Text("Información del recurso", size=AppTypography.SECTION_TITLE, weight="bold"),
                ft.Row([self.nombre, self.tipo]),
                ft.Row([self.descripcion]),
                ft.Row([self.unidad, self.cantidad, self.estado, self.modo_adquisicion]),
                ft.Row([self.proveedor, self.codigo_interno]),
                ft.Row([self.observaciones]),
            ],
            spacing=AppSpacing.CONTROL_SPACING,
        )

        self.paso2 = ft.Column(
            [
                ft.Text("Configuración del costo", size=AppTypography.SECTION_TITLE, weight="bold"),
                ft.Row([self.modalidad]),
                ft.Row([self.costo, self.unidad_costo, self.periodo]),
                self.ayuda_costo,
                ft.Row([self.vida_util_meses, self.valor_residual]),
                self.ayuda_depreciacion,
            ],
            spacing=AppSpacing.CONTROL_SPACING,
        )

        # --- Stepper ---
        # ft.Stepper / ft.Step / ft.StepState no existen en Flet: son
        # controles de otros frameworks. Usamos el componente Stepper
        # propio (solo indicador visual) y manejamos el contenido de
        # cada paso manualmente con un contenedor que se reemplaza.
        self.titulos_pasos = ["Información", "Costo"]
        self.current_step = 0

        self.stepper = Stepper(
            pasos=self.titulos_pasos,
            paso_actual=self.current_step,
        )

        self.contenido_paso = ft.Container(content=self.paso1)

        # --- Botones ---
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
            texto="Guardar",
            icono=ft.icons.SAVE,
            on_click=self._guardar,
        )
        self.btn_cancelar = BotonSecundario(
            texto="Cancelar",
            icono=ft.icons.CLOSE,
            on_click=self._cancelar,
        )

        self.acciones = ft.Row(
            [self.btn_anterior, self.btn_siguiente, self.btn_guardar, self.btn_cancelar],
            spacing=AppSpacing.BUTTON_SPACING,
            alignment=ft.MainAxisAlignment.END,
        )

        self.content = ft.Column(
            [self.stepper, self.contenido_paso, self.acciones],
            spacing=AppSpacing.CONTROL_SPACING,
            width=700,
        )

        self._actualizar_botones()

    # ------------------------------------------------------------
    #  Lógica del Stepper
    # ------------------------------------------------------------

    def _actualizar_campos_costo(self, e):
        """Muestra/oculta campos según la modalidad seleccionada."""
        modalidad = self.modalidad.value
        self.periodo.visible = (modalidad == "mensual")
        self.unidad_costo.visible = (modalidad in ["por_hora", "por_uso"])
        if modalidad == "porcentaje":
            self.unidad_costo.value = "%"
            self.unidad_costo.read_only = True
        else:
            self.unidad_costo.read_only = False

        ayuda_por_modalidad = {
            "por_unidad": "Costo de comprar una sola unidad (ej: una caja, una tortera).",
            "mensual": "Costo fijo que se repite cada periodo, ej: la factura de agua o gas.",
            "por_hora": "Costo calculado según las horas que se use.",
            "por_uso": "Costo calculado según cada vez que se usa.",
            "porcentaje": "Costo calculado como un porcentaje de otro valor.",
        }
        self.ayuda_costo.value = ayuda_por_modalidad.get(modalidad, "")

        # Evita el error "Control must be added to the page first."
        # cuando este método se invoca desde __init__, antes de que
        # el wizard haya sido agregado a la página.
        if self.page:
            self.update()

    def _actualizar_campos_por_tipo(self, e):
        """
        Ajusta qué campos tienen sentido según la categoría del tipo
        seleccionado y, para herramienta/mobiliario, según si es
        comprado o alquilado (ver docstring de la clase).
        """
        tipo = self.tipo.value
        es_inventario = tipo in self.TIPOS_CON_STOCK
        es_recurrente = tipo in self.TIPOS_RECURRENTES
        puede_alquilarse = tipo in self.TIPOS_CON_MODO_ADQUISICION

        # El selector de modo de adquisición solo tiene sentido para
        # herramienta/mobiliario. Para el resto se fuerza "comprado"
        # (aunque no se muestre) para que el resto de la lógica no
        # tenga que preguntar dos veces por lo mismo.
        self.modo_adquisicion.visible = puede_alquilarse
        if not puede_alquilarse:
            self.modo_adquisicion.value = "comprado"

        alquilado = puede_alquilarse and self.modo_adquisicion.value == "alquilado"

        # La cantidad en inventario solo aplica a cosas físicas que se cuentan.
        # No tiene sentido preguntar "cuántos" de un servicio de agua.
        self.cantidad.visible = es_inventario

        # La vida útil y el valor residual solo aplican a activos propios
        # que se deprecian (utensilio siempre, herramienta/mobiliario
        # cuando son comprados). Si están alquilados no son tuyos, así
        # que no se deprecian: ese costo se maneja como costo recurrente.
        es_depreciable = tipo in self.TIPOS_DEPRECIABLES and not alquilado
        self.vida_util_meses.visible = es_depreciable
        self.valor_residual.visible = es_depreciable
        self.ayuda_depreciacion.visible = es_depreciable

        # La modalidad de costo se muestra para todo lo recurrente, y
        # también para herramienta/mobiliario cuando están alquilados
        # (ahí sí aplica "mensual" o "por_uso" en vez de "por_unidad").
        self.modalidad.visible = (not es_inventario) or alquilado

        if es_inventario and not alquilado:
            self.modalidad.value = "por_unidad"
        elif (es_recurrente or alquilado) and self.modalidad.value == "por_unidad":
            # Sugerencia razonable por defecto; el usuario puede cambiarla.
            self.modalidad.value = "mensual"

        # Unidad de medida: la lista de opciones depende del tipo. Si el
        # tipo no se mide en unidades físicas (ej. servicio), se oculta.
        unidades = self.UNIDADES_POR_TIPO.get(tipo, ["unidad"])
        self.unidad.visible = bool(unidades)
        if unidades:
            valor_actual = self.unidad.value
            self.unidad.establecer_opciones(unidades)
            self.unidad.value = valor_actual if valor_actual in unidades else unidades[0]

        self._actualizar_campos_costo(None)

        if self.page:
            self.update()

    def _ir_a_paso(self, paso: int):
        """Cambia el paso activo: actualiza indicador, contenido y botones."""
        self.current_step = paso
        self.contenido_paso.content = self.paso1 if paso == 0 else self.paso2
        self.stepper.ir_a(paso)
        self._actualizar_botones()

    def _actualizar_botones(self):
        """Muestra/oculta botones según el paso actual."""
        paso = self.current_step
        total_pasos = len(self.titulos_pasos)
        self.btn_anterior.visible = paso > 0
        self.btn_siguiente.visible = paso < total_pasos - 1
        self.btn_guardar.visible = paso == total_pasos - 1
        # Evita el error "Control must be added to the page first."
        # cuando este método se invoca desde __init__, antes de que
        # el wizard haya sido agregado a la página.
        if self.page:
            self.update()

    def _siguiente(self, e):
        """Avanza al siguiente paso."""
        if self.current_step < len(self.titulos_pasos) - 1:
            self._ir_a_paso(self.current_step + 1)
            if self.page:
                self.update()

    def _anterior(self, e):
        """Retrocede al paso anterior."""
        if self.current_step > 0:
            self._ir_a_paso(self.current_step - 1)
            if self.page:
                self.update()

    def _guardar(self, e):
        """Recoge los datos y llama al callback on_guardar."""
        datos = {
            "nombre": self.nombre.value.strip(),
            "tipo": self.tipo.value,
            "descripcion": self.descripcion.value.strip(),
            "unidad": self.unidad.value,
            "stock_actual": (
                float(self.cantidad.value)
                if self.cantidad.visible and self.cantidad.value
                else 0.0
            ),
            "estado": self.estado.value,
            "modo_adquisicion": (
                self.modo_adquisicion.value if self.modo_adquisicion.visible else None
            ),
            "proveedor": self.proveedor.value.strip(),
            "codigo_interno": self.codigo_interno.value.strip(),
            "observaciones": self.observaciones.value.strip(),
            "modalidad_costo": self.modalidad.value,
            "costo_unitario": float(self.costo.value) if self.costo.value else 0.0,
            "unidad_costo": self.unidad_costo.value.strip(),
            "periodo": self.periodo.value.strip() if self.periodo.visible else "",
            "vida_util_meses": (
                int(self.vida_util_meses.value)
                if self.vida_util_meses.visible and self.vida_util_meses.value
                else None
            ),
            "valor_residual": (
                float(self.valor_residual.value)
                if self.valor_residual.visible and self.valor_residual.value
                else 0.0
            ),
        }
        if callable(self.on_guardar):
            self.on_guardar(datos)

    def _cancelar(self, e):
        """Llama al callback on_cancelar."""
        if callable(self.on_cancelar):
            self.on_cancelar()