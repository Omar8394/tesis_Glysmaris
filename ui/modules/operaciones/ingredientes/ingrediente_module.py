# ui/modules/operaciones/ingredientes/ingrediente_module.py

from __future__ import annotations
import flet as ft
from datetime import datetime, date  # ✅ Importación agregada

from ui.components.barra_acciones import Accion, BarraAcciones
from ui.components.autocompletado import AutoCompletado
from ui.components.dialogo import Dialogo
from ui.components.mensajes import MensajeSistema
from ui.components.paginador import Paginador
from ui.components.selector import Selector
from ui.components.tabla import ColumnaTabla, TablaDatos, AccionTabla, EstadoFila
from ui.components.toolbar import Toolbar
from ui.components.overlay import Overlay
from ui.components.ingrediente_formulario import IngredienteFormulario
from ui.components.resumen_ingredientes import ResumenIngredientes
from ui.core.icons import AppIcons
from ui.core.services.factory import ServiceFactory
from ui.layouts.tabla_con_resumen_layout import TablaConResumenLayout
from ui.components.buscador import Buscador

# ============================================================
# CONSTANTES DE NEGOCIO
# ============================================================

# Días de anticipación para avisar que algo está por caducar.
# Los ingredientes perecederos/refrigerados tienen vida útil más corta,
# así que necesitan avisarse con más cuidado (umbral más chico pero de
# revisión más frecuente) para no perder el producto.

UMBRAL_DIAS_GENERAL = 30
UMBRAL_DIAS_FRAGIL = 10


def _a_fecha(valor):
    """Normaliza cualquier valor de fecha (date, datetime o string) a date."""
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _formatear_fecha(valor):
    fecha = _a_fecha(valor)
    return fecha.strftime("%d/%m/%Y") if fecha else ""


def _formatear_moneda(valor):
    try:
        return f"${float(valor or 0):.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _formatear_stock(valor):
    try:
        return f"{float(valor or 0):.2f}"
    except (TypeError, ValueError):
        return "0.00"


