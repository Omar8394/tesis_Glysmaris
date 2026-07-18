# ui/modules/operaciones/recetas/recetas_module.py

"""
============================================================
Sistema La Dulce Tía

Archivo:
    recetas_module.py

Responsabilidad:
    Módulo de Recetas. Administra los sucesos de la UI
    (clicks, cambios de selección, etc.) y delega toda la
    lógica de negocio en RecetasService. No contiene SQL ni
    reglas de negocio -- solo arma componentes y reacciona a
    sus eventos, igual que IngredienteModule.

AJUSTAR IMPORTS: las rutas de abajo son un supuesto -- cámbialas
para que coincidan con la ubicación real de esos archivos en tu
proyecto.
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.components.barra_acciones import Accion, BarraAcciones
from ui.components.buscador import Buscador
from ui.components.crud_view import EncabezadoCRUD
from ui.components.dialogo import Dialogo
from ui.components.mensajes import MensajeSistema
from ui.components.recetas_form import RecetasForm
from ui.components.selector import Selector
from ui.components.toolbar import Toolbar
from ui.core.icons import AppIcons
from ui.core.services.factory import ServiceFactory
from ui.layouts.crud_layout import CRUDLayout


# ============================================================
# CONSTANTES DE NEGOCIO
# ============================================================

TIPOS_FILTRO = ["Todos", "Base", "Relleno", "Cobertura", "Receta clásica", "Otro"]

COLORES_TIPO = {
    "Base": ft.colors.BLUE_400,
    "Relleno": ft.colors.ORANGE_400,
    "Cobertura": ft.colors.PURPLE_400,
    "Receta clásica": ft.colors.GREEN_400,
    "Otro": ft.colors.GREY_400,
    "Sin categoría": ft.colors.GREY_600,
}


class RecetasModule:

    def __init__(self, page, content_area, service=None):

        self.page = page
        self.content_area = content_area
        self.service = service or ServiceFactory.get_recetas_service()

        # Componentes
        self.form = RecetasForm()
        self.buscador = None
        self.selector_tipo = None
        self.toolbar = None
        self.lista_recetas = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)

        # Estado
        # `_ingredientes` es la lista de trabajo de la receta que se
        # está armando (con "origen"/"uid" por cada item -- ver
        # RecetasService). Vive acá, no en el service ni en el form.
        self._ingredientes: list[dict] = []
        self._seleccionado = None          # id_receta en edición (None = nueva)
        self._filtro_actual = ""
        self._filtro_tipo = "Todos"
        self._layout_principal = None

        self._crear_toolbar()
        self._conectar_formulario()

    # ============================================================
    # CONSTRUCCIÓN DEL LAYOUT PRINCIPAL
    # ============================================================

    def construir(self) -> ft.Control:

        if self._layout_principal is None:

            encabezado = EncabezadoCRUD(
                titulo="Recetas",
                icono=AppIcons.RECIPE,
            )

            # ✅ Sin scroll acá: self.form ya scrollea internamente (tiene
            # su propio Column(scroll=AUTO) + Container(expand=True)).
            # Anidar OTRO expand+scroll encima es lo que causaba que
            # panel_costos se dibujara superpuesto sobre los botones del
            # form (el hijo expand no tiene de qué tamaño expandirse
            # dentro de un eje "sin límite" por el scroll del padre).
            # Este Column solo reparte el espacio: form se lleva lo que
            # sobra (expand=True) y panel_costos su tamaño natural.
            

            historial = ft.Container(
                expand=True,
                content=self.lista_recetas,
            )

            self._layout_principal = CRUDLayout(
                encabezado=encabezado,
                toolbar=self.toolbar,
                historial=historial,
                formulario=self.form,
            )

            self.cargar()  # ✅ carga inicial

        return self._layout_principal

    # ============================================================
    # TOOLBAR
    # ============================================================

    def _crear_toolbar(self):

        self.buscador = Buscador(
            buscar=self._buscar,
            placeholder="Buscar receta...",
            width=250,
            mostrar_actualizar=False,
        )

        self.selector_tipo = Selector(
            etiqueta="Tipo",
            opciones=TIPOS_FILTRO,
            valor="Todos",
            width=170,
            on_change=self._filtrar_por_tipo,
        )

        btn_refrescar = ft.IconButton(
            icon=AppIcons.REFRESH,
            tooltip="Refrescar",
            on_click=lambda e: self.cargar(),
        )

        self.toolbar = Toolbar(
            izquierda=[self.buscador, self.selector_tipo, btn_refrescar],

        )

    # ============================================================
    # CONEXIÓN DE EVENTOS: RecetasForm -> este módulo
    # ============================================================

    def _conectar_formulario(self):

        self.form.on_agregar = self._agregar_ingrediente
        self.form.on_editar_cantidad = self._editar_cantidad_ingrediente
        self.form.on_eliminar = self._eliminar_ingrediente

        self.form.on_base_changed = lambda id_r: self._sincronizar_componente("base", id_r)
        self.form.on_relleno_changed = lambda id_r: self._sincronizar_componente("relleno", id_r)
        self.form.on_cobertura_changed = lambda id_r: self._sincronizar_componente("cobertura", id_r)

        self.form.on_calcular = self._recalcular_costos
        self.form.on_guardar = self._guardar
        self.form.on_nuevo = self._nueva_receta
        self.form.on_cancelar = self._cancelar_edicion


    # ============================================================
    # CARGA DE DATOS
    # ============================================================

    def _esta_montado(self) -> bool:
        return bool(self.page)

    def cargar(self):

        if not self._esta_montado():
            return

        resultado = self.service.listar(self._filtro_actual)

        if not resultado.exito:
            MensajeSistema.error(self.page, resultado.mensaje)
            self._poblar_historial([])
            return

        datos_filtrados = self._filtrar_por_tipo_local(resultado.datos or [])
        self._poblar_historial(datos_filtrados)

        self._cargar_catalogo_ingredientes()
        self._cargar_componentes()

        # Si `cargar()` se llama desde `construir()` (primera carga),
        # el layout todavía no fue agregado a la página -- llamar a
        # update() ahí explota con "Control must be added to the page
        # first.". Se actualiza solo si ya está montado.
        if self._layout_principal is not None and self._layout_principal.page:
            self._layout_principal.update()

    def _filtrar_por_tipo_local(self, recetas):

        if self._filtro_tipo == "Todos":
            return recetas

        return [
            r for r in recetas
            if (r.get("tipo_receta") or "Sin categoría") == self._filtro_tipo
        ]

    def _cargar_catalogo_ingredientes(self):

        resultado = self.service.obtener_ingredientes_catalogo()

        if resultado.exito:
            self.form.cargar_ingredientes(resultado.datos or [])

    def _cargar_componentes(self):
        """
        Carga las opciones de Base/Relleno/Cobertura, excluyendo la
        receta que se está editando actualmente (una receta no puede
        usarse a sí misma como su propio componente).
        """

        mapa = (
            ("Base", self.form.cargar_bases),
            ("Relleno", self.form.cargar_rellenos),
            ("Cobertura", self.form.cargar_coberturas),
        )

        for tipo, cargar in mapa:

            resultado = self.service.obtener_por_tipo(tipo)
            opciones = resultado.datos or [] if resultado.exito else []

            if self._seleccionado is not None:
                opciones = [
                    r for r in opciones
                    if r["id_receta"] != self._seleccionado
                ]

            cargar(opciones)

    # ============================================================
    # LISTA LATERAL (HISTORIAL AGRUPADO POR TIPO)
    # ============================================================

    def _poblar_historial(self, recetas):

        grupos: dict[str, list] = {}

        for r in recetas:
            tipo = r.get("tipo_receta") or "Sin categoría"
            grupos.setdefault(tipo, []).append(r)

        controles = []

        for tipo, recs in grupos.items():

            color = COLORES_TIPO.get(tipo, ft.colors.GREY_600)

            controles.append(
                ft.Row(
                    [
                        ft.Icon(AppIcons.CATEGORY, color=color, size=16),
                        ft.Text(tipo.upper(), size=13, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(f"({len(recs)})", size=11, color=ft.colors.GREY_500),
                    ],
                    spacing=5,
                )
            )

            for rec in recs:
                controles.append(self._tarjeta_receta(rec))

        self.lista_recetas.controls = controles

        if self.lista_recetas.page:
            self.lista_recetas.update()

    def _tarjeta_receta(self, receta):

        return ft.Card(
            content=ft.Container(
                padding=10,
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(receta["nombre_receta"], weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(
                                    receta.get("tipo_receta", "Sin categoría"),
                                    size=11,
                                    color=ft.colors.GREY_600,
                                ),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=AppIcons.EDIT,
                            icon_size=18,
                            tooltip="Editar receta",
                            on_click=lambda e, r=receta: self._editar_receta(r["id_receta"]),
                        ),
                        ft.IconButton(
                            icon=AppIcons.DELETE,
                            icon_size=18,
                            icon_color=ft.colors.RED_400,
                            tooltip="Eliminar receta",
                            on_click=lambda e, r=receta: self._confirmar_eliminar(
                                r["id_receta"], r["nombre_receta"],
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ),
        )

    # ============================================================
    # FILTROS Y BÚSQUEDA
    # ============================================================

    def _buscar(self, texto: str):

        self._filtro_actual = texto.strip()
        self.cargar()

    def _filtrar_por_tipo(self, e=None):

        self._filtro_tipo = self.selector_tipo.value or "Todos"
        self.cargar()

    # ============================================================
    # COMPONENTES: BASE / RELLENO / COBERTURA
    # ============================================================

    def _sincronizar_componente(self, origen, id_receta_componente):

        self._ingredientes = self.service.sincronizar_componente(
            self._ingredientes, origen, id_receta_componente,
        )

        self._refrescar_ingredientes()

    # ============================================================
    # INGREDIENTES PROPIOS
    # ============================================================

    def _agregar_ingrediente(self):

        datos = self.form.obtener_datos()

        if not datos["ingrediente"]:
            MensajeSistema.advertencia(self.page, "Seleccioná un ingrediente.")
            return

        try:
            cantidad = float(datos["cantidad"]) if datos["cantidad"] else 0
        except ValueError:
            cantidad = 0

        if cantidad <= 0:
            MensajeSistema.advertencia(self.page, "La cantidad debe ser mayor a cero.")
            return

        id_ing = int(datos["ingrediente"])

        nombre_ing = next(
            (
                opt.text
                for opt in self.form.dd_ingrediente.options
                if opt.key == str(id_ing)
            ),
            "Desconocido",
        )

        self._ingredientes = self.service.agregar_ingrediente(
            self._ingredientes, id_ing, nombre_ing, cantidad, datos["unidad"],
        )

        self.form.txt_cantidad.value = ""
        self.form.dd_ingrediente.value = None
        self.form.update()

        self._refrescar_ingredientes()

    def _editar_cantidad_ingrediente(self, uid, valor):

        try:
            nueva_cantidad = float(valor) if valor else 0
        except ValueError:
            nueva_cantidad = 0

        self._ingredientes = self.service.actualizar_cantidad(
            self._ingredientes, uid, nueva_cantidad,
        )

        # No se llama a _refrescar_ingredientes() completo acá para no
        # perder el foco del campo mientras el usuario escribe -- solo
        # se recalculan los costos.
        self._recalcular_costos()

    def _eliminar_ingrediente(self, uid):

        self._ingredientes = self.service.eliminar_ingrediente(self._ingredientes, uid)

        self._refrescar_ingredientes()

    # ============================================================
    # COSTOS
    # ============================================================

    def _recalcular_costos(self):
        subtotal = self.service.calcular_subtotal(self._ingredientes)
        sugerido = self.service.calcular_precio_sugerido(self._ingredientes)
        self.form.actualizar_costos(subtotal, sugerido)

    def _refrescar_ingredientes(self):
        self.form.mostrar_ingredientes(self._ingredientes)
        self._recalcular_costos()
    # ============================================================
    # NUEVA / CANCELAR / GUARDAR
    # ============================================================

    def _limpiar_todo(self):

        self._ingredientes = []
        self.form.limpiar()
        self._recalcular_costos()

    def _nueva_receta(self, e=None):

        self._seleccionado = None
        self._limpiar_todo()
        self.form.modo_edicion(False)
        self._cargar_componentes()

    def _cancelar_edicion(self):

        self._nueva_receta()

    def _guardar(self):

        datos_form = self.form.obtener_datos()

        # Verificación de stock: informativa, no bloquea el guardado.
        resultado_stock = self.service.verificar_stock(self._ingredientes)

        if resultado_stock.datos:

            detalle = ", ".join(
                f"{f['ingrediente']} (stock {f['stock']}, solicitado {f['solicitado']})"
                for f in resultado_stock.datos
            )

            MensajeSistema.advertencia(self.page, f"Stock insuficiente: {detalle}")

        datos = {
            "nombre": datos_form["nombre"],
            "tipo": datos_form["tipo"],
            "descripcion": "",
            "ingredientes": self._ingredientes,
        }

        resultado = self.service.guardar(datos, self._seleccionado)

        if not resultado.exito:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        MensajeSistema.exito(self.page, resultado.mensaje)

        self._nueva_receta()
        self.cargar()

    # ============================================================
    # EDITAR / ELIMINAR
    # ============================================================

    def _editar_receta(self, id_receta):

        resultado = self.service.obtener(id_receta)

        if not resultado.exito:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        self._limpiar_todo()

        receta = resultado.datos["receta"]
        ingredientes_bd = resultado.datos["ingredientes"]

        self.form.cargar(receta)

        # NOTA: la base de datos no guarda qué ingredientes vinieron de
        # una base/relleno/cobertura, así que todos se cargan como
        # "propios". Si esta receta usaba componentes, hay que volver
        # a marcarlos para poder editarlos por separado.
        self._ingredientes = self.service.preparar_ingredientes_para_edicion(ingredientes_bd)

        self._seleccionado = id_receta

        self.form.modo_edicion(True)
        self._cargar_componentes()
        self._refrescar_ingredientes()

    def _confirmar_eliminar(self, id_receta, nombre):

        def eliminar(e):

            resultado = self.service.eliminar(id_receta)

            if resultado.exito:
                MensajeSistema.exito(self.page, resultado.mensaje)
            else:
                MensajeSistema.error(self.page, resultado.mensaje)

            self.cargar()

        Dialogo.confirmacion(
            page=self.page,
            mensaje=f"¿Estás seguro de eliminar la receta '{nombre}'?",
            on_confirmar=eliminar,
            titulo="Eliminar receta",
            texto_confirmar="Eliminar",
        )