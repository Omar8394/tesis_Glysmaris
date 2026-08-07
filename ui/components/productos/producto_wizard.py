"""
============================================================
Sistema La Dulce Tía

Archivo:
    producto_wizard.py

Responsabilidad:
    Asistente (Wizard) para la creación/edición de productos.

    No conoce el service ni el repositorio: recibe callbacks ya
    conectados desde ProductoModule para buscar recetas,
    ingredientes, productos y activos, y para guardar el
    resultado final.

    ⚠️ El cálculo de costos (costo de receta, empaques, costos
    indirectos, mano de obra, precio sugerido) NO se hace acá.
    Ese cálculo vive en ProductoService (ver
    calcular_precio_final). Este archivo solo arma el dict de
    datos y lo entrega mediante on_guardar; quien conecte el
    service es ProductoModule.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.campo_texto import CampoTexto
from ui.components.selector import Selector
from ui.components.autocompletado import AutoCompletado
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.tarjetas import TarjetaFormulario
from ui.components.mensajes import MensajeSistema
from ui.components.productos.stepper import Stepper
from ui.components.productos.tabla_seleccion import TablaSeleccion
from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography
from ui.core.theme_manager import ThemeManager
from ui.core.icons import AppIcons


class ProductoWizard(ft.Container):
    """
    Asistente de creación de productos.

    Tipos soportados: "individual", "elaborado", "combo".
    """

    TIPOS = [
        ("individual", "Producto Individual", "Nace directamente de una receta", AppIcons.RECIPE),
        ("elaborado", "Producto Elaborado", "Se arma combinando ingredientes, productos o subproductos", ft.icons.LAYERS_OUTLINED),
        ("combo", "Combo", "Conjunto de productos vendidos como una sola unidad", ft.icons.SHOPPING_BASKET_OUTLINED),
    ]

    # Mismas etiquetas que reconoce RecetasService.UNIDADES_CANONICAS (una
    # por categoría, para no saturar el selector) -- así lo que se elige
    # acá siempre puede convertirse contra la unidad nativa del
    # ingrediente/producto en ProductoService.
    UNIDADES_COMPONENTE = ["g", "kg", "ml", "l", "cucharada", "cucharadita", "taza", "unidad", "docena"]

    PASOS_INDIVIDUAL = ["Información", "Costos", "Presentaciones", "Resumen"]
    PASOS_ELABORADO = ["Información", "Componentes", "Empaques", "Costos", "Resumen"]
    PASOS_COMBO = ["Información", "Productos", "Precio", "Resumen"]

    def __init__(
        self,
        page: ft.Page,
        on_guardar: Callable[[dict], None],
        on_cancelar: Callable[[], None],
        buscar_recetas: Callable[[str], list] | None = None,
        buscar_ingredientes: Callable[[str], list] | None = None,
        buscar_productos: Callable[[str], list] | None = None,
        buscar_empaques: Callable[[str], list] | None = None,
        buscar_costos_indirectos: Callable[[str], list] | None = None,
        calcular_preview: Callable[[dict], dict] | None = None,
        obtener_tasas_hora: Callable[[], dict] | None = None,
        categorias: list[str] | None = None,
        datos_iniciales: dict | None = None,
    ):
        super().__init__(expand=True)

        self._pagina = page
        self.tema = ThemeManager.theme
        self.on_guardar = on_guardar
        self.on_cancelar = on_cancelar

        self.buscar_recetas = buscar_recetas
        self.buscar_ingredientes = buscar_ingredientes
        self.buscar_productos = buscar_productos
        self.buscar_empaques = buscar_empaques
        self.buscar_costos_indirectos = buscar_costos_indirectos
        self.calcular_preview = calcular_preview
        self.obtener_tasas_hora = obtener_tasas_hora
        self._tasas_hora_cache: dict | None = None
        self._es_torta: bool = False

        self.categorias = categorias or [
            "Tortas", "Postres", "Cupcakes", "Donas",
            "Galletas", "Refrigerados", "Pasapalos",
            "Bebidas", "Combos", "Otros",
        ]

        # Estado del asistente
        self.tipo = None
        self.paso_actual = 0
        self.datos_iniciales = datos_iniciales or {}

        # Listas acumulativas
        self.presentaciones: list[dict] = list(self.datos_iniciales.get("presentaciones", []))
        self._empaques_presentacion_actual: list[dict] = []
        self.componentes: list[dict] = list(self.datos_iniciales.get("componentes", []))
        self.empaques: list[dict] = list(self.datos_iniciales.get("empaques", []))
        self.productos_combo: list[dict] = list(self.datos_iniciales.get("productos", []))

        # Contenedores dinámicos
        self.contenedor_stepper = ft.Container()
        self.contenedor_paso = ft.Container(expand=True)
        self.contenedor_botones = ft.Row(
            alignment=ft.MainAxisAlignment.END,
            spacing=AppSpacing.BUTTON_SPACING,
        )

        self.content = ft.Column(
            expand=True,
            spacing=AppSpacing.SECTION_SPACING,
            controls=[
                self.contenedor_stepper,
                ft.Container(expand=True, content=self.contenedor_paso),
                self.contenedor_botones,
            ],
        )

        tipo_inicial = self.datos_iniciales.get("tipo")
        if tipo_inicial in ("individual", "elaborado", "combo"):
            self._elegir_tipo(tipo_inicial)
        else:
            self._mostrar_seleccion_tipo()

    # =====================================================
    # NAVEGACIÓN GENERAL
    # =====================================================

    def _pasos_para_tipo(self):
        return {
            "individual": self.PASOS_INDIVIDUAL,
            "elaborado": self.PASOS_ELABORADO,
            "combo": self.PASOS_COMBO,
        }[self.tipo]

    def _renderizar_stepper(self):
        if self.tipo is None:
            self._stepper_instancia = None
            self.contenedor_stepper.content = ft.Container()
            return

        # ✅ Antes se creaba un Stepper nuevo en cada cambio de paso.
        # Ahora se reusa la misma instancia (vía ir_a) mientras el tipo
        # de producto no cambie -- Stepper.ir_a() ya existía pero no se
        # llamaba desde ningún lado.
        pasos_actuales = self._pasos_para_tipo()
        stepper_existente = getattr(self, "_stepper_instancia", None)
        if stepper_existente is not None and stepper_existente.pasos == pasos_actuales:
            stepper_existente.ir_a(self.paso_actual)
        else:
            self._stepper_instancia = Stepper(
                pasos=pasos_actuales,
                paso_actual=self.paso_actual,
            )
            self.contenedor_stepper.content = self._stepper_instancia

    def _renderizar_botones(self):
        if self.tipo is None:
            botones = [
                BotonSecundario(
                    texto="Cancelar",
                    icono=AppIcons.CANCEL,
                    on_click=lambda e: self._cancelar(),
                ),
            ]
        else:
            # ✅ "Cambiar tipo" es más largo que "Atrás"; el fix de fondo
            # (que BotonSecundario/BotonPrimario no desborden con
            # textos largos) va en boton.py, pero mientras tanto le
            # pasamos un ancho explícito más generoso a este botón en
            # particular para que el texto entre completo.
            botones = [
                BotonSecundario(
                    texto="Atrás" if self.paso_actual > 0 else "Cambiar tipo",
                    icono=AppIcons.BACK,
                    width=None if self.paso_actual > 0 else 170,
                    on_click=lambda e: self._atras(),
                ),
            ]
            es_ultimo_paso = self.paso_actual == len(self._pasos_para_tipo()) - 1
            botones.append(
                BotonPrimario(
                    texto="Guardar" if es_ultimo_paso else "Siguiente",
                    icono=AppIcons.SAVE if es_ultimo_paso else AppIcons.NEXT,
                    on_click=(lambda e: self._guardar()) if es_ultimo_paso else (lambda e: self._siguiente()),
                )
            )
        self.contenedor_botones.controls = botones

    def _refrescar(self):
        self._renderizar_stepper()
        self._renderizar_botones()
        if self.page:
            self.update()

    # =====================================================
    # PASO 0: SELECCIÓN DE TIPO
    # =====================================================

    def _mostrar_seleccion_tipo(self):
        self.tipo = None
        tarjetas = []
        for clave, titulo, descripcion, icono in self.TIPOS:
            tarjetas.append(
                ft.Container(
                    width=220,
                    height=170,
                    padding=AppSpacing.LG,
                    border_radius=10,
                    bgcolor=self.tema.card,
                    border=ft.border.all(1, self.tema.border),
                    ink=True,
                    on_click=lambda e, t=clave: self._elegir_tipo(t),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Icon(icono, size=32, color=self.tema.primary),
                            ft.Text(titulo, weight=AppTypography.BOLD, size=AppTypography.CARD_TITLE),
                            ft.Text(descripcion, size=AppTypography.SMALL, color=self.tema.text_secondary),
                        ],
                    ),
                )
            )
        self.contenedor_paso.content = ft.Column(
            spacing=AppSpacing.LG,
            controls=[
                ft.Text("¿Qué querés crear?", size=AppTypography.SECTION_TITLE, weight=AppTypography.BOLD),
                ft.Row(wrap=True, spacing=AppSpacing.MD, controls=tarjetas),
            ],
        )
        self._refrescar()

    def _elegir_tipo(self, tipo):
        self.tipo = tipo
        self.paso_actual = 0
        self._mostrar_paso_actual()

    # =====================================================
    # DESPACHADOR DE PASOS
    # =====================================================

    def _mostrar_paso_actual(self):
        nombre_paso = self._pasos_para_tipo()[self.paso_actual]
        mapa = {
            "Información": self._paso_informacion,
            "Presentaciones": self._paso_presentaciones,
            "Componentes": self._paso_componentes,
            "Empaques": self._paso_empaques,
            "Costos": self._paso_costos,
            "Productos": self._paso_productos_combo,
            "Precio": self._paso_precio_combo,
            "Resumen": self._paso_resumen,
        }
        self.contenedor_paso.content = mapa[nombre_paso]()
        self._refrescar()

    def _siguiente(self):
        if not self._validar_paso_actual():
            return
        if self.paso_actual < len(self._pasos_para_tipo()) - 1:
            self.paso_actual += 1
            self._mostrar_paso_actual()

    def _atras(self):
        if self.paso_actual == 0:
            self._mostrar_seleccion_tipo()
        else:
            self.paso_actual -= 1
            self._mostrar_paso_actual()

    def _cancelar(self):
        if self.on_cancelar:
            self.on_cancelar()

    def _validar_paso_actual(self) -> bool:
        nombre_paso = self._pasos_para_tipo()[self.paso_actual]

        if nombre_paso == "Información":
            if not self.txt_nombre.value or not self.txt_nombre.value.strip():
                self.txt_nombre.error_text = "El nombre es obligatorio."
                self.txt_nombre.update()
                return False
            self.txt_nombre.error_text = None
            self.txt_nombre.update()

            if self.tipo == "individual":
                if not self.autocompletado_receta.obtener():
                    self._mostrar_error_paso("Debés seleccionar una receta.")
                    return False
                if not self._obtener_id_seleccionado(self.autocompletado_receta, "la receta"):
                    return False

        elif nombre_paso == "Presentaciones" and self.tipo == "individual":
            # ✅ Antes solo el service (al guardar) exigía al menos una
            # presentación en productos individuales que no son torta;
            # ahora se bloquea acá para no dejar avanzar todo el wizard
            # y enterarse recién en "Guardar".
            if self._es_torta:
                if not self.txt_diametro.value or not self.txt_diametro.value.strip():
                    self._mostrar_error_paso("El diámetro es obligatorio para una torta.")
                    return False
            elif not self.presentaciones:
                self._mostrar_error_paso("Agregá al menos una presentación antes de continuar.")
                return False

        elif nombre_paso == "Componentes" and self.tipo == "elaborado":
            if not self.componentes:
                self._mostrar_error_paso("Agregá al menos un componente antes de continuar.")
                return False

        elif nombre_paso == "Productos" and self.tipo == "combo":
            if not self.productos_combo:
                self._mostrar_error_paso("Agregá al menos un producto al combo antes de continuar.")
                return False

        elif nombre_paso == "Precio" and self.tipo == "combo":
            if not self.txt_precio_combo.value or not self.txt_precio_combo.value.strip():
                self._mostrar_error_paso("El precio del combo es obligatorio.")
                return False

        return True

    def _mostrar_error_paso(self, mensaje: str):
        """Muestra un aviso breve de validación (mismo mecanismo que usa el resto del sistema)."""
        MensajeSistema.error(self._pagina, mensaje)

    def _obtener_id_seleccionado(self, autocompletado, entidad: str):
        """
        Devuelve el id de lo que el usuario eligió en `autocompletado`
        (una receta, ingrediente, producto, empaque, etc.), o None si
        hay texto en el campo pero no corresponde a ninguna selección
        real de la lista de sugerencias.

        ⚠️ AutoCompletado._seleccionado (y por lo tanto obtener_id())
        solo se fija cuando el usuario hace clic en un ítem de la
        lista de sugerencias. Si escribe el nombre exacto y sigue de
        largo (Tab, clic en otro campo) sin clickear la sugerencia, el
        campo se ve perfecto pero obtener_id() devuelve None -- y
        quien llame a esto (_agregar_componente, _agregar_empaque,
        _agregar_producto_combo, _agregar_empaque_presentacion, o el
        id_receta de "Información") terminaba agregando el ítem con
        id=None sin ningún aviso. ProductoService trata ese id=None
        como costo $0 en silencio (así apareció el $4.27 en vez de
        $8.96: la receta se guardó sin id). Este método centraliza el
        chequeo para que ningún punto de selección se olvide de
        hacerlo.
        """
        id_valor = getattr(autocompletado, "obtener_id", lambda: None)()
        if autocompletado.obtener() and not id_valor:
            self._mostrar_error_paso(
                f"Elegí {entidad} de la lista de sugerencias (no alcanza con escribir el nombre)."
            )
            return None
        return id_valor

    # Nuevo método:
    def _actualizar_es_torta(self, e=None):
        self._es_torta = (self.dd_categoria.value or "") == "Tortas"

    # =====================================================
    # PASO: INFORMACIÓN
    # =====================================================

    def _paso_informacion(self):
        datos = self.datos_iniciales
        self.txt_nombre = CampoTexto(
            etiqueta="Nombre del producto",
            width=350,
            value=datos.get("nombre", ""),
        )

        self.dd_categoria = Selector(
        etiqueta="Categoría",
        opciones=self.categorias,
        valor=datos.get("categoria"),
        width=250,
        on_change=self._actualizar_es_torta,   # 👈 nuevo
        )
        self._actualizar_es_torta() 
        
        self.txt_descripcion = CampoTexto(
            etiqueta="Descripción",
            multiline=True,
            width=610,
            value=datos.get("descripcion", ""),
        )

        controles = [
            ft.Row([self.txt_nombre, self.dd_categoria], spacing=AppSpacing.CONTROL_SPACING),
        ]

        if self.tipo == "individual":
            self.autocompletado_receta = AutoCompletado(
                etiqueta="Receta",
                buscar=self.buscar_recetas,
                width=350,
            )
            if datos.get("nombre_receta"):
                self.autocompletado_receta.establecer(datos.get("nombre_receta"), id=datos.get("receta_id"))
            controles.append(self.autocompletado_receta)

        if self.tipo == "elaborado":
            # ✅ Un producto individual ya tiene una unidad "nativa" (la
            # de su receta: rendimiento_unidad). Un elaborado no tiene
            # receta propia, así que sin este campo no había forma de
            # saber en qué unidad está expresado su costo cuando OTRO
            # producto elaborado lo usa como componente (ver
            # unidad_base / ProductoService._unidad_base_producto).
            self.dd_unidad_base = Selector(
                etiqueta="Unidad de este producto (para usarlo como componente de otro)",
                opciones=self.UNIDADES_COMPONENTE,
                valor=datos.get("unidad_base") or "unidad",
                width=350,
            )
            controles.append(self.dd_unidad_base)

        controles.append(self.txt_descripcion)
        return TarjetaFormulario(
            titulo="Información del producto",
            contenido=controles,
            expand=True,
        )

    # =====================================================
    # PASO: PRESENTACIONES (solo Producto Individual)
    # =====================================================

    def _paso_presentaciones(self):
        datos = self.datos_iniciales
        # ✅ Antes esta línea repetía la misma lógica que
        # _actualizar_es_torta(); ahora ese método es la única fuente
        # de verdad para el criterio "¿es torta?".
        self._actualizar_es_torta()

        controles: list = []

        if self._es_torta:
            # ─── Campos globales para la torta ───
            self.txt_diametro = CampoTexto(
                etiqueta="Diámetro (cm)",
                width=140,
                keyboard_type=ft.KeyboardType.NUMBER,
                value=datos.get("diametro_cm", ""),
            )
            self.dd_tipo_venta = Selector(
                etiqueta="Venta",
                opciones=["Completa", "Por trozos"],
                valor=datos.get("tipo_venta", "Completa"),
                width=160,
                on_change=self._alternar_campos_trozos,
            )
            self.txt_cantidad_trozos = CampoTexto(
                etiqueta="Cantidad de trozos",
                width=160,
                keyboard_type=ft.KeyboardType.NUMBER,
                visible=(self.dd_tipo_venta.value == "Por trozos"),
                value=datos.get("cantidad_trozos", ""),
                on_change=self._actualizar_precio_sugerido,
            )
            controles.append(
                ft.Row(
                    [self.txt_diametro, self.dd_tipo_venta, self.txt_cantidad_trozos],
                    spacing=AppSpacing.CONTROL_SPACING,
                )
            )
            controles.append(ft.Divider())

            # ─── Empaques de la presentación (única) ───
            self.autocompletado_presentacion_empaque = AutoCompletado(
                etiqueta="Empaque",
                buscar=self.buscar_empaques,
                width=260,
            )
            self.txt_presentacion_empaque_cantidad = CampoTexto(
                etiqueta="Cantidad",
                width=100,
                value="1",
                keyboard_type=ft.KeyboardType.NUMBER,
            )
            boton_agregar_empaque = ft.IconButton(
                icon=AppIcons.ADD,
                tooltip="Agregar empaque a esta presentación",
                on_click=self._agregar_empaque_presentacion,
            )
            self.tabla_empaques_presentacion = TablaSeleccion(
                columnas=[("nombre", "Empaque"), ("cantidad", "Cantidad")],
                on_eliminar=self._quitar_empaque_presentacion,
            )
            self.tabla_empaques_presentacion.reemplazar(self._empaques_presentacion_actual)

            # ─── Precio sugerido / manual ───
            precio_sugerido_inicial = self._precio_sugerido_actual()
            self.txt_presentacion_precio_sugerido = CampoTexto(
                etiqueta="Precio sugerido",
                width=140,
                read_only=True,
                value=f"{precio_sugerido_inicial:.2f}",
            )
            self.txt_presentacion_precio_manual = CampoTexto(
                etiqueta="Precio manual (opcional)",
                width=170,
                hint="Vacío = usar el sugerido",
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            controles.extend([
                ft.Text("Empaques de esta presentación", weight=AppTypography.MEDIUM, size=AppTypography.SMALL),
                ft.Row(
                    [self.autocompletado_presentacion_empaque, self.txt_presentacion_empaque_cantidad, boton_agregar_empaque],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                self.tabla_empaques_presentacion,
                ft.Row(
                    [self.txt_presentacion_precio_sugerido, self.txt_presentacion_precio_manual],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
            ])

        else:
            # ─── Presentación genérica (cualquier individual que NO
            # sea de categoría "Tortas": galletas, cupcakes, donas,
            # bebidas, etc.). Antes esta rama repetía el vocabulario de
            # tortas (Diámetro, Completa/Por trozos), que no aplica a
            # este tipo de producto -- ahora es "nombre de la
            # presentación" + "cuántas unidades incluye" (por ejemplo
            # "Caja x6" con cantidad_unidades=6, o "Unidad" con 1).
            self.txt_presentacion_nombre = CampoTexto(
                etiqueta="Presentación (ej. Unidad, Caja x6, Docena)",
                width=260,
            )
            self.txt_presentacion_cantidad_unidades = CampoTexto(
                etiqueta="Unidades que incluye",
                width=160,
                hint="Ej: 1, 6, 12",
                value="1",
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=self._actualizar_precio_sugerido_original,
            )

            self.autocompletado_presentacion_empaque = AutoCompletado(
                etiqueta="Empaque",
                buscar=self.buscar_empaques,
                width=260,
            )
            self.txt_presentacion_empaque_cantidad = CampoTexto(
                etiqueta="Cantidad",
                width=100,
                value="1",
                keyboard_type=ft.KeyboardType.NUMBER,
            )
            boton_agregar_empaque = ft.IconButton(
                icon=AppIcons.ADD,
                tooltip="Agregar empaque a esta presentación",
                on_click=self._agregar_empaque_presentacion,
            )
            self.tabla_empaques_presentacion = TablaSeleccion(
                columnas=[("nombre", "Empaque"), ("cantidad", "Cantidad")],
                on_eliminar=self._quitar_empaque_presentacion,
            )
            self.tabla_empaques_presentacion.reemplazar(self._empaques_presentacion_actual)

            precio_sugerido_inicial = self._precio_sugerido_actual(100, None)
            self.txt_presentacion_precio_sugerido = CampoTexto(
                etiqueta="Precio sugerido",
                width=140,
                read_only=True,
                value=f"{precio_sugerido_inicial:.2f}",
            )
            self.txt_presentacion_precio_manual = CampoTexto(
                etiqueta="Precio manual (opcional)",
                width=170,
                hint="Vacío = usar el sugerido",
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            self.tabla_presentaciones = TablaSeleccion(
                columnas=[
                    ("nombre", "Presentación"),
                    ("detalle", "Detalle"),
                    ("empaque", "Empaque"),
                    ("precio", "Precio"),
                ],
                on_eliminar=self._quitar_presentacion,
            )
            self.tabla_presentaciones.reemplazar(self._filas_presentaciones())
            boton_agregar = ft.IconButton(
                icon=AppIcons.ADD,
                tooltip="Agregar presentación",
                on_click=self._agregar_presentacion,
            )

            controles.extend([
                ft.Row([self.txt_presentacion_nombre, self.txt_presentacion_cantidad_unidades], spacing=AppSpacing.CONTROL_SPACING),
                ft.Text("Empaques de esta presentación", weight=AppTypography.MEDIUM, size=AppTypography.SMALL),
                ft.Row(
                    [self.autocompletado_presentacion_empaque, self.txt_presentacion_empaque_cantidad, boton_agregar_empaque],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                self.tabla_empaques_presentacion,
                ft.Row(
                    [self.txt_presentacion_precio_sugerido, self.txt_presentacion_precio_manual, boton_agregar],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                self.tabla_presentaciones,
            ])

        return TarjetaFormulario(
            titulo="Presentaciones disponibles",
            subtitulo=(
                "Define cómo se vende este producto. El precio sugerido usa el costo, el empaque y el margen; "
                "podés ajustarlo a mano si querés."
            ),
            contenido=controles,
            expand=True,
        )

    # ─── Helpers para torta ───

    def _alternar_campos_trozos(self, e=None):
        """Muestra/oculta el campo de cantidad de trozos según el tipo de venta (torta)."""
        mostrar = self.dd_tipo_venta.value == "Por trozos"
        self.txt_cantidad_trozos.visible = mostrar
        if self.txt_cantidad_trozos.page:
            self.txt_cantidad_trozos.update()
        self._actualizar_precio_sugerido()

    def _actualizar_margen(self, e=None):
        """El margen afecta el precio sugerido tanto de tortas (paso Presentaciones) como de elaborados (paso Costos)."""
        self._actualizar_precio_sugerido()
        self._actualizar_precio_sugerido_elaborado()

    def _actualizar_precio_sugerido(self, e=None):
        """Recalcula el precio sugerido para tortas."""
        if not self._es_torta:
            return
        if not hasattr(self, "dd_tipo_venta") or not hasattr(self, "txt_presentacion_precio_sugerido"):
            return

        if self.dd_tipo_venta.value == "Por trozos":
            try:
                cantidad = float(self.txt_cantidad_trozos.value or 0)
            except ValueError:
                cantidad = 0
            fraccion = round(100 / cantidad, 4) if cantidad else 0.0
        else:
            fraccion = 100.0

        sugerido = self._precio_sugerido_actual(fraccion, self._empaques_presentacion_actual)
        self.txt_presentacion_precio_sugerido.value = f"{sugerido:.2f}"
        if self.txt_presentacion_precio_sugerido.page:
            self.txt_presentacion_precio_sugerido.update()

    def _actualizar_precio_sugerido_original(self, e=None):
        """
        Precio sugerido para presentaciones genéricas (no torta): el
        costo base del producto multiplicado por la cantidad de
        unidades que incluye esta presentación (1 para "Unidad", 6
        para "Caja x6", etc.), más sus propios empaques.
        """
        if self._es_torta:
            return
        if not hasattr(self, "txt_presentacion_cantidad_unidades") or not hasattr(self, "txt_presentacion_precio_sugerido"):
            return

        try:
            unidades = float(self.txt_presentacion_cantidad_unidades.value or 1) or 1
        except ValueError:
            unidades = 1

        sugerido = self._precio_sugerido_actual(unidades * 100, self._empaques_presentacion_actual)
        self.txt_presentacion_precio_sugerido.value = f"{sugerido:.2f}"
        if self.txt_presentacion_precio_sugerido.page:
            self.txt_presentacion_precio_sugerido.update()

    def _agregar_empaque_presentacion(self, e):
        """Agrega un empaque a la lista de la presentación actual."""
        nombre = self.autocompletado_presentacion_empaque.obtener()
        if not nombre:
            return

        id_activo = self._obtener_id_seleccionado(self.autocompletado_presentacion_empaque, "el empaque")
        if not id_activo:
            return
        try:
            cantidad = float(self.txt_presentacion_empaque_cantidad.value or 1) or 1
        except ValueError:
            cantidad = 1

        self._empaques_presentacion_actual.append({
            "nombre": nombre,
            "id_activo": id_activo,
            "cantidad": cantidad,
        })
        self.tabla_empaques_presentacion.reemplazar(self._empaques_presentacion_actual)
        self.autocompletado_presentacion_empaque.limpiar()
        self.txt_presentacion_empaque_cantidad.value = "1"
        self.txt_presentacion_empaque_cantidad.update()
        self._actualizar_precio_sugerido()

    def _quitar_empaque_presentacion(self, indice):
        """Callback de TablaSeleccion: quita un empaque de la lista real
        de la presentación actual (torta o genérica) y re-renderiza."""
        if 0 <= indice < len(self._empaques_presentacion_actual):
            self._empaques_presentacion_actual.pop(indice)
            self.tabla_empaques_presentacion.reemplazar(self._empaques_presentacion_actual)
            self._actualizar_precio_sugerido()
            self._actualizar_precio_sugerido_original()

    # ─── Lógica de presentaciones para no-torta ───

    def _filas_presentaciones(self) -> list[dict]:
        filas = []
        for p in self.presentaciones:
            unidades = p.get("cantidad_unidades", 1)
            detalle = "1 unidad" if unidades == 1 else f"{unidades} unidades"
            empaques = p.get("empaques") or []
            texto_empaques = ", ".join(emp["nombre"] for emp in empaques) if empaques else "-"
            filas.append({
                "nombre": p.get("nombre"),
                "detalle": detalle,
                "empaque": texto_empaques,
                "precio": p.get("precio"),
            })
        return filas

    def _agregar_presentacion(self, e):
        """Agrega una presentación a la tabla (solo para no-torta)."""
        if self._es_torta:
            return
        nombre = (self.txt_presentacion_nombre.value or "").strip()
        if not nombre:
            return

        try:
            unidades = float(self.txt_presentacion_cantidad_unidades.value or 1) or 1
        except ValueError:
            unidades = 1
        fraccion = unidades * 100

        empaques = self._empaques_presentacion_actual.copy()
        precio_manual = (self.txt_presentacion_precio_manual.value or "").strip()
        precio_manual_valido = None
        if precio_manual:
            try:
                precio_manual_valido = float(precio_manual)
            except ValueError:
                precio_manual_valido = None

        # ✅ "precio" sigue usándose para mostrar en la tabla y como
        # precio de venta de esta presentación puntual (si el usuario
        # no escribió nada, se muestra la preview del wizard como
        # referencia). Pero "precio_manual" indica si ese valor vino
        # realmente del usuario o es solo la estimación del wizard --
        # eso es lo que decide, en _guardar(), si se le manda
        # precio_venta al backend o se deja que calcule el suyo propio
        # (ver _guardar: antes se mandaba siempre, pisando el precio
        # correcto que arma el service con costo_receta + mano de obra
        # + indirectos).
        precio = precio_manual_valido if precio_manual_valido is not None else self._precio_sugerido_actual(fraccion, empaques)

        self.presentaciones.append({
            "nombre": nombre,
            "cantidad_unidades": unidades,
            "empaques": empaques,
            "precio": precio,
            "precio_manual": precio_manual_valido is not None,
        })
        self.tabla_presentaciones.reemplazar(self._filas_presentaciones())

        # Limpiar campos
        self.txt_presentacion_nombre.value = ""
        self.txt_presentacion_cantidad_unidades.value = "1"
        self.autocompletado_presentacion_empaque.limpiar()
        self.txt_presentacion_precio_manual.value = ""
        self._empaques_presentacion_actual.clear()
        self.tabla_empaques_presentacion.reemplazar([])
        self._actualizar_precio_sugerido_original()

    def _quitar_presentacion(self, indice):
        """Callback de TablaSeleccion: quita una presentación de la
        lista real self.presentaciones y re-renderiza la tabla."""
        if 0 <= indice < len(self.presentaciones):
            self.presentaciones.pop(indice)
            self.tabla_presentaciones.reemplazar(self._filas_presentaciones())

    # ─── Cálculo de precio sugerido ───

    def _armar_datos_parciales_para_preview(self, empaques: list[dict] | None = None) -> dict:
        """
        Arma un dict parcial para que el service calcule costo/precio en
        vivo, según el tipo de producto real del wizard (antes esto
        tenía "tipo": "individual" fijo, así que pedir un preview desde
        el paso de Costos de un producto elaborado siempre calculaba
        como si fuera individual).
        """
        try:
            horas = float(self.txt_tiempo_preparacion.value or 0)
        except (ValueError, AttributeError):
            horas = 0.0

        datos = {
            "tipo": self.tipo or "individual",
            "empaques": empaques if empaques is not None else list(getattr(self, "empaques", [])),
            "costos_indirectos_monto": self._costos_indirectos_estimados(horas),
            "mano_obra": self._mano_obra_estimada(horas),
            "margen_porcentaje": float(getattr(self, "txt_margen", None) and self.txt_margen.value or 40),
        }

        if self.tipo == "individual":
            datos["id_receta"] = getattr(self.autocompletado_receta, "obtener_id", lambda: None)()
        elif self.tipo == "elaborado":
            datos["componentes"] = list(getattr(self, "componentes", []))

        return datos

    def _precio_sugerido_actual(self, fraccion: float = 100.0, empaques: list[dict] | None = None) -> float:
        """Devuelve el precio sugerido para una fracción del producto."""
        if not self.calcular_preview:
            return 0.0
        try:
            datos_parciales = self._armar_datos_parciales_para_preview(empaques)
            resultado = self.calcular_preview(datos_parciales) or {}
        except Exception:
            return 0.0
        precio_total = float(resultado.get("precio_final", 0) or 0)
        return round(precio_total * (fraccion / 100), 2)

    # ─── Consolidación de empaques para el producto ───

    def _consolidar_empaques_presentaciones(self) -> list[dict]:
        """Junta los empaques de todas las presentaciones (para no-torta)."""
        acumulado: dict[int, dict] = {}
        for p in self.presentaciones:
            for empaque in (p.get("empaques") or []):
                if not empaque or not empaque.get("id_activo"):
                    continue
                id_activo = empaque["id_activo"]
                if id_activo not in acumulado:
                    acumulado[id_activo] = dict(empaque)
                else:
                    acumulado[id_activo]["cantidad"] = acumulado[id_activo].get("cantidad", 1) + empaque.get("cantidad", 1)
        return list(acumulado.values())

    # =====================================================
    # PASO: COMPONENTES (Elaborado)
    # =====================================================

    def _paso_componentes(self):
        self.dd_tipo_componente = Selector(
            etiqueta="Tipo",
            opciones=["Ingrediente", "Producto", "Subproducto"],
            width=170,
        )
        self.autocompletado_componente = AutoCompletado(
            etiqueta="Nombre",
            buscar=self._buscar_componente,
            width=260,
        )
        self.txt_componente_cantidad = CampoTexto(
            etiqueta="Cantidad",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        # ✅ Antes no había forma de indicar en qué unidad se cargaba la
        # cantidad: siempre se asumía (en silencio) la unidad nativa del
        # ingrediente/producto, así que cargar "0.5" para algo que se
        # guarda en gramos significaba medio gramo, no medio kilo. Ahora
        # el usuario elige la unidad y ProductoService la convierte (o
        # rechaza el guardado si es de otra magnitud, ej. ml para algo
        # en gramos).
        self.dd_componente_unidad = Selector(
            etiqueta="Unidad",
            opciones=self.UNIDADES_COMPONENTE,
            width=130,
        )
        self.tabla_componentes = TablaSeleccion(
            columnas=[("tipo", "Tipo"), ("nombre", "Nombre"), ("cantidad", "Cantidad"), ("unidad", "Unidad")],
            on_eliminar=self._quitar_componente,
        )
        self.tabla_componentes.reemplazar(self.componentes)
        boton_agregar = ft.IconButton(
            icon=AppIcons.ADD,
            tooltip="Agregar componente",
            on_click=self._agregar_componente,
        )
        return TarjetaFormulario(
            titulo="Componentes del producto",
            subtitulo="Ingredientes, productos o subproductos que forman este artículo. La unidad debe ser coherente con la del componente (no se puede usar ml para algo que se guarda en gramos).",
            contenido=[
                ft.Row(
                    [self.dd_tipo_componente, self.autocompletado_componente, self.txt_componente_cantidad, self.dd_componente_unidad, boton_agregar],
                    spacing=AppSpacing.CONTROL_SPACING,
                    wrap=True,
                ),
                self.tabla_componentes,
            ],
            expand=True,
        )

    def _buscar_componente(self, texto):
        tipo = self.dd_tipo_componente.value or "Ingrediente"
        if tipo == "Ingrediente" and self.buscar_ingredientes:
            return self.buscar_ingredientes(texto)
        if tipo == "Producto" and self.buscar_productos:
            return self.buscar_productos(texto)
        if tipo == "Subproducto" and self.buscar_productos:
            return self.buscar_productos(texto)
        return []

    def _agregar_componente(self, e):
        nombre = self.autocompletado_componente.obtener()
        if not nombre:
            return
        id_componente = self._obtener_id_seleccionado(self.autocompletado_componente, "el componente")
        if not id_componente:
            return
        try:
            cantidad = float(self.txt_componente_cantidad.value or 0)
        except ValueError:
            cantidad = 0
        self.componentes.append({
            "tipo": (self.dd_tipo_componente.value or "Ingrediente").lower(),
            "nombre": nombre,
            "id": id_componente,
            "cantidad": cantidad,
            "unidad": self.dd_componente_unidad.value or "unidad",
        })
        self.tabla_componentes.reemplazar(self.componentes)
        self.autocompletado_componente.limpiar()
        self.txt_componente_cantidad.value = ""
        self.txt_componente_cantidad.update()

    def _quitar_componente(self, indice):
        """Callback de TablaSeleccion: quita un componente de la lista
        real self.componentes y re-renderiza la tabla."""
        if 0 <= indice < len(self.componentes):
            self.componentes.pop(indice)
            self.tabla_componentes.reemplazar(self.componentes)

    # =====================================================
    # PASO: EMPAQUES (Elaborado)
    # =====================================================

    def _paso_empaques(self):
        self.autocompletado_empaque = AutoCompletado(
            etiqueta="Seleccionar empaque",
            buscar=self.buscar_empaques,
            width=300,
        )
        self.txt_empaque_cantidad = CampoTexto(
            etiqueta="Cantidad",
            width=120,
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.tabla_empaques = TablaSeleccion(
            columnas=[("nombre", "Empaque"), ("cantidad", "Cantidad")],
            on_eliminar=self._quitar_empaque,
        )
        self.tabla_empaques.reemplazar(self.empaques)
        boton_agregar = ft.IconButton(
            icon=AppIcons.ADD,
            tooltip="Agregar empaque",
            on_click=self._agregar_empaque,
        )
        return TarjetaFormulario(
            titulo="Empaques",
            subtitulo="Los empaques son activos del inventario. Se reutilizan entre productos.",
            contenido=[
                ft.Row(
                    [self.autocompletado_empaque, self.txt_empaque_cantidad, boton_agregar],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                self.tabla_empaques,
            ],
            expand=True,
        )

    def _agregar_empaque(self, e):
        nombre = self.autocompletado_empaque.obtener()
        if not nombre:
            return
        id_activo = self._obtener_id_seleccionado(self.autocompletado_empaque, "el empaque")
        if not id_activo:
            return
        try:
            cantidad = float(self.txt_empaque_cantidad.value or 1)
        except ValueError:
            cantidad = 1
        self.empaques.append({"nombre": nombre, "id_activo": id_activo, "cantidad": cantidad})
        self.tabla_empaques.reemplazar(self.empaques)
        self.autocompletado_empaque.limpiar()
        self.txt_empaque_cantidad.value = "1"
        self.txt_empaque_cantidad.update()

    def _quitar_empaque(self, indice):
        """Callback de TablaSeleccion: quita un empaque de la lista
        real self.empaques y re-renderiza la tabla."""
        if 0 <= indice < len(self.empaques):
            self.empaques.pop(indice)
            self.tabla_empaques.reemplazar(self.empaques)

    # =====================================================
    # PASO: COSTOS (Individual y Elaborado)
    # =====================================================

    def _paso_costos(self):
        datos = self.datos_iniciales
        minutos_iniciales = datos.get("tiempo_preparacion_minutos") or 0
        try:
            horas_iniciales = round(float(minutos_iniciales) / 60, 2) if minutos_iniciales else 0.0
        except (TypeError, ValueError):
            horas_iniciales = 0.0

        self.txt_tiempo_preparacion = CampoTexto(
            etiqueta="¿Cuánto tiempo toma preparar y hornear este producto? (horas)",
            width=320,
            hint="Ej: 2",
            value=str(horas_iniciales) if horas_iniciales else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._actualizar_estimados_costos,
        )
        self.txt_margen = CampoTexto(
            etiqueta="Margen de ganancia (%)",
            width=170,
            hint="Ej: 40",
            value=str(datos.get("margen_porcentaje", 40)),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._actualizar_margen,
        )

        self.txt_mano_obra_estimada = CampoTexto(
            etiqueta="Mano de obra (calculada)",
            width=190,
            read_only=True,
            value=f"${self._mano_obra_estimada(horas_iniciales):.2f}",
        )
        self.txt_costos_indirectos_estimados = CampoTexto(
            etiqueta="Costos indirectos (calculados)",
            width=210,
            read_only=True,
            value=f"${self._costos_indirectos_estimados(horas_iniciales):.2f}",
        )

        contenido = [
            ft.Row([self.txt_tiempo_preparacion, self.txt_margen], spacing=AppSpacing.CONTROL_SPACING),
            ft.Row([self.txt_mano_obra_estimada, self.txt_costos_indirectos_estimados], spacing=AppSpacing.CONTROL_SPACING),
        ]

        # ✅ Los productos "elaborado" no pasan por el paso de
        # Presentaciones (eso es solo para "individual"), así que este
        # es el único lugar donde pueden fijar su precio de venta. El
        # sugerido se recalcula solo; el campo de venta queda vacío
        # (= usar el sugerido) salvo que el usuario escriba el suyo.
        if self.tipo == "elaborado":
            precio_sugerido_inicial = self._precio_sugerido_actual()
            self.txt_precio_sugerido = CampoTexto(
                etiqueta="Precio sugerido",
                width=170,
                read_only=True,
                value=f"{precio_sugerido_inicial:.2f}",
            )
            precio_venta_inicial = datos.get("precio_venta") or datos.get("precio_final")
            self.txt_precio_venta = CampoTexto(
                etiqueta="Precio de venta",
                width=170,
                hint="Vacío = usar el sugerido",
                keyboard_type=ft.KeyboardType.NUMBER,
                value=str(precio_venta_inicial) if precio_venta_inicial else "",
            )
            contenido.append(
                ft.Row(
                    [self.txt_precio_sugerido, self.txt_precio_venta],
                    spacing=AppSpacing.CONTROL_SPACING,
                )
            )

        tasas = self._obtener_tasas_hora()
        if not tasas or not tasas.get("costo_hora_total"):
            contenido.append(
                ft.Container(
                    padding=AppSpacing.SM,
                    border_radius=8,
                    bgcolor=self.tema.warning + "15",
                    content=ft.Text(
                        "Todavía no cargaste el valor de tu hora en Mi Negocio "
                        "(o no hay servicios/herramientas en Activos), así que "
                        "la mano de obra y los costos indirectos calculados dan $0.",
                        size=AppTypography.SMALL,
                        color=self.tema.warning,
                    ),
                )
            )

        return TarjetaFormulario(
            titulo="Costos",
            subtitulo=(
                "Solo necesitamos el tiempo que lleva preparar este producto. "
                "La mano de obra y los costos indirectos se calculan solos, "
                "usando las tasas por hora que ya cargaste en Mi Negocio."
            ),
            contenido=contenido,
            expand=True,
        )

    # ─── Cálculo de mano de obra / costos indirectos ───

    def _obtener_tasas_hora(self) -> dict:
        if self._tasas_hora_cache is None:
            if self.obtener_tasas_hora:
                try:
                    self._tasas_hora_cache = self.obtener_tasas_hora() or {}
                except Exception:
                    self._tasas_hora_cache = {}
            else:
                self._tasas_hora_cache = {}
        return self._tasas_hora_cache

    def _mano_obra_estimada(self, horas) -> float:
        try:
            horas = float(horas or 0)
        except (TypeError, ValueError):
            horas = 0.0
        costo_hora_trabajo = float(self._obtener_tasas_hora().get("costo_hora_trabajo", 0) or 0)
        return round(horas * costo_hora_trabajo, 2)

    def _costos_indirectos_estimados(self, horas) -> float:
        try:
            horas = float(horas or 0)
        except (TypeError, ValueError):
            horas = 0.0
        tasas = self._obtener_tasas_hora()
        tasa_por_hora = float(tasas.get("tasa_servicios_por_hora", 0) or 0) + float(
            tasas.get("tasa_depreciacion_por_hora", 0) or 0
        )
        return round(horas * tasa_por_hora, 2)

    def _actualizar_estimados_costos(self, e=None):
        try:
            horas = float(self.txt_tiempo_preparacion.value or 0)
        except ValueError:
            horas = 0.0
        self.txt_mano_obra_estimada.value = f"${self._mano_obra_estimada(horas):.2f}"
        self.txt_costos_indirectos_estimados.value = f"${self._costos_indirectos_estimados(horas):.2f}"
        if self.txt_mano_obra_estimada.page:
            self.txt_mano_obra_estimada.update()
        if self.txt_costos_indirectos_estimados.page:
            self.txt_costos_indirectos_estimados.update()
        self._actualizar_precio_sugerido()
        self._actualizar_precio_sugerido_elaborado()

    def _actualizar_precio_sugerido_elaborado(self, e=None):
        """Recalcula el precio sugerido en el paso de Costos de un producto elaborado."""
        if self.tipo != "elaborado" or not hasattr(self, "txt_precio_sugerido"):
            return
        sugerido = self._precio_sugerido_actual()
        self.txt_precio_sugerido.value = f"{sugerido:.2f}"
        if self.txt_precio_sugerido.page:
            self.txt_precio_sugerido.update()

    # =====================================================
    # PASO: PRODUCTOS DEL COMBO
    # =====================================================

    def _paso_productos_combo(self):
        self.autocompletado_producto_combo = AutoCompletado(
            etiqueta="Producto",
            buscar=self.buscar_productos,
            width=300,
        )
        self.txt_producto_combo_cantidad = CampoTexto(
            etiqueta="Cantidad",
            width=120,
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.tabla_productos_combo = TablaSeleccion(
            columnas=[("nombre", "Producto"), ("cantidad", "Cantidad")],
            on_eliminar=self._quitar_producto_combo,
        )
        self.tabla_productos_combo.reemplazar(self.productos_combo)
        boton_agregar = ft.IconButton(
            icon=AppIcons.ADD,
            tooltip="Agregar producto",
            on_click=self._agregar_producto_combo,
        )
        return TarjetaFormulario(
            titulo="Productos incluidos en el combo",
            contenido=[
                ft.Row(
                    [self.autocompletado_producto_combo, self.txt_producto_combo_cantidad, boton_agregar],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                self.tabla_productos_combo,
            ],
            expand=True,
        )

    def _agregar_producto_combo(self, e):
        nombre = self.autocompletado_producto_combo.obtener()
        if not nombre:
            return
        id_producto = self._obtener_id_seleccionado(self.autocompletado_producto_combo, "el producto")
        if not id_producto:
            return
        try:
            cantidad = float(self.txt_producto_combo_cantidad.value or 1)
        except ValueError:
            cantidad = 1
        self.productos_combo.append({"nombre": nombre, "id_producto": id_producto, "cantidad": cantidad})
        self.tabla_productos_combo.reemplazar(self.productos_combo)
        self.autocompletado_producto_combo.limpiar()
        self.txt_producto_combo_cantidad.value = "1"
        self.txt_producto_combo_cantidad.update()

    def _quitar_producto_combo(self, indice):
        """Callback de TablaSeleccion: quita un producto de la lista
        real self.productos_combo y re-renderiza la tabla."""
        if 0 <= indice < len(self.productos_combo):
            self.productos_combo.pop(indice)
            self.tabla_productos_combo.reemplazar(self.productos_combo)

    # =====================================================
    # PASO: PRECIO DEL COMBO
    # =====================================================

    def _paso_precio_combo(self):
        datos = self.datos_iniciales
        self.txt_precio_combo = CampoTexto(
            etiqueta="Precio del combo",
            width=200,
            value=str(datos.get("precio_combo", "")),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.txt_descuento_combo = CampoTexto(
            etiqueta="Descuento (%)",
            width=200,
            value=str(datos.get("descuento_combo", "0")),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        return TarjetaFormulario(
            titulo="Precio del combo",
            contenido=[
                ft.Row([self.txt_precio_combo, self.txt_descuento_combo], spacing=AppSpacing.CONTROL_SPACING),
            ],
            expand=True,
        )

    # =====================================================
    # PASO: RESUMEN
    # =====================================================

    def _paso_resumen(self):
        filas = [
            ("Nombre", self.txt_nombre.value),
            ("Categoría", self.dd_categoria.value),
        ]

        if self.tipo == "individual":
            if self._es_torta:
                # Datos de la torta
                diametro = self.txt_diametro.value or "-"
                tipo_venta = self.dd_tipo_venta.value
                cantidad_trozos = self.txt_cantidad_trozos.value if tipo_venta == "Por trozos" else "-"
                # Precio completo sugerido (sin dividir)
                precio_completo_sugerido = self._precio_sugerido_actual(100, self._empaques_presentacion_actual)
                # Precio por trozo sugerido
                if tipo_venta == "Por trozos":
                    try:
                        cant = float(self.txt_cantidad_trozos.value or 1)
                        precio_trozo_sugerido = precio_completo_sugerido / cant if cant else 0
                    except (ValueError, ZeroDivisionError):
                        precio_trozo_sugerido = 0
                else:
                    precio_trozo_sugerido = None

                # Precio final elegido (manual o sugerido)
                precio_manual = self.txt_presentacion_precio_manual.value.strip()
                if precio_manual:
                    try:
                        precio_final = float(precio_manual)
                    except ValueError:
                        precio_final = precio_completo_sugerido
                else:
                    precio_final = precio_completo_sugerido

                filas += [
                    ("Diámetro", f"{diametro} cm" if diametro else "-"),
                    ("Venta", tipo_venta),
                    ("Cantidad de trozos", cantidad_trozos),
                    ("Precio completo sugerido", f"${precio_completo_sugerido:.2f}"),
                ]
                if tipo_venta == "Por trozos":
                    filas.append(("Precio por trozo sugerido", f"${precio_trozo_sugerido:.2f}"))
                filas.append(("Precio final (elegido)", f"${precio_final:.2f}"))
                filas.append(("Empaques", str(len(self._empaques_presentacion_actual))))
            else:
                # Producto individual no torta
                filas += [
                    ("Presentaciones", str(len(self.presentaciones))),
                ]
            # Costos comunes
            filas += [
                ("Tiempo de preparación", f"{self.txt_tiempo_preparacion.value or 0} h"),
                ("Mano de obra (calculada)", self.txt_mano_obra_estimada.value),
                ("Costos indirectos (calculados)", self.txt_costos_indirectos_estimados.value),
                ("Margen de ganancia", f"{self.txt_margen.value or 40}%"),
            ]

        elif self.tipo == "elaborado":
            precio_venta_texto = (getattr(self, "txt_precio_venta", None) and self.txt_precio_venta.value or "").strip()
            precio_sugerido_texto = getattr(self, "txt_precio_sugerido", None) and self.txt_precio_sugerido.value or "0"
            filas += [
                ("Componentes", str(len(self.componentes))),
                ("Empaques", str(len(self.empaques))),
                ("Tiempo de preparación", f"{self.txt_tiempo_preparacion.value or 0} h"),
                ("Mano de obra (calculada)", self.txt_mano_obra_estimada.value),
                ("Costos indirectos (calculados)", self.txt_costos_indirectos_estimados.value),
                ("Margen de ganancia", f"{self.txt_margen.value or 40}%"),
                ("Precio sugerido", f"${precio_sugerido_texto}"),
                ("Precio de venta", f"${precio_venta_texto}" if precio_venta_texto else f"${precio_sugerido_texto} (sugerido)"),
            ]

        elif self.tipo == "combo":
            filas += [
                ("Productos", str(len(self.productos_combo))),
                ("Precio combo", self.txt_precio_combo.value),
                ("Descuento", f"{self.txt_descuento_combo.value or 0}%"),
            ]

        filas_widgets = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(titulo, weight=AppTypography.MEDIUM),
                    ft.Text(str(valor or "-")),
                ],
            )
            for titulo, valor in filas
        ]

        aviso = ft.Container(
            padding=AppSpacing.SM,
            border_radius=8,
            bgcolor=self.tema.warning + "15",
            content=ft.Text(
                "El costo se recalcula al guardar con los datos definitivos. "
                "El precio sugerido ya refleja el costo, la mano de obra y el "
                "margen cargados, pero el precio final es el que vos elegiste "
                "(o el sugerido, si dejaste el campo de precio vacío).",
                size=AppTypography.SMALL,
                color=self.tema.warning,
            ),
        )

        return TarjetaFormulario(
            titulo="Resumen",
            contenido=[*filas_widgets, ft.Divider(), aviso],
            expand=True,
        )

    # =====================================================
    # GUARDAR
    # =====================================================

    def _guardar(self):
        if not self._validar_paso_actual():
            return

        datos = {
            "tipo": self.tipo,
            "nombre": self.txt_nombre.value.strip(),
            "categoria": self.dd_categoria.value,
            "descripcion": self.txt_descripcion.value,
        }

        try:
            horas = float(getattr(self, "txt_tiempo_preparacion", None) and self.txt_tiempo_preparacion.value or 0)
        except ValueError:
            horas = 0.0

        if self.tipo == "individual":
            datos["nombre_receta"] = self.autocompletado_receta.obtener()
            datos["id_receta"] = getattr(self.autocompletado_receta, "obtener_id", lambda: None)()
            datos["margen_porcentaje"] = float(self.txt_margen.value or 40)
            datos["tiempo_preparacion_minutos"] = round(horas * 60, 2)
            datos["mano_obra"] = self._mano_obra_estimada(horas)
            datos["costos_indirectos_monto"] = self._costos_indirectos_estimados(horas)

            if self._es_torta:
                # Guardar atributos específicos de la torta
                datos["diametro_cm"] = float(self.txt_diametro.value) if self.txt_diametro.value else None
                datos["tipo_venta"] = self.dd_tipo_venta.value
                datos["cantidad_trozos"] = int(self.txt_cantidad_trozos.value) if self.txt_cantidad_trozos.value else None

                # Construir una única presentación
                empaques = self._empaques_presentacion_actual
                precio_manual = self.txt_presentacion_precio_manual.value.strip()
                precio_manual_valido = None
                if precio_manual:
                    try:
                        precio_manual_valido = float(precio_manual)
                    except ValueError:
                        precio_manual_valido = None

                # "precio" es lo que se guarda en la presentación (manual
                # si lo hay, si no la preview del wizard, solo para
                # mostrar). precio_manual_valido es lo que decide si se
                # manda precio_venta al backend.
                precio = precio_manual_valido if precio_manual_valido is not None else self._precio_sugerido_actual(100, empaques)

                presentacion = {
                    "nombre": "Torta completa" if self.dd_tipo_venta.value == "Completa" else "Trozo de torta",
                    "tipo": self.dd_tipo_venta.value.lower(),
                    "diametro_cm": datos["diametro_cm"],
                    "cantidad_trozos": datos["cantidad_trozos"],
                    "empaques": empaques,
                    "precio": precio,
                }
                datos["presentaciones"] = [presentacion]
                # Los empaques consolidados para inventario se toman de la presentación
                datos["empaques"] = self._consolidar_empaques_presentaciones()
                # ✅ Solo mandamos precio_venta si el usuario realmente
                # escribió un precio manual. Antes se mandaba SIEMPRE
                # (incluso vacío -> usaba _precio_sugerido_actual, el
                # preview del wizard), y ProductoService lo tomaba como
                # decisión final e inapelable del usuario, pisando el
                # precio_sugerido correcto que el backend calcula con
                # costo_receta + mano de obra + costos indirectos +
                # margen. Si no hay precio manual, dejamos que el
                # backend calcule y use su propio precio_sugerido fresco
                # -- igual que ya se hacía para "elaborado".
                if precio_manual_valido is not None:
                    datos["precio_venta"] = precio_manual_valido
            else:
                datos["presentaciones"] = self.presentaciones
                datos["empaques"] = self._consolidar_empaques_presentaciones()
                # ✅ Con varias presentaciones no hay "un" precio único;
                # si el usuario fijó un precio manual para la primera
                # presentación, lo usamos como precio de referencia del
                # producto (el que se ve en la tarjeta del catálogo y el
                # que se usa si este producto se incluye en un combo o
                # como subproducto de otro elaborado). La venta real de
                # cada presentación sigue usando su propio precio.
                # Si esa primera presentación NO tiene precio manual
                # (precio_manual=False, ver _agregar_presentacion), su
                # "precio" es solo la preview del wizard -- no lo
                # mandamos como precio_venta para no pisar el
                # precio_sugerido correcto que calcula el backend.
                if self.presentaciones and self.presentaciones[0].get("precio_manual"):
                    datos["precio_venta"] = self.presentaciones[0].get("precio")

        elif self.tipo == "elaborado":
            datos["componentes"] = self.componentes
            datos["empaques"] = self.empaques
            datos["unidad_base"] = getattr(self, "dd_unidad_base", None) and self.dd_unidad_base.value or "unidad"
            datos["margen_porcentaje"] = float(self.txt_margen.value or 40)
            datos["tiempo_preparacion_minutos"] = round(horas * 60, 2)
            datos["mano_obra"] = self._mano_obra_estimada(horas)
            datos["costos_indirectos_monto"] = self._costos_indirectos_estimados(horas)
            # ✅ Antes no existía ningún campo para que el usuario
            # eligiera el precio de venta de un producto elaborado:
            # salía siempre el calculado (costo x margen).
            precio_venta = (getattr(self, "txt_precio_venta", None) and self.txt_precio_venta.value or "").strip()
            if precio_venta:
                try:
                    datos["precio_venta"] = float(precio_venta)
                except ValueError:
                    pass

        elif self.tipo == "combo":
            datos["productos"] = self.productos_combo
            datos["precio_combo"] = float(self.txt_precio_combo.value) if self.txt_precio_combo.value else 0
            datos["descuento_combo"] = float(self.txt_descuento_combo.value) if self.txt_descuento_combo.value else 0

        if self.on_guardar:
            self.on_guardar(datos)