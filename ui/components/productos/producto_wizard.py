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

    # ✅ Orden nuevo: Información → Costos (tiempo + margen) →
    # Presentaciones (trozos/diámetro + empaque por presentación) →
    # Resumen. El empaque dejó de ser un paso propio en "individual":
    # como varía según la presentación (torta completa vs. trozo, caja
    # vs. domo), ahora se elige dentro de cada presentación.
    PASOS_INDIVIDUAL = ["Información", "Costos", "Presentaciones", "Resumen"]

    # "elaborado" todavía no tiene presentaciones por trozos (no aplica
    # a productos armados por componentes), así que conserva su paso de
    # Empaques propio, solo reordenado detrás de Costos.
    PASOS_ELABORADO = ["Información", "Componentes", "Costos", "Empaques", "Resumen"]

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

        # Callback opcional: sin argumentos, devuelve el desglose de
        # tasas por hora ya cargado en "Mi Negocio" (equivalente a
        # ParametrosNegocioService.obtener_desglose().datos), con las
        # claves "costo_hora_trabajo", "tasa_servicios_por_hora",
        # "tasa_depreciacion_por_hora" y "costo_hora_total". Con esto el
        # wizard calcula mano de obra y costos indirectos a partir del
        # tiempo de preparación, en vez de pedírselos al usuario. Si no
        # se provee, se asumen todas las tasas en $0 (con aviso en pantalla).
        obtener_tasas_hora: Callable[[], dict] | None = None,

        categorias: list[str] | None = None,

        datos_iniciales: dict | None = None,

    ):

        super().__init__(expand=True)

        # ✅ OJO: NO asignar esto a self.page. ft.Container ya usa
        # `self.page` internamente para saber si el control está
        # montado en el árbol de la página (None hasta que se
        # agrega de verdad, p.ej. en _mostrar_wizard). Si lo
        # pisamos acá, "if self.page:" da True incluso durante el
        # propio __init__, y cualquier self.update() llamado antes
        # de montar el control revienta con AssertionError (Flet
        # intenta actualizar un control sin uid todavía).
        self._pagina = page

        self.tema = ThemeManager.theme

        self.on_guardar = on_guardar

        self.on_cancelar = on_cancelar

        self.buscar_recetas = buscar_recetas

        self.buscar_ingredientes = buscar_ingredientes

        self.buscar_productos = buscar_productos

        self.buscar_empaques = buscar_empaques

        self.buscar_costos_indirectos = buscar_costos_indirectos

        # Callback opcional: dado un dict parcial de datos del producto,
        # devuelve {"costo_total":.., "precio_final":..} calculado en vivo
        # (sin guardar nada). Se usa para sugerir el precio de cada
        # presentación. Si no se provee, las presentaciones piden el
        # precio a mano, igual que antes.
        self.calcular_preview = calcular_preview

        self.obtener_tasas_hora = obtener_tasas_hora
        # Cache simple: se pide una sola vez por instancia del wizard
        # (las tasas no cambian mientras se está cargando un producto).
        self._tasas_hora_cache: dict | None = None

        self.categorias = categorias or [

            "Tortas", "Postres", "Cupcakes", "Donas",

            "Galletas", "Refrigerados", "Pasapalos",

            "Bebidas", "Combos", "Otros",

        ]

        # ---------------------------------------------------
        # Estado del asistente
        # ---------------------------------------------------

        self.tipo = None

        self.paso_actual = 0

        self.datos_iniciales = datos_iniciales or {}

        # ✅ Al editar, estas listas deben restaurarse desde
        # datos_iniciales (si no, el wizard "borra" visualmente
        # la composición del producto aunque el dict original la
        # tuviera). Nótese que el combo guarda su lista bajo la
        # clave "productos" (ver _guardar()).

        self.presentaciones: list[dict] = list(self.datos_iniciales.get("presentaciones", []))

        self.componentes: list[dict] = list(self.datos_iniciales.get("componentes", []))

        self.empaques: list[dict] = list(self.datos_iniciales.get("empaques", []))

        # ⚠️ Legacy: antes era una lista de activos elegidos a mano en
        # el paso Costos. Ahora los costos indirectos se calculan solos
        # (tiempo de preparación x tasas de Mi Negocio, ver
        # _costos_indirectos_estimados). Se mantiene el atributo solo
        # para no romper si datos_iniciales todavía trae la clave vieja.
        self.costos_indirectos: list[dict] = list(self.datos_iniciales.get("costos_indirectos", []))

        self.productos_combo: list[dict] = list(self.datos_iniciales.get("productos", []))

        # ---------------------------------------------------
        # Contenedores dinámicos
        # ---------------------------------------------------

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

                ft.Container(

                    expand=True,

                    content=self.contenedor_paso,

                ),

                self.contenedor_botones,

            ],

        )

        # ✅ Si estamos editando y el producto ya tiene un tipo
        # definido, saltamos directo a sus pasos en lugar de
        # forzar a re-elegir el tipo cada vez que se edita.

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

            self.contenedor_stepper.content = ft.Container()

        else:

            self.contenedor_stepper.content = Stepper(

                pasos=self._pasos_para_tipo(),

                paso_actual=self.paso_actual,

            )

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

            botones = [

                BotonSecundario(

                    texto="Atrás" if self.paso_actual > 0 else "Cambiar tipo",

                    icono=AppIcons.BACK,

                    on_click=lambda e: self._atras(),

                ),

            ]

            es_ultimo_paso = self.paso_actual == len(self._pasos_para_tipo()) - 1

            botones.append(

                BotonPrimario(

                    texto="Guardar" if es_ultimo_paso else "Siguiente",

                    icono=AppIcons.SAVE if es_ultimo_paso else AppIcons.NEXT,

                    on_click=(

                        lambda e: self._guardar()
                    ) if es_ultimo_paso else (
                        lambda e: self._siguiente()
                    ),

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

                            ft.Text(

                                titulo,

                                weight=AppTypography.BOLD,

                                size=AppTypography.CARD_TITLE,

                            ),

                            ft.Text(

                                descripcion,

                                size=AppTypography.SMALL,

                                color=self.tema.text_secondary,

                            ),

                        ],

                    ),

                )

            )

        self.contenedor_paso.content = ft.Column(

            spacing=AppSpacing.LG,

            controls=[

                ft.Text(

                    "¿Qué querés crear?",

                    size=AppTypography.SECTION_TITLE,

                    weight=AppTypography.BOLD,

                ),

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

        return True

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

        )

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
        self._es_torta = (self.dd_categoria.value or "") == "Tortas"

        controles: list = []

        if self._es_torta:
            controles += self._controles_torta(datos)
            controles.append(ft.Divider())

        self.txt_presentacion_nombre = CampoTexto(
            etiqueta="Presentación (ej. Torta completa, Trozo individual)",
            width=260,
        )

        # ✅ En vez de un % a ciegas, se elige cómo se vende: completa,
        # o por trozos (y en ese caso se pide diámetro + cantidad de
        # trozos, para dividir el costo de la receta base entre esa
        # cantidad).
        self.dd_presentacion_tipo = Selector(

            etiqueta="Se vende",

            opciones=["Completa", "Por trozos"],

            valor="Completa",

            width=160,

            on_change=lambda e: self._alternar_campos_trozos(),

        )

        self.txt_presentacion_diametro = CampoTexto(

            etiqueta="Diámetro (cm)",

            width=140,

            hint="Ej: 20",

            keyboard_type=ft.KeyboardType.NUMBER,

            visible=False,

        )

        self.txt_presentacion_cantidad_trozos = CampoTexto(

            etiqueta="Cantidad de trozos",

            width=160,

            hint="Ej: 10",

            keyboard_type=ft.KeyboardType.NUMBER,

            visible=False,

            on_change=self._actualizar_precio_sugerido,

        )

        # ✅ El empaque varía según la presentación (caja para la torta
        # completa, domo para el trozo, etc.), así que se elige acá, a
        # nivel de presentación, y se suma al costo de esa presentación
        # puntual en vez de a un total genérico del producto.
        self.autocompletado_presentacion_empaque = AutoCompletado(

            etiqueta="Empaque para esta presentación (opcional)",

            buscar=self.buscar_empaques,

            width=300,

        )

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

        )

        self.tabla_presentaciones.reemplazar(self._filas_presentaciones())

        boton_agregar = ft.IconButton(

            icon=AppIcons.ADD,

            tooltip="Agregar presentación",

            on_click=self._agregar_presentacion,

        )

        controles += [

            ft.Row(
                [self.txt_presentacion_nombre, self.dd_presentacion_tipo],
                spacing=AppSpacing.CONTROL_SPACING,
            ),

            ft.Row(
                [self.txt_presentacion_diametro, self.txt_presentacion_cantidad_trozos],
                spacing=AppSpacing.CONTROL_SPACING,
            ),

            self.autocompletado_presentacion_empaque,

            ft.Row(
                [self.txt_presentacion_precio_sugerido, self.txt_presentacion_precio_manual, boton_agregar],
                spacing=AppSpacing.CONTROL_SPACING,
            ),

            self.tabla_presentaciones,

        ]

        return TarjetaFormulario(

            titulo="Presentaciones disponibles",

            subtitulo=(
                "Define cómo se vende este producto: completo o por trozos, "
                "y qué empaque lleva cada presentación. El precio sugerido "
                "usa el costo, el empaque y el margen que ya cargaste; "
                "podés ajustarlo a mano si querés."
            ),

            contenido=controles,

            expand=True,

        )

    def _controles_torta(self, datos: dict) -> list:
        """
        Preguntas propias de la categoría "Tortas": tamaño y si se
        vende (además) por porciones. Son metadatos informativos para
        precargar la presentación por trozos más abajo (diámetro y
        cantidad de trozos sugeridos); no reemplazan la carga de cada
        presentación, que sigue siendo explícita.
        """
        self.dd_torta_tamano = Selector(

            etiqueta="Tamaño de la torta",

            opciones=["20 cm", "15 cm", "10 cm"],

            valor=datos.get("torta_tamano_cm"),

            width=180,

        )

        self.sw_torta_por_porciones = ft.Switch(

            label="¿Se vende por porciones?",

            value=bool(datos.get("torta_vende_por_porciones", False)),

        )

        self.txt_torta_porciones = CampoTexto(

            etiqueta="Cantidad de porciones",

            width=180,

            hint="Ej: 10",

            value=str(datos.get("torta_cantidad_porciones", "") or ""),

            keyboard_type=ft.KeyboardType.NUMBER,

        )

        return [
            ft.Text("Detalle de la torta", weight=AppTypography.MEDIUM),
            ft.Row(
                [self.dd_torta_tamano, self.sw_torta_por_porciones, self.txt_torta_porciones],
                spacing=AppSpacing.CONTROL_SPACING,
            ),
        ]

    def _alternar_campos_trozos(self, e=None):
        """Muestra/oculta diámetro y cantidad de trozos según "Se vende"."""
        mostrar = self.dd_presentacion_tipo.value == "Por trozos"
        self.txt_presentacion_diametro.visible = mostrar
        self.txt_presentacion_cantidad_trozos.visible = mostrar
        if self.txt_presentacion_diametro.page:
            self.txt_presentacion_diametro.update()
        if self.txt_presentacion_cantidad_trozos.page:
            self.txt_presentacion_cantidad_trozos.update()
        self._actualizar_precio_sugerido()

    def _filas_presentaciones(self) -> list[dict]:
        """Traduce self.presentaciones al formato de columnas de la tabla."""
        filas = []
        for p in self.presentaciones:
            if p.get("es_por_trozos"):
                diametro = p.get("diametro_cm")
                detalle = f"Trozo ({diametro} cm, 1/{p.get('cantidad_trozos')})" if diametro else f"Trozo (1/{p.get('cantidad_trozos')})"
            else:
                detalle = "Completa"
            empaque = p.get("empaque")
            filas.append({
                "nombre": p.get("nombre"),
                "detalle": detalle,
                "empaque": empaque["nombre"] if empaque else "-",
                "precio": p.get("precio"),
            })
        return filas

    def _empaque_seleccionado_actual(self) -> dict | None:
        """Lee el empaque elegido (todavía sin agregar) en el formulario."""
        if not hasattr(self, "autocompletado_presentacion_empaque"):
            return None
        nombre = self.autocompletado_presentacion_empaque.obtener()
        if not nombre:
            return None
        id_activo = getattr(self.autocompletado_presentacion_empaque, "obtener_id", lambda: None)()
        return {"nombre": nombre, "id_activo": id_activo, "cantidad": 1}

    def _armar_datos_parciales_para_preview(self, empaque: dict | None = None) -> dict:
        """
        Arma un dict "en progreso" con todo lo que el usuario ya cargó
        en Información/Costos, para pedirle a ProductoService un cálculo
        de costo/precio sin guardar nada. `empaque`, si se pasa, es el
        de ESTA presentación puntual (no un total del producto: cada
        presentación puede llevar un empaque distinto).

        Se asume que estos widgets ya existen porque Presentaciones es
        el paso siguiente a Costos.
        """
        try:
            horas = float(self.txt_tiempo_preparacion.value or 0)
        except (ValueError, AttributeError):
            horas = 0.0
        return {
            "tipo": "individual",
            "id_receta": getattr(self.autocompletado_receta, "obtener_id", lambda: None)(),
            "empaques": [empaque] if empaque else [],
            # ⚠️ Requiere que ProductoService acepte "costos_indirectos_monto"
            # como override directo del total de costos indirectos (en vez
            # de recalcularlo desde una lista de activos elegidos a mano).
            "costos_indirectos_monto": self._costos_indirectos_estimados(horas),
            "mano_obra": self._mano_obra_estimada(horas),
            "margen_porcentaje": self.txt_margen.value or 40,
        }

    def _precio_sugerido_actual(self, fraccion: float, empaque: dict | None = None) -> float:
        """Precio sugerido para una presentación que representa `fraccion`% del producto completo."""
        if not self.calcular_preview:
            return 0.0
        try:
            datos_parciales = self._armar_datos_parciales_para_preview(empaque)
            resultado = self.calcular_preview(datos_parciales) or {}
        except Exception:
            return 0.0
        precio_total = float(resultado.get("precio_final", 0) or 0)
        return round(precio_total * (fraccion / 100), 2)

    def _actualizar_precio_sugerido(self, e=None):
        """
        Recalcula el precio sugerido mostrado en el campo de solo lectura.
        Se llama al cambiar el tiempo de preparación, el margen, el tipo
        de presentación, la cantidad de trozos o el empaque elegido.
        Con hasattr porque txt_margen (paso Costos) puede disparar este
        callback antes de que el paso Presentaciones exista todavía.
        """
        if not hasattr(self, "dd_presentacion_tipo") or not hasattr(self, "txt_presentacion_precio_sugerido"):
            return

        if self.dd_presentacion_tipo.value == "Por trozos":
            try:
                cantidad_trozos = float(self.txt_presentacion_cantidad_trozos.value or 0)
            except ValueError:
                cantidad_trozos = 0
            fraccion = round(100 / cantidad_trozos, 4) if cantidad_trozos else 0.0
        else:
            fraccion = 100.0

        empaque = self._empaque_seleccionado_actual()
        sugerido = self._precio_sugerido_actual(fraccion, empaque)
        self.txt_presentacion_precio_sugerido.value = f"{sugerido:.2f}"
        # ✅ Se revisa la página del control en sí, no la del wizard: un
        # control recién creado (p.ej. al construir este paso) puede no
        # estar montado todavía aunque el wizard container sí lo esté,
        # y llamar update() sobre él revienta con AssertionError.
        if self.txt_presentacion_precio_sugerido.page:
            self.txt_presentacion_precio_sugerido.update()

    def _agregar_presentacion(self, e):

        nombre = (self.txt_presentacion_nombre.value or "").strip()

        if not nombre:

            return

        es_por_trozos = self.dd_presentacion_tipo.value == "Por trozos"

        diametro = None
        cantidad_trozos = None
        fraccion = 100.0

        if es_por_trozos:

            try:
                cantidad_trozos = int(float(self.txt_presentacion_cantidad_trozos.value or 0))
            except ValueError:
                cantidad_trozos = 0

            if not cantidad_trozos:
                self.txt_presentacion_cantidad_trozos.error_text = "Indicá en cuántos trozos se divide."
                self.txt_presentacion_cantidad_trozos.update()
                return
            self.txt_presentacion_cantidad_trozos.error_text = None

            try:
                diametro = float(self.txt_presentacion_diametro.value or 0) or None
            except ValueError:
                diametro = None

            # ✅ El costo de la receta base se divide entre la cantidad
            # de trozos: cada trozo "es" esa fracción del producto entero.
            fraccion = round(100 / cantidad_trozos, 4)

        empaque = self._empaque_seleccionado_actual()

        precio_manual = (self.txt_presentacion_precio_manual.value or "").strip()

        if precio_manual:

            try:

                precio = float(precio_manual)

            except ValueError:

                precio = 0.0

        else:

            precio = self._precio_sugerido_actual(fraccion, empaque)

        self.presentaciones.append({
            "nombre": nombre,
            "es_por_trozos": es_por_trozos,
            "diametro_cm": diametro,
            "cantidad_trozos": cantidad_trozos,
            "fraccion": fraccion,
            "empaque": empaque,
            "precio": precio,
        })

        self.tabla_presentaciones.reemplazar(self._filas_presentaciones())

        self.txt_presentacion_nombre.value = ""

        self.dd_presentacion_tipo.value = "Completa"

        self.txt_presentacion_diametro.value = ""

        self.txt_presentacion_cantidad_trozos.value = ""

        self.autocompletado_presentacion_empaque.limpiar()

        self.txt_presentacion_precio_manual.value = ""

        self._alternar_campos_trozos()

        self._actualizar_precio_sugerido()

        self.txt_presentacion_nombre.update()

        self.dd_presentacion_tipo.update()

        self.txt_presentacion_precio_manual.update()

    def _consolidar_empaques_presentaciones(self) -> list[dict]:
        """
        Junta los empaques usados en todas las presentaciones en una
        sola lista, sumando cantidades cuando se repite el mismo
        empaque, para la relación PRODUCTO_ACTIVO (control de stock de
        cajas/domos consumidos por este producto). El costo mostrado en
        cada presentación ya incluye su propio empaque; esta lista es
        solo para inventario, no se vuelve a sumar al costo del producto.
        """
        acumulado: dict[int, dict] = {}
        for p in self.presentaciones:
            empaque = p.get("empaque")
            if not empaque or not empaque.get("id_activo"):
                continue
            id_activo = empaque["id_activo"]
            if id_activo not in acumulado:
                acumulado[id_activo] = dict(empaque)
            else:
                acumulado[id_activo]["cantidad"] = acumulado[id_activo].get("cantidad", 1) + empaque.get("cantidad", 1)
        return list(acumulado.values())

    # =====================================================
    # PASO: COMPONENTES (solo Producto Elaborado)
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

        self.tabla_componentes = TablaSeleccion(

            columnas=[("tipo", "Tipo"), ("nombre", "Nombre"), ("cantidad", "Cantidad")],

        )

        self.tabla_componentes.reemplazar(self.componentes)

        boton_agregar = ft.IconButton(

            icon=AppIcons.ADD,

            tooltip="Agregar componente",

            on_click=self._agregar_componente,

        )

        return TarjetaFormulario(

            titulo="Componentes del producto",

            subtitulo="Ingredientes, productos o subproductos que forman este artículo.",

            contenido=[

                ft.Row(

                    [

                        self.dd_tipo_componente,

                        self.autocompletado_componente,

                        self.txt_componente_cantidad,

                        boton_agregar,

                    ],

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

        # "Subproducto" reutiliza la búsqueda de productos: un
        # subproducto se guarda como un producto más (ver
        # doc funcional, sección "Subproductos").
        if tipo == "Subproducto" and self.buscar_productos:

            return self.buscar_productos(texto)

        return []

    def _agregar_componente(self, e):

        nombre = self.autocompletado_componente.obtener()

        if not nombre:

            return

        try:

            cantidad = float(self.txt_componente_cantidad.value or 0)

        except ValueError:

            cantidad = 0

        id_componente = getattr(self.autocompletado_componente, "obtener_id", lambda: None)()

        # ✅ El service espera "tipo" en minúsculas ("ingrediente",
        # "producto", "subproducto"), el selector muestra "Ingrediente"...
        self.componentes.append({

            "tipo": (self.dd_tipo_componente.value or "Ingrediente").lower(),

            "nombre": nombre,

            "id": id_componente,

            "cantidad": cantidad,

        })

        self.tabla_componentes.reemplazar(self.componentes)

        self.autocompletado_componente.limpiar()

        self.txt_componente_cantidad.value = ""

        self.txt_componente_cantidad.update()

    # =====================================================
    # PASO: EMPAQUES
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

        try:

            cantidad = float(self.txt_empaque_cantidad.value or 1)

        except ValueError:

            cantidad = 1

        # ⚠️ Igual que con la receta: requiere obtener_id() en AutoCompletado.
        id_activo = getattr(self.autocompletado_empaque, "obtener_id", lambda: None)()

        self.empaques.append({"nombre": nombre, "id_activo": id_activo, "cantidad": cantidad})

        self.tabla_empaques.reemplazar(self.empaques)

        self.autocompletado_empaque.limpiar()

        self.txt_empaque_cantidad.value = "1"

        self.txt_empaque_cantidad.update()

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

        # ✅ El cambio clave: ya no se inventan montos de mano de obra ni
        # se eligen "a mano" los costos indirectos. Se pide un único dato
        # -el tiempo que lleva preparar el producto- y con eso, más las
        # tasas por hora ya cargadas en "Mi Negocio", el sistema calcula
        # solo cuánto vale la mano de obra y los costos indirectos.
        self.txt_tiempo_preparacion = CampoTexto(

            etiqueta="¿Cuánto tiempo toma preparar y hornear este producto? (horas)",

            width=320,

            hint="Ej: 2",

            value=str(horas_iniciales) if horas_iniciales else "",

            keyboard_type=ft.KeyboardType.NUMBER,

            on_change=self._actualizar_estimados_costos,

        )

        # ✅ El margen de ganancia sigue siendo el único valor que el
        # usuario decide directamente: es lo que convierte "costo" en
        # "precio sugerido".
        self.txt_margen = CampoTexto(

            etiqueta="Margen de ganancia (%)",

            width=170,

            hint="Ej: 40",

            value=str(datos.get("margen_porcentaje", 40)),

            keyboard_type=ft.KeyboardType.NUMBER,

            on_change=lambda e: self._actualizar_precio_sugerido(),

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
            ft.Row(
                [self.txt_tiempo_preparacion, self.txt_margen],
                spacing=AppSpacing.CONTROL_SPACING,
            ),
            ft.Row(
                [self.txt_mano_obra_estimada, self.txt_costos_indirectos_estimados],
                spacing=AppSpacing.CONTROL_SPACING,
            ),
        ]

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

    # ---------------------------------------------------
    # Cálculo de mano de obra / costos indirectos por tiempo
    # ---------------------------------------------------

    def _obtener_tasas_hora(self) -> dict:
        """Pide (una sola vez por instancia) el desglose de tasas por hora."""
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
        """
        Recalcula los campos de solo lectura de mano de obra y costos
        indirectos cuando cambia el tiempo de preparación, y en cadena
        actualiza también el precio sugerido de la presentación (si ese
        paso ya está armado).
        """
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

        try:

            cantidad = float(self.txt_producto_combo_cantidad.value or 1)

        except ValueError:

            cantidad = 1

        id_producto = getattr(self.autocompletado_producto_combo, "obtener_id", lambda: None)()

        self.productos_combo.append({"nombre": nombre, "id_producto": id_producto, "cantidad": cantidad})

        self.tabla_productos_combo.reemplazar(self.productos_combo)

        self.autocompletado_producto_combo.limpiar()

        self.txt_producto_combo_cantidad.value = "1"

        self.txt_producto_combo_cantidad.update()

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

                ft.Row(

                    [self.txt_precio_combo, self.txt_descuento_combo],

                    spacing=AppSpacing.CONTROL_SPACING,

                ),

            ],

            expand=True,

        )

    # =====================================================
    # PASO: RESUMEN
    #
    # ⚠️ El costo total y el precio sugerido reales dependen de
    # ProductoService (todavía no conectado). Este paso solo
    # muestra lo que el usuario cargó.
    # =====================================================

    def _paso_resumen(self):

        filas = [

            ("Nombre", self.txt_nombre.value),

            ("Categoría", self.dd_categoria.value),

        ]

        if self.tipo == "individual":

            filas += [

                ("Presentaciones", str(len(self.presentaciones))),

                ("Tiempo de preparación", f"{self.txt_tiempo_preparacion.value or 0} h"),

                ("Mano de obra (calculada)", self.txt_mano_obra_estimada.value),

                ("Costos indirectos (calculados)", self.txt_costos_indirectos_estimados.value),

                ("Margen de ganancia", f"{self.txt_margen.value or 40}%"),

            ]

        elif self.tipo == "elaborado":

            filas += [

                ("Componentes", str(len(self.componentes))),

                ("Empaques", str(len(self.empaques))),

                ("Tiempo de preparación", f"{self.txt_tiempo_preparacion.value or 0} h"),

                ("Mano de obra (calculada)", self.txt_mano_obra_estimada.value),

                ("Costos indirectos (calculados)", self.txt_costos_indirectos_estimados.value),

                ("Margen de ganancia", f"{self.txt_margen.value or 40}%"),

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

                "El costo y el precio final se recalculan al guardar con "
                "los datos definitivos. Los precios sugeridos en "
                "Presentaciones ya reflejan el costo, la mano de obra y el "
                "margen que cargaste.",

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

            # ⚠️ Requiere que AutoCompletado exponga obtener_id() cuando
            # buscar_recetas devuelve {"id":..,"nombre":..}. Si todavía no
            # lo expone, esto guarda id_receta=None y el service rechazará
            # el guardado ("Debe seleccionar una receta").
            datos["nombre_receta"] = self.autocompletado_receta.obtener()

            datos["id_receta"] = getattr(self.autocompletado_receta, "obtener_id", lambda: None)()

            datos["presentaciones"] = self.presentaciones

            # Los empaques ya no se cargan en un paso propio: se eligen
            # por presentación (ver Presentaciones) y acá se consolidan
            # para la relación PRODUCTO_ACTIVO (control de stock).
            datos["empaques"] = self._consolidar_empaques_presentaciones()

            datos["margen_porcentaje"] = self.txt_margen.value or 40

            datos["tiempo_preparacion_minutos"] = round(horas * 60, 2)

            datos["mano_obra"] = self._mano_obra_estimada(horas)

            # ⚠️ Requiere que ProductoService acepte "costos_indirectos_monto"
            # como override directo (ver _armar_datos_parciales_para_preview).
            datos["costos_indirectos_monto"] = self._costos_indirectos_estimados(horas)

            if getattr(self, "_es_torta", False) and hasattr(self, "dd_torta_tamano"):

                datos["torta_tamano_cm"] = self.dd_torta_tamano.value

                datos["torta_vende_por_porciones"] = self.sw_torta_por_porciones.value

                datos["torta_cantidad_porciones"] = self.txt_torta_porciones.value

        elif self.tipo == "elaborado":

            datos["componentes"] = self.componentes

            datos["empaques"] = self.empaques

            datos["margen_porcentaje"] = self.txt_margen.value or 40

            datos["tiempo_preparacion_minutos"] = round(horas * 60, 2)

            datos["mano_obra"] = self._mano_obra_estimada(horas)

            datos["costos_indirectos_monto"] = self._costos_indirectos_estimados(horas)

        elif self.tipo == "combo":

            datos["productos"] = self.productos_combo

            datos["precio_combo"] = self.txt_precio_combo.value

            datos["descuento_combo"] = self.txt_descuento_combo.value

        if self.on_guardar:

            self.on_guardar(datos)