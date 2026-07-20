"""
============================================================
Sistema La Dulce Tía

Archivo:
    producto_module.py

Responsabilidad:
    Módulo del catálogo de Productos.

    Conectado a ProductoService (y, para el asistente,
    RecetasService / ActivoService / IngredienteService) — ya no
    trabaja con una lista en memoria. Los servicios se reciben
    inyectados en el constructor; quien instancie ProductoModule
    es responsable de armar ProductoRepository/RecetasService/
    ActivoService/IngredienteService/ProductoService con la
    conexión real y pasarlos acá.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.productos.catalogo_productos import CatalogoProductos
from ui.components.productos.producto_wizard import ProductoWizard
from ui.components.buscador import Buscador
from ui.components.selector import Selector
from ui.components.boton import BotonPrimario
from ui.components.toolbar import Toolbar
from ui.components.overlay import Overlay
from ui.components.mensajes import MensajeSistema
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager
from ui.core.services.factory import ServiceFactory


class ProductoModule:
    """
    Módulo de catálogo de productos.
    Sigue el mismo patrón que IngredienteModule / RecetasModule:
    clase plana, sin herencia de Module, con construir() idempotente.
    """

    CATEGORIAS_BASE = [
        "Tortas", "Postres", "Cupcakes", "Donas",
        "Galletas", "Refrigerados", "Pasapalos",
        "Bebidas", "Combos", "Otros",
    ]

    def __init__(
        self,
        page: ft.Page,
        content_area,
        producto_service=None,
        recetas_service=None,
        activo_service=None,
        ingrediente_service=None,
        parametros_negocio_service=None,
    ):
        self.page = page
        self.content_area = content_area

        # producto_service es obligatorio para el funcionamiento del módulo;
        # los demás son opcionales y solo degradan la búsqueda del asistente.
        self._producto_service = producto_service or ServiceFactory.get_producto_service()
        self._recetas_service = recetas_service
        self._activo_service = activo_service
        self._ingrediente_service = ingrediente_service
        self._parametros_negocio_service = (
            parametros_negocio_service or ServiceFactory.get_parametros_negocio_service()
        )

        self._productos_cache: list[dict] = []
        self._layout_principal = None
        self.wizard_activo = None

        self.catalogo = None
        self.overlay = None
        self.buscador = None
        self.filtro_categoria = None
        self.orden = None
        self.toolbar = None

        # Componentes que no dependen de datos se crean una sola vez acá,
        # igual que _crear_toolbar()/_crear_tabla() en IngredienteModule.
        self._crear_componentes()

    # =====================================================
    # CONSTRUCCIÓN DEL LAYOUT PRINCIPAL
    # =====================================================

    def _esta_montado(self) -> bool:
        return bool(self.page)

    def _crear_componentes(self):

        self.catalogo = CatalogoProductos(
            on_editar=self._editar_producto,
            on_duplicar=self._duplicar_producto,
            on_ver_composicion=self._ver_composicion,
            on_desactivar=self._alternar_activo,
            on_eliminar=self._eliminar_producto,
        )

        self.buscador = Buscador(
            buscar=self._buscar,
            placeholder="Buscar producto...",
        )

        self.filtro_categoria = Selector(
            etiqueta="Categoría",
            opciones=["Todas"] + self._categorias_disponibles(),
            valor="Todas",
            width=200,
            on_change=lambda e: self._filtrar(),
        )

        self.orden = Selector(
            etiqueta="Ordenar por",
            opciones=["Nombre", "Precio", "Costo"],
            valor="Nombre",
            width=180,
            on_change=lambda e: self._filtrar(),
        )

        self.toolbar = Toolbar(
            izquierda=[self.buscador, self.filtro_categoria, self.orden],
            derecha=[
                BotonPrimario(
                    texto="Nuevo Producto",
                    icono=AppIcons.ADD,
                    on_click=self._nuevo_producto,
                ),
            ],
        )

        self.overlay = Overlay()

    def construir(self) -> ft.Control:

        if self._layout_principal is None:

            contenido = ft.Column(
                expand=True,
                spacing=AppSpacing.SECTION_SPACING,
                controls=[self.toolbar, self.catalogo],
            )

            self._layout_principal = ft.Stack(
                expand=True,
                controls=[
                    ft.Container(content=contenido, expand=True, padding=AppSpacing.LG),
                    self.overlay,
                ],
            )

            self.cargar()  # ✅ carga inicial, una sola vez

        return self._layout_principal

    # =====================================================
    # CARGA / FILTRADO
    # =====================================================

    def cargar(self):
        self._refrescar_catalogo()

    def _categorias_disponibles(self):
        usadas = {p.get("categoria") for p in self._productos_cache if p.get("categoria")}
        return sorted(usadas | set(self.CATEGORIAS_BASE))

    def _buscar(self, texto):
        self._filtrar(texto)

    def _filtrar(self, texto: str = ""):

        if not self._esta_montado():
            return

        texto = (texto or self.buscador.obtener() or "").strip()
        categoria = self.filtro_categoria.value

        resultado = (
            self._producto_service.buscar(texto) if texto
            else self._producto_service.listar()
        )

        if resultado.fallo:
            MensajeSistema.error(self.page, resultado.mensaje)
            productos = []
        else:
            productos = resultado.datos or []

        self._productos_cache = productos
        self.filtro_categoria.opciones = ["Todas"] + self._categorias_disponibles()

        if categoria and categoria != "Todas":
            productos = [p for p in productos if p.get("categoria") == categoria]

        clave_orden = {
            "Nombre": lambda p: (p.get("nombre") or "").lower(),
            "Precio": lambda p: float(p.get("precio_final", 0) or 0),
            "Costo": lambda p: float(p.get("costo_total", 0) or 0),
        }[self.orden.value]

        productos = sorted(productos, key=clave_orden)

        self.catalogo.reemplazar(productos)

        # ✅ Guard igual al de RecetasModule/IngredienteModule: solo
        # actualizamos si el layout ya está montado en la página.
        if self._layout_principal is not None and self._layout_principal.page:
            self._layout_principal.update()

    def _refrescar_catalogo(self):
        self._filtrar()

    # =====================================================
    # ACCIONES DEL ASISTENTE (wizard)
    # =====================================================

    def _nuevo_producto(self, e):

        wizard = ProductoWizard(
            page=self.page,
            on_guardar=self._guardar_producto,
            on_cancelar=self._cerrar_wizard,
            buscar_recetas=self._buscar_recetas,
            buscar_ingredientes=self._buscar_ingredientes,
            buscar_productos=self._buscar_productos,
            buscar_empaques=self._buscar_empaques,
            buscar_costos_indirectos=self._buscar_costos_indirectos,
            calcular_preview=self._calcular_preview,
            obtener_tasas_hora=self._obtener_tasas_hora,
            categorias=self._categorias_disponibles(),
        )
        self._mostrar_wizard(wizard)

    def _editar_producto(self, producto):

        resultado = self._producto_service.obtener(producto.get("id_producto"))

        if resultado.fallo:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        datos_iniciales = self._datos_iniciales_para_wizard(resultado.datos)

        wizard = ProductoWizard(
            page=self.page,
            on_guardar=lambda datos: self._guardar_producto(datos, producto.get("id_producto")),
            on_cancelar=self._cerrar_wizard,
            buscar_recetas=self._buscar_recetas,
            buscar_ingredientes=self._buscar_ingredientes,
            buscar_productos=self._buscar_productos,
            buscar_empaques=self._buscar_empaques,
            buscar_costos_indirectos=self._buscar_costos_indirectos,
            calcular_preview=self._calcular_preview,
            obtener_tasas_hora=self._obtener_tasas_hora,
            categorias=self._categorias_disponibles(),
            datos_iniciales=datos_iniciales,
        )
        self._mostrar_wizard(wizard)

    def _datos_iniciales_para_wizard(self, producto: dict) -> dict:
        datos = dict(producto)

        def _con_id_activo(items):
            return [
                {**item, "id_activo": item.get("id_activo", item.get("id"))}
                for item in (items or [])
            ]

        datos["empaques"] = _con_id_activo(producto.get("empaques", []))
        datos["costos_indirectos"] = _con_id_activo(producto.get("costos_indirectos", []))
        datos["productos"] = producto.get("productos_combo", [])

        if producto.get("mano_obra_es_porcentaje", True):
            datos["mano_obra_porcentaje"] = producto.get("mano_obra")
        else:
            datos["mano_obra_monto"] = producto.get("mano_obra")

        return datos

    def _mostrar_wizard(self, wizard: ProductoWizard):

        self.wizard_activo = wizard

        self.overlay.abrir(
            ft.Container(
                width=900,
                height=650,
                bgcolor=ThemeManager.theme.card,
                border_radius=12,
                padding=AppSpacing.LG,
                content=wizard,
            )
        )

    def _cerrar_wizard(self):
        self.wizard_activo = None
        self.overlay.cerrar()

    def _guardar_producto(self, datos: dict, id_producto: int = None):

        if id_producto is None:
            resultado = self._producto_service.crear(datos)
        else:
            resultado = self._producto_service.actualizar(id_producto, datos)

        if resultado.fallo:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        self._cerrar_wizard()
        self._refrescar_catalogo()
        MensajeSistema.exito(self.page, resultado.mensaje or "Producto guardado correctamente.")

    # =====================================================
    # ACCIONES DEL MENÚ CONTEXTUAL
    # =====================================================

    def _duplicar_producto(self, producto):

        resultado = self._producto_service.duplicar(producto.get("id_producto"))

        if resultado.fallo:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        self._refrescar_catalogo()
        MensajeSistema.exito(self.page, "Producto duplicado correctamente.")

    def _ver_composicion(self, producto):
        MensajeSistema.informacion(
            self.page,
            f"Composición de '{producto.get('nombre')}' — pendiente de implementar.",
        )

    def _alternar_activo(self, producto):

        resultado = self._producto_service.eliminar(producto.get("id_producto"))

        if resultado.fallo:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        self._refrescar_catalogo()
        MensajeSistema.exito(self.page, resultado.mensaje or "Producto desactivado.")

    def _eliminar_producto(self, producto):
        self._alternar_activo(producto)

    # =====================================================
    # BÚSQUEDAS DEL ASISTENTE
    # =====================================================

    def _buscar_recetas(self, texto):
        if not self._recetas_service:
            return []
        resultado = self._recetas_service.buscar(texto)
        if resultado.fallo:
            return []
        return [
            {"id": r.get("id_receta"), "nombre": r.get("nombre_receta")}
            for r in (resultado.datos or [])
        ]

    def _buscar_ingredientes(self, texto):
        if not self._ingrediente_service:
            return []
        resultado = self._ingrediente_service.buscar(texto)
        if resultado.fallo:
            return []
        return [
            {"id": i.get("id_ingrediente"), "nombre": i.get("nombre_ingrediente")}
            for i in (resultado.datos or [])
        ]

    def _buscar_productos(self, texto):
        resultado = self._producto_service.buscar(texto)
        if resultado.fallo:
            return []
        return [
            {"id": p.get("id_producto"), "nombre": p.get("nombre")}
            for p in (resultado.datos or [])
        ]

    def _buscar_empaques(self, texto):
        return self._buscar_activos_por_tipo("empaque", texto)

    def _buscar_costos_indirectos(self, texto):
        return self._buscar_activos_por_tipo("costo_indirecto", texto)

    def _buscar_activos_por_tipo(self, tipo: str, texto: str):
        if not self._activo_service:
            return []
        # ActivoService.obtener_por_tipo() devuelve una lista plana de
        # diccionarios (igual que listar()/buscar()), no un ServiceResult.
        activos = self._activo_service.obtener_por_tipo(tipo) or []
        texto = (texto or "").lower().strip()
        if texto:
            activos = [a for a in activos if texto in (a.get("nombre") or "").lower()]
        return [{"id": a.get("id_activo"), "nombre": a.get("nombre")} for a in activos]

    def _calcular_preview(self, datos: dict) -> dict:
        """
        Le pasa al wizard un cálculo de costo/precio en vivo (sin guardar
        nada), para que pueda sugerir el precio de cada presentación
        mientras el usuario todavía está completando el producto.
        """
        resultado = self._producto_service.calcular_preview(datos)
        if resultado.fallo:
            return {}
        return resultado.datos or {}

    def _obtener_tasas_hora(self) -> dict:
        """
        Callback que el wizard usa para calcular mano de obra y costos
        indirectos a partir del tiempo de preparación (ver
        ProductoWizard._obtener_tasas_hora). Devuelve el desglose ya
        calculado por ParametrosNegocioService (costo_hora_trabajo,
        tasa_servicios_por_hora, tasa_depreciacion_por_hora,
        costo_hora_total), o {} si no hay servicio configurado o falla
        la consulta -- el wizard ya sabe mostrar el aviso correspondiente
        cuando recibe un desglose vacío.
        """
        if not self._parametros_negocio_service:
            return {}
        resultado = self._parametros_negocio_service.obtener_desglose()
        if resultado.fallo:
            return {}
        return resultado.datos or {}