class IngredienteModule:
    def __init__(self, page, content_area, service=None):
        self.page = page
        self.content_area = content_area
        self.service = service or ServiceFactory.get_ingrediente_service()

        # Componentes
        self.resumen = ResumenIngredientes()
        self.tabla = None
        self.toolbar = None
        self.paginador = None
        self.buscador = None
        self.overlay = Overlay(visible=False)
        self.formulario = None

        # Estado
        self._seleccionado = None
        self._filtro_actual = ""
        self._layout_principal = None
        self._primera_carga = True  # ✅ para no repetir la alerta de frágiles en cada refresco

        # Crear componentes
        self._crear_buscador()
        self._crear_toolbar()
        self._crear_tabla()
        self._crear_paginador()

    # ============================================================
    # CONSTRUCCIÓN DEL LAYOUT PRINCIPAL
    # ============================================================

    def construir(self) -> ft.Control:
        if self._layout_principal is None:
            self._layout_principal = TablaConResumenLayout(
                resumen=self.resumen,
                toolbar=self.toolbar,
                tabla=self.tabla,
                paginador=self.paginador,
                overlay=self.overlay,
            )
            self.cargar()  # ✅ carga inicial
        return self._layout_principal

    # ============================================================
    # COMPONENTES
    # ============================================================

    def _crear_buscador(self):
    # Buscador simple que filtra en vivo al escribir
        self.buscador = Buscador(
            buscar=self._buscar,
            placeholder="Buscar ingrediente...",
            width=250,
            mostrar_actualizar=False,  # Opcional: ocultar botón de actualizar
            mostrar_limpiar=True,
        )

    def _filtrar_y_sugerir(self, texto):
        self._buscar(texto)
        return self.service.buscar_nombres(texto)

    def _crear_toolbar(self):
        # Filtros
        self.selector_categoria = Selector(
            etiqueta="Categoría",
            opciones=["Todas", "Decoración", "Elaboración", "Esencias", "Lácteos", "Chocolate", "Frutas", "Otros"],
            valor="Todas",
            width=150,
            on_change=self._aplicar_filtros,
        )
        self.selector_unidad = Selector(
            etiqueta="Unidad",
            opciones=["Todas", "g", "kg", "ml", "L", "unidad"],
            valor="Todas",
            width=120,
            on_change=self._aplicar_filtros,
        )
        self.selector_stock = Selector(
            etiqueta="Stock",
            opciones=["Todos", "Bajo (< 10)", "Medio (10-50)", "Alto (> 50)"],
            valor="Todos",
            width=130,
            on_change=self._aplicar_filtros,
        )

        # Botón Nuevo
        self.btn_nuevo = Accion(
            texto="Nuevo",
            icono=AppIcons.ADD,
            callback=self._agregar,
            primario=True,
        )
        barra_acciones = BarraAcciones([self.btn_nuevo])

        # Botón Refrescar
        btn_refrescar = ft.IconButton(
            icon=AppIcons.REFRESH,
            tooltip="Refrescar",
            on_click=self._refrescar,
        )

        # Toolbar
        self.toolbar = Toolbar(
            izquierda=[
                self.buscador,
                self.selector_categoria,
                self.selector_unidad,
                self.selector_stock,
                btn_refrescar,
            ],
            derecha=barra_acciones.controls,
        )

    def _crear_tabla(self):
        self._columnas = [
            ColumnaTabla("ID", campo="id_lote", width=50),
            ColumnaTabla("Ingrediente", campo="nombre_ingrediente", width=170),
            ColumnaTabla("Stock", campo="stock_actual", width=90,
                         formato=_formatear_stock),
            ColumnaTabla("Unidad", campo="unidad_medida", width=70),
            ColumnaTabla("Costo Uni.", campo="costo_unitario", width=90,
                         formato=_formatear_moneda),
            ColumnaTabla("Categoría", campo="categoria", width=110),
            ColumnaTabla("Caducidad", campo="fecha_caducidad", width=100,
                         formato=_formatear_fecha),
        ]
        acciones = [
            AccionTabla(icono=AppIcons.EDIT, tooltip="Editar", callback=self._editar_seleccionado),
            AccionTabla(icono=AppIcons.DELETE, tooltip="Eliminar", callback=self._eliminar_seleccionado, color="error"),
        ]
        self.tabla = TablaDatos(columnas=self._columnas, acciones=acciones, seleccionar=self._seleccionar_fila)

    def _crear_paginador(self):
        self.paginador = Paginador(on_change=self._cambiar_pagina, elementos_por_pagina=5)

    # ============================================================
    # CARGA DE DATOS
    # ============================================================

    def _esta_montado(self) -> bool:
        """✅ Verifica si el módulo ya tiene una página asociada para refrescar UI."""
        return bool(self.page)

    def cargar(self):
        # ✅ Aunque el layout aún no esté completamente montado, la carga de
        # datos debe seguir funcionando. El refresco visual se hará de forma
        # segura y se reintenta si el control todavía no está en el árbol.
        if not self._esta_montado():
            return

        resultado = self.service.listar(self._filtro_actual)
        if not resultado.exito:
            MensajeSistema.error(self.page, resultado.mensaje)
            self._poblar_tabla([])
            self._actualizar_resumen([], mostrar_alerta=False)
            if self._layout_principal is not None:
                self._layout_principal.update()
            return

        # ✅ Filtro real por categoría / unidad / stock (antes se ignoraba)
        datos_filtrados = self._filtrar_datos(resultado.datos or [])

        try:
            # ✅ Actualizamos el paginador ANTES de recortar, para que ajuste
            # total de páginas / página actual según el total ya filtrado.
            self._actualizar_paginador(datos_filtrados)
            datos_pagina = self._paginar(datos_filtrados)
            self._poblar_tabla(datos_pagina)
            # ✅ El resumen usa el total FILTRADO completo (no solo la
            # página visible), para que las tarjetas reflejen todo lo que
            # cumple el filtro, no solo lo que se ve en pantalla.
            self._actualizar_resumen(datos_filtrados, mostrar_alerta=self._primera_carga)
            self._primera_carga = False

            if self._layout_principal is not None:
                self._layout_principal.update()
            if self.page is not None:
                self.page.update()
        except AssertionError:
            # ✅ Salvaguarda extra por si algún subcomponente llama a
            # .update() internamente antes de estar montado.
            if self.page is not None:
                self.page.update()

    def _paginar(self, datos):
    
        if not self.paginador:
            return datos
        por_pagina = self.paginador.elementos_por_pagina
        pagina = self.paginador.obtener_pagina()
        inicio = (pagina - 1) * por_pagina
        return datos[inicio: inicio + por_pagina]

    def _filtrar_datos(self, datos):
        """Aplica los filtros de categoría, unidad y stock elegidos en la toolbar."""
        categoria = self.selector_categoria.value
        unidad = self.selector_unidad.value
        stock = self.selector_stock.value

        def cumple(item):
            if categoria and categoria != "Todas" and item.get("categoria") != categoria:
                return False
            if unidad and unidad != "Todas" and item.get("unidad_medida") != unidad:
                return False
            if stock and stock != "Todos":
                valor_stock = item.get("stock_actual", 0) or 0
                if stock == "Bajo (< 10)" and not (valor_stock < 10):
                    return False
                if stock == "Medio (10-50)" and not (10 <= valor_stock <= 50):
                    return False
                if stock == "Alto (> 50)" and not (valor_stock > 50):
                    return False
            return True

        return [item for item in datos if cumple(item)]

    def _estado_fila(self, item):
        """✅ Resalta visualmente los ingredientes perecederos/refrigerados
        próximos a vencer (o ya vencidos), ya que su vida útil corta los
        hace más propensos a generar pérdida si no se detectan a tiempo.
        Devuelve un estado semántico (str) definido en EstadoFila — el
        color real de Flet lo decide tabla.py, no este módulo."""

        fecha_cad = _a_fecha(item.get("fecha_caducidad"))
        if not fecha_cad:
            return None

        dias_restantes = (fecha_cad - date.today()).days
        es_fragil = bool(item.get("perecedero")) or bool(item.get("refrigerado"))
        umbral = UMBRAL_DIAS_FRAGIL if es_fragil else UMBRAL_DIAS_GENERAL

        if dias_restantes < 0:
            return EstadoFila.VENCIDO_CRITICO if es_fragil else EstadoFila.VENCIDO
        if dias_restantes < umbral:
            return EstadoFila.ALERTA if es_fragil else None
        return None

    def _poblar_tabla(self, datos):
        self.tabla.limpiar()
        for item in datos:
            valores = []
            for columna in self._columnas:
                crudo = item.get(columna.campo)
                valores.append(columna.formato(crudo) if columna.formato else crudo)
            self.tabla.agregar_fila(
                valores,
                item_id=item["id_lote"],
                estado=self._estado_fila(item),
            )

    def _actualizar_paginador(self, datos):
        if self.paginador:
            total = len(datos) if datos else 0
            self.paginador.establecer_total(total, actualizar=False)

    def _actualizar_resumen(self, datos, mostrar_alerta: bool = False):
        if not datos:
            total = stock_bajo = por_caducar = categorias = fragiles_por_vencer = 0
            detalle_fragiles = []
        else:
            total = len(datos)
            stock_bajo = sum(1 for item in datos if (item.get("stock_actual", 0) or 0) < 10)
            categorias = len(set(item.get("categoria") for item in datos if item.get("categoria")))

            hoy = date.today()
            por_caducar = 0
            fragiles_por_vencer = 0
            detalle_fragiles = []
            for item in datos:
                fecha_cad = _a_fecha(item.get("fecha_caducidad"))
                if not fecha_cad:
                    continue

                dias_restantes = (fecha_cad - hoy).days
                # ✅ Perecedero o refrigerado = ingrediente "frágil": su vida útil
                # es más corta, así que se avisa con un umbral distinto y se
                # cuenta aparte para poder priorizarlo.
                es_fragil = bool(item.get("perecedero")) or bool(item.get("refrigerado"))
                umbral = UMBRAL_DIAS_FRAGIL if es_fragil else UMBRAL_DIAS_GENERAL

                if dias_restantes < umbral:
                    por_caducar += 1
                    if es_fragil:
                        fragiles_por_vencer += 1
                        detalle_fragiles.append((item.get("nombre_ingrediente", "?"), dias_restantes))

        self.resumen.actualizar(total, stock_bajo, por_caducar, categorias, fragiles_por_vencer)

        if mostrar_alerta:
            self._alertar_fragiles(detalle_fragiles)

    def _alertar_fragiles(self, detalle):
        """Muestra un recordatorio de ingredientes perecederos/refrigerados
        próximos a vencer (pueden generar pérdida si no se usan a tiempo)."""
        if not detalle:
            return

        detalle_ordenado = sorted(detalle, key=lambda t: t[1])  # los más urgentes primero
        partes = []
        for nombre, dias in detalle_ordenado[:5]:
            if dias < 0:
                partes.append(f"{nombre} (¡vencido hace {abs(dias)}d!)")
            else:
                partes.append(f"{nombre} ({dias}d)")
        extra = f" y {len(detalle_ordenado) - 5} más" if len(detalle_ordenado) > 5 else ""

        MensajeSistema.advertencia(
            self.page,
            f"⚠️ {len(detalle_ordenado)} ingrediente(s) perecedero(s)/refrigerado(s) "
            f"por vencer o vencidos: {', '.join(partes)}{extra}. Revisalos antes de "
            f"que se pierdan.",
        )

    # ============================================================
    # FILTROS Y BÚSQUEDA
    # ============================================================

    def _buscar(self, texto: str):
        self._filtro_actual = texto.strip()
        if self.paginador:
            self.paginador.resetear_pagina_silencioso()
        self.cargar()

    def _aplicar_filtros(self, e=None):
        # ✅ El filtrado real ahora ocurre en _filtrar_datos(), llamado desde cargar()
        if self.paginador:
            self.paginador.resetear_pagina_silencioso()
        self.cargar()

    def _refrescar(self, e=None):
        self.cargar()

    def _cambiar_pagina(self, pagina, cantidad):
        self.cargar()

    # ============================================================
    # SELECCIÓN Y ACCIONES
    # ============================================================

    def _seleccionar_fila(self, e):
        # ✅ TablaDatos guarda el id de la fila en row.data (no en .key)
        if hasattr(e.control, "data") and e.control.data is not None:
            self._seleccionado = e.control.data
        else:
            self._seleccionado = None

    def _obtener_seleccionado(self):
        if self._seleccionado is None:
            MensajeSistema.advertencia(self.page, "Seleccione un ingrediente primero.")
            return None
        return self._seleccionado

    def _agregar(self, e=None):
        # ✅ Limpiamos la selección previa para no confundir "crear" con "actualizar"
        self._seleccionado = None
        self._abrir_formulario()

    def _editar(self, e=None):
        id_lote = self._obtener_seleccionado()
        if id_lote is None:
            return
        resultado = self.service.obtener_lote(id_lote)
        if resultado.exito:
            self._abrir_formulario(resultado.datos)
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    def _editar_seleccionado(self, e):
        # ✅ El botón de acción de la fila trae el id en e.control.data
        if hasattr(e.control, "data") and e.control.data is not None:
            self._seleccionado = e.control.data
        self._editar()

    def _eliminar(self, e=None):
        id_lote = self._obtener_seleccionado()
        if id_lote is None:
            return
        resultado = self.service.obtener_lote(id_lote)
        if not resultado.exito:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        datos_lote = resultado.datos
        Dialogo.eliminar_ingrediente(
            page=self.page,
            nombre_ingrediente=datos_lote.get("nombre_ingrediente", "el ingrediente"),
            cantidad_disponible=float(datos_lote.get("stock_actual", 0) or 0),
            on_eliminar=lambda cantidad, motivo: self._confirmar_eliminacion(id_lote, cantidad, motivo),
        )

    def _eliminar_seleccionado(self, e):
        # ✅ El botón de acción de la fila trae el id en e.control.data
        if hasattr(e.control, "data") and e.control.data is not None:
            self._seleccionado = e.control.data
        self._eliminar()

    def _confirmar_eliminacion(self, id_lote, cantidad, motivo):
        resultado = self.service.registrar_perdida(id_lote, cantidad, motivo)
        if resultado.exito:
            MensajeSistema.exito(self.page, resultado.mensaje)
            self.cargar()
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

    # ============================================================
    # FORMULARIO EN OVERLAY
    # ============================================================

    def _abrir_formulario(self, datos=None):
        self.formulario = IngredienteFormulario(
            page = self.page,
            on_guardar=self._guardar_desde_formulario,
            on_cancelar=self._cerrar_formulario,
            datos_iniciales=datos,
            buscar_nombres=self.service.buscar_nombres,
        )
        contenido = ft.Container(
            content=self.formulario,
            alignment=ft.alignment.center,
        )
        self.overlay.abrir(contenido)

    def _cerrar_formulario(self):
        self.overlay.cerrar()

    def _guardar_desde_formulario(self, datos):
        id_lote = self._seleccionado if self._seleccionado else None
        if id_lote:
            # Es una edición explícita de un lote ya seleccionado.
            self._procesar_guardado(id_lote, datos)
            return

        # ✅ Antes de crear uno nuevo, chequeamos si ya existe un ingrediente
        # con ese nombre (para evitar duplicados exactos).
        existente = self.service.obtener_por_nombre(datos.get("nombre", ""))
        if not existente.exito:
            MensajeSistema.error(self.page, existente.mensaje)
            return

        item_existente = existente.datos
        if item_existente:
            # Caso en que el ingrediente ya existe en el catálogo maestro.
            # En lugar de sumarlo matemáticamente en la interfaz, le advertimos al usuario
            # que se abrirá un lote independiente para respetar la estrategia PEPS.
            stock_actual = item_existente.get("stock_actual", 0) or 0
            stock_nuevo = datos.get("stock", 0) or 0
            
            Dialogo.confirmacion(
                page=self.page,
                titulo="Registrar Nuevo Lote",
                mensaje=(
                    f"'{item_existente.get('nombre_ingrediente')}' ya está registrado "
                    f"(Stock actual acumulado: {stock_actual:.2f} {item_existente.get('unidad_medida', '')}).\n\n"
                    f"¿Deseas registrar el ingreso de estos {stock_nuevo:.2f} como un NUEVO LOTE "
                    f"con su propia fecha de vencimiento y costo?"
                ),
                # Al confirmar, pasamos None como ID. El servicio interceptará el nombre,
                # verá que ya existe y creará el lote enlazado automáticamente.
                on_confirmar=lambda e: self._procesar_guardado(None, datos),
                texto_confirmar="Sí, registrar lote",
            )
            return

        # Si el ingrediente es 100% nuevo, se procesa el guardado inicial limpio.
        self._procesar_guardado(None, datos)

    def _procesar_guardado(self, id_lote, datos):
        # Si viene un id_lote, significa que estamos editando un lote existente
        if id_lote:
            resultado = self.service.actualizar_lote(id_lote, datos)
        else:
            # Si no hay id_lote, delegamos la creación al servicio (quien maneja los lotes)
            resultado = self.service.crear(datos)

        if resultado.exito:
            # Notificación de éxito, cerramos el formulario flotante y recargamos la tabla
            MensajeSistema.exito(self.page, resultado.mensaje)
            self.overlay.cerrar()
            self.cargar()
        else:
            # Si hubo un error en la capa de negocio o base de datos, mostramos el aviso
            MensajeSistema.error(self.page, resultado.mensaje)