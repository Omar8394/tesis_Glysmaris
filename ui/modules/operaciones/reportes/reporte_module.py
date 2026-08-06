"""
============================================================
Sistema La Dulce Tía

Archivo:
    reporte_module.py

Responsabilidad:
    Módulo de reportes y exportación a PDF.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import inspect
import flet as ft
from typing import Dict, List, Optional
from datetime import datetime

from ui.core.services.factory import ServiceFactory
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.selector import Selector
from ui.components.selector_fecha import SelectorFecha
from ui.components.tabla import TablaDatos, ColumnaTabla
from ui.components.toolbar import Toolbar
from ui.components.tarjetas import TarjetaEstadistica
from ui.components.paginador import Paginador
from ui.layouts.tabla_con_resumen_layout import TablaConResumenLayout
from ui.core.spacing import AppSpacing
from ui.core.icons import AppIcons
from ui.core.sizes import AppSize
from ui.components.mensajes import MensajeSistema


class ReporteModule:
    """
    Módulo para generar reportes históricos y exportarlos a PDF.
    """

    def __init__(self, page: ft.Page, content_area: ft.Container, usuario=None):
        self.page = page
        self.content_area = content_area
        self.usuario = usuario
        self._service = ServiceFactory.get_reporte_service()
        self._datos_actuales: List[Dict] = []
        self._tipo_seleccionado: str = "ingredientes"
        self._fecha_inicio: Optional[str] = None
        self._fecha_fin: Optional[str] = None
        self._historial_reportes: List[Dict] = []
        self._tabla = None
        self._resumen_container = None
        self._pdf_bytes: Optional[bytes] = None
        self._file_picker: Optional[ft.FilePicker] = None

        # ✅ Guarda contra consultas superpuestas: sin esto, si _cambio_fecha
        # dispara _consultar automáticamente y el usuario alcanza a pulsar
        # "Consultar" en el mismo instante, se podían encolar dos consultas
        # y la segunda pisaba el estado de botones que dejó la primera.
        self._cargando: bool = False

        # Controles de filtro
        self._selector_tipo = None
        self._fecha_inicio_control = None
        self._fecha_fin_control = None
        self._btn_consultar = None
        self._btn_limpiar = None
        self._btn_exportar_pdf = None

        # ✅ Paginación: antes `paginador=None` se pasaba directo al layout
        # (nunca se instanciaba Paginador), así que la tabla mostraba TODOS
        # los registros de una sola vez, sin scroll ni forma de navegar.
        # La paginación es del lado del cliente (sobre self._datos_actuales,
        # que ya contiene el resultado completo filtrado) porque el
        # repositorio no soporta LIMIT/OFFSET todavía.
        self._paginador: Optional[Paginador] = None
        self._elementos_por_pagina = 5

    def construir(self) -> ft.Control:
        """
        Construye la vista del módulo.
        """
        # ----- Toolbar con filtros -----
        self._selector_tipo = Selector(
            etiqueta="Tipo de reporte",
            opciones=[
                "Ingredientes (Lotes)",
                "Ventas",
                "Producción",
                "Mermas",
            ],
            valor="Ingredientes (Lotes)",
            width=AppSize.DROPDOWN_MEDIUM,
            on_change=self._cambio_tipo,
        )

        self._fecha_inicio_control = SelectorFecha(
            page=self.page,
            etiqueta="Fecha inicio",
            width=AppSize.FIELD_SMALL,
            on_change=self._cambio_fecha,
        )
        self._fecha_fin_control = SelectorFecha(
            page=self.page,
            etiqueta="Fecha fin",
            width=AppSize.FIELD_SMALL,
            on_change=self._cambio_fecha,
        )

        self._btn_consultar = BotonPrimario(
            texto="Consultar",
            icono=AppIcons.SEARCH,
            on_click=self._consultar,
        )
        self._btn_limpiar = BotonSecundario(
            texto="Limpiar filtros",
            icono=None,
            on_click=self._limpiar_filtros,
        )
        self._btn_exportar_pdf = BotonSecundario(
            texto="Exportar PDF",
            icono=AppIcons.PDF,
            on_click=self._exportar_pdf,
            disabled=True,
        )

        toolbar = Toolbar(
            izquierda=[
                self._selector_tipo,
                self._fecha_inicio_control,
                self._fecha_fin_control,
            ],
            derecha=[
                self._btn_consultar,
                self._btn_limpiar,
                self._btn_exportar_pdf,
            ]
        )

        # ----- Tabla de resultados -----
        self._tabla = TablaDatos(
            columnas=self._columnas_para_tipo(self._tipo_seleccionado),
            seleccionar=None,
        )
        self._tabla.expand = True

        # ----- Paginador -----
        self._paginador = Paginador(
            on_change=self._cambio_pagina,
            elementos_por_pagina=self._elementos_por_pagina,
        )

        # ----- Resumen (tarjetas estadísticas) -----
        self._resumen_container = ft.Row(
            spacing=AppSpacing.CONTROL_SPACING,
            wrap=True,
        )
        self._actualizar_resumen()

        # ----- Layout principal -----
        layout = TablaConResumenLayout(
            resumen=self._resumen_container,
            toolbar=toolbar,
            tabla=ft.Container(
                content=self._tabla,
                expand=True,
            ),
            paginador=self._paginador,
            expand=True,
        )

        # Carga inicial
        self._consultar(None)

        return layout

    def cargar(self):
        """Recarga los datos (llamado al navegar al módulo)."""
        self._consultar(None)

    # ============================================================
    # MANEJADORES DE EVENTOS
    # ============================================================
    def _cambio_tipo(self, e):
        tipo_texto = self._selector_tipo.value
        self._tipo_seleccionado = self._mapear_tipo(tipo_texto)
        # Se limpian los datos del tipo anterior: si no se hace esto,
        # _actualizar_resumen() calcula las tarjetas usando datos del
        # tipo viejo con la lógica del tipo nuevo (cifras erróneas).
        self._datos_actuales = []
        self._tabla.establecer_columnas(self._columnas_para_tipo(self._tipo_seleccionado))
        self._safe_update(self._tabla)
        self._btn_exportar_pdf.disabled = True
        self._safe_update(self._btn_exportar_pdf)
        # Se vuelve a consultar automáticamente con el nuevo tipo (usando
        # el mismo rango de fechas ya seleccionado).
        self._consultar(None)

    def _cambio_fecha(self, e):
        self._fecha_inicio = self._fecha_inicio_control.obtener()
        self._fecha_fin = self._fecha_fin_control.obtener()
        self._btn_exportar_pdf.disabled = True
        self._safe_update(self._btn_exportar_pdf)

        # ✅ BUG: antes, cambiar una fecha solo actualizaba las variables
        # internas y deshabilitaba "Exportar PDF" — la tabla y las
        # tarjetas se quedaban mostrando los datos del rango anterior
        # hasta que el usuario pulsara "Consultar" manualmente. Esto era
        # inconsistente con _cambio_tipo (que sí vuelve a consultar solo)
        # y daba la sensación de que el campo de fecha "no hacía nada".
        # Ahora el comportamiento es el mismo para ambos filtros.
        self._consultar(None)

    def _consultar(self, e):
        # ✅ Evita disparar una segunda consulta mientras la primera
        # todavía está en curso (p. ej. el auto-consultar de una fecha
        # se solapa con un clic manual en "Consultar").
        if self._cargando:
            return

        # ✅ BUG SILENCIOSO: si fecha_inicio queda después de fecha_fin,
        # la consulta SQL (WHERE fecha >= inicio AND fecha <= fin) no
        # falla, simplemente no encuentra nada. Antes eso se veía igual
        # que "no hay datos en ese rango", así que el usuario no tenía
        # forma de saber que el problema era el rango mismo.
        if not self._rango_fechas_valido():
            return

        self._cargando = True
        self._btn_consultar.disabled = True
        self._safe_update(self._btn_consultar)

        try:
            tipo = self._tipo_seleccionado
            fecha_ini = self._fecha_inicio
            fecha_fin = self._fecha_fin

            resultado = self._service.obtener_datos(tipo, fecha_ini, fecha_fin)
            if resultado.fallo:
                MensajeSistema.error(self.page, resultado.mensaje)
                return

            datos = resultado.datos
            self._datos_actuales = datos

            # ✅ El paginador se resetea a la página 1 en cada consulta nueva
            # (silencioso: no dispara on_change ni una recarga extra) y se
            # le informa el total de registros. La tabla solo recibe la
            # porción de la página actual, no self._datos_actuales completo.
            self._paginador.resetear_pagina_silencioso()
            self._paginador.establecer_total(len(datos), actualizar=False)
            self._safe_update(self._paginador)
            self._poblar_tabla(self._datos_pagina_actual())

            # ✅ BUG: antes se hacía `self._btn_exportar_pdf.disabled = False`
            # sin condición, así que una consulta exitosa con 0 filas dejaba
            # el botón de exportar habilitado (aunque exportar_pdf luego lo
            # rechazara con una advertencia). Ahora el botón refleja si
            # realmente hay datos para exportar.
            self._btn_exportar_pdf.disabled = not bool(datos)
            self._safe_update(self._btn_exportar_pdf)

            self._actualizar_resumen()
            self.update()

            # Si la consulta tuvo éxito pero no hay registros, se avisa
            # solo cuando el usuario disparó la acción (clic o cambio de
            # filtro), no en la carga inicial silenciosa del módulo.
            if not datos and e is not None:
                MensajeSistema.informacion(
                    self.page,
                    "No se encontraron registros para los filtros seleccionados.",
                )
        finally:
            self._cargando = False
            self._btn_consultar.disabled = False
            self._safe_update(self._btn_consultar)

    def _cambio_pagina(self, pagina: int, elementos_por_pagina: int):
        """
        Callback del Paginador: no vuelve a consultar la base de datos,
        solo re-renderiza la tabla con la porción correspondiente de
        self._datos_actuales (que ya tiene el resultado completo filtrado).
        """
        self._poblar_tabla(self._datos_pagina_actual())

    def _datos_pagina_actual(self) -> List[Dict]:
        pagina = self._paginador.obtener_pagina()
        tam = self._elementos_por_pagina
        inicio = (pagina - 1) * tam
        return self._datos_actuales[inicio: inicio + tam]

    def _limpiar_filtros(self, e):
        """
        Restablece fechas y vuelve a consultar con el tipo actual sin
        filtro de rango (equivalente a "ver todo el historial").
        """
        self._fecha_inicio_control.limpiar()
        self._fecha_fin_control.limpiar()
        self._fecha_inicio = None
        self._fecha_fin = None
        self._consultar(None)

    def _exportar_pdf(self, e):
        if not self._datos_actuales:
            MensajeSistema.advertencia(self.page, "No hay datos para exportar.")
            return

        tipo = self._tipo_seleccionado
        fecha_ini = self._fecha_inicio
        fecha_fin = self._fecha_fin

        resultado = self._service.generar_pdf(tipo, self._datos_actuales, fecha_ini, fecha_fin)
        if resultado.fallo:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        self._pdf_bytes = resultado.datos
        # El nombre del archivo ahora incluye el tipo de reporte (antes
        # todos los PDFs se llamaban "Reporte_<fecha>.pdf" sin importar si
        # eran de ventas, mermas, etc. — fácil de confundir al tener varios
        # descargados).
        nombre_archivo = (
            f"Reporte_{self._tipo_seleccionado}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        # ✅ BUG: `ft.FilePicker(on_result=...)` es la firma de Flet
        # clásico. En versiones recientes de Flet, FilePicker YA NO acepta
        # `on_result` -- el resultado se obtiene con
        # `await file_picker.save_file(...)`, que devuelve la ruta
        # directamente. Con la firma nueva, construir
        # `ft.FilePicker(on_result=...)` lanza un TypeError al vuelo; si
        # Flet no expone ese traceback en la interfaz, se siente
        # exactamente igual que "presioné el botón y no pasó nada". Se
        # detecta en tiempo de ejecución cuál API hay disponible para no
        # depender de fijar una versión exacta de Flet.
        if "on_result" in inspect.signature(ft.FilePicker.__init__).parameters:
            self._guardar_pdf_legacy(nombre_archivo)
        else:
            self.page.run_task(self._guardar_pdf_moderno, nombre_archivo)

    def _guardar_pdf_legacy(self, nombre_archivo: str):
        """Flet clásico: FilePicker con callback on_result."""
        # Se guarda como atributo de instancia (self._file_picker) en vez
        # de variable local para poder quitar SOLO este control del
        # overlay en _on_file_picker_result, sin tocar lo demás que haya
        # ahí (los DatePicker de "Fecha inicio"/"Fecha fin", por ejemplo).
        self._file_picker = ft.FilePicker(on_result=self._on_file_picker_result)
        self.page.overlay.append(self._file_picker)
        self.page.update()
        self._file_picker.save_file(file_name=nombre_archivo, allowed_extensions=["pdf"])

    def _on_file_picker_result(self, e: ft.FilePickerResultEvent):
        self._procesar_resultado_guardado(e.path)
        # Solo se quita este FilePicker puntual del overlay (no
        # page.overlay.clear(), que borraría también los DatePicker de
        # fecha_inicio/fecha_fin).
        if self._file_picker in self.page.overlay:
            self.page.overlay.remove(self._file_picker)
        self.page.update()

    async def _guardar_pdf_moderno(self, nombre_archivo: str):
        """Flet reciente: save_file() es async y devuelve la ruta directamente."""
        file_picker = ft.FilePicker()
        self.page.overlay.append(file_picker)
        self.page.update()
        try:
            ruta = await file_picker.save_file(
                file_name=nombre_archivo,
                allowed_extensions=["pdf"],
            )
            self._procesar_resultado_guardado(ruta)
        finally:
            if file_picker in self.page.overlay:
                self.page.overlay.remove(file_picker)
            self.page.update()

    def _procesar_resultado_guardado(self, ruta: Optional[str]):
        """Lógica común de guardado, compartida por ambos flujos (legacy y moderno)."""
        if ruta:
            try:
                with open(ruta, "wb") as f:
                    f.write(self._pdf_bytes)
                MensajeSistema.exito(self.page, "PDF guardado correctamente.")
                self._historial_reportes.append({
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "tipo": self._tipo_seleccionado,
                    "filtros": f"Fechas: {self._fecha_inicio or 'Inicio'} - {self._fecha_fin or 'Fin'}",
                    "archivo": ruta.split("/")[-1],
                })
            except Exception as ex:
                MensajeSistema.error(self.page, f"Error al guardar: {ex}")
        else:
            MensajeSistema.informacion(self.page, "Exportación cancelada.")

    # ============================================================
    # MÉTODOS AUXILIARES
    # ============================================================
    def _mapear_tipo(self, tipo_texto: str) -> str:
        mapping = {
            "Ingredientes (Lotes)": "ingredientes",
            "Ventas": "ventas",
            "Producción": "produccion",
            "Mermas": "mermas",
        }
        return mapping.get(tipo_texto, "ingredientes")

    def _rango_fechas_valido(self) -> bool:
        """
        Verifica que, si ambas fechas están definidas, el inicio no sea
        posterior al fin. Los valores vienen en formato ISO (YYYY-MM-DD)
        desde SelectorFecha.obtener(), por lo que se pueden comparar
        directamente como strings.
        """
        if self._fecha_inicio and self._fecha_fin and self._fecha_inicio > self._fecha_fin:
            MensajeSistema.advertencia(
                self.page,
                "La fecha de inicio no puede ser posterior a la fecha fin.",
            )
            return False
        return True

    def _columnas_para_tipo(self, tipo: str) -> List[ColumnaTabla]:
        if tipo == "ingredientes":
            return [
                ColumnaTabla("Ingrediente", "nombre_ingrediente", width=200),
                ColumnaTabla("Lote", "id_lote", width=80),
                ColumnaTabla("Stock", "stock_actual", width=100, formato=lambda x: f"{x:.2f}"),
                ColumnaTabla("Unidad", "unidad_medida", width=100),
                ColumnaTabla("Costo Unit.", "costo_unitario", width=120, formato=lambda x: f"${x:.2f}"),
                ColumnaTabla("Ingreso", "fecha_ingreso", width=120),
                ColumnaTabla("Caducidad", "fecha_caducidad", width=120),
            ]
        elif tipo == "ventas":
            return [
                ColumnaTabla("ID Venta", "id_venta", width=80),
                ColumnaTabla("Fecha", "fecha_venta", width=140),
                ColumnaTabla("Cliente", "cliente_nombre", width=180),
                ColumnaTabla("Subtotal", "subtotal", width=100, formato=lambda x: f"${x:.2f}"),
                ColumnaTabla("Descuento", "descuento", width=100, formato=lambda x: f"${x:.2f}"),
                ColumnaTabla("Total", "total", width=100, formato=lambda x: f"${x:.2f}"),
                ColumnaTabla("Estado", "estado", width=100),
            ]
        elif tipo == "produccion":
            return [
                ColumnaTabla("N° Orden", "numero_orden", width=120),
                ColumnaTabla("Fecha Planif.", "fecha_planificada", width=120),
                ColumnaTabla("Estado", "estado", width=100),
                ColumnaTabla("Prioridad", "prioridad", width=100),
                ColumnaTabla("Responsable", "responsable", width=150),
                ColumnaTabla("Costo Real", "costo_real", width=100, formato=lambda x: f"${x:.2f}"),
                ColumnaTabla("Tiempo Real", "tiempo_real_minutos", width=100, formato=lambda x: f"{x} min"),
            ]
        elif tipo == "mermas":
            return [
                ColumnaTabla("Fecha", "fecha_registro", width=140),
                ColumnaTabla("Cantidad", "cantidad", width=100, formato=lambda x: f"{x:.2f}"),
                ColumnaTabla("Unidad", "unidad", width=80),
                ColumnaTabla("Tipo", "tipo_merma", width=120),
                ColumnaTabla("Motivo", "motivo", width=150),
                ColumnaTabla("Costo Asoc.", "costo_asociado", width=100, formato=lambda x: f"${x:.2f}"),
                ColumnaTabla("Producto/Ingrediente", "producto_asociado", width=180),
            ]
        return []

    def _poblar_tabla(self, datos: List[Dict]):
        self._tabla.limpiar()
        columnas = self._columnas_para_tipo(self._tipo_seleccionado)
        for fila in datos:
            valores = []
            for col in columnas:
                campo = col.campo
                valor = fila.get(campo)
                if col.formato and valor is not None:
                    valor = col.formato(valor)
                # `valor or ""` descartaría valores legítimos como 0; solo
                # se reemplaza cuando el valor es None.
                valores.append(valor if valor is not None else "")
            self._tabla.agregar_fila(valores, item_id=fila.get("id"))
        self._safe_update(self._tabla)

    def _actualizar_resumen(self):
        if not self._datos_actuales:
            self._resumen_container.controls = []
            self._safe_update(self._resumen_container)
            return

        total_registros = len(self._datos_actuales)
        # `d.get(campo) or 0` en vez de `d.get(campo, 0)`: si el campo
        # existe en la fila pero su valor es NULL en la base de datos,
        # dict.get devuelve None (el default de dict.get solo aplica
        # cuando la clave no existe) y float(None) lanza TypeError.
        if self._tipo_seleccionado == "ingredientes":
            total_stock = sum(float(d.get("stock_actual") or 0) for d in self._datos_actuales)
            tarjetas = [
                TarjetaEstadistica("Total Registros", total_registros, icono=AppIcons.INVENTARIO),
                TarjetaEstadistica("Stock Total", f"{total_stock:.2f}", icono=AppIcons.INGREDIENT),
            ]
        elif self._tipo_seleccionado == "ventas":
            total_ventas = sum(float(d.get("total") or 0) for d in self._datos_actuales)
            tarjetas = [
                TarjetaEstadistica("Total Ventas", total_registros, icono=AppIcons.SALES),
                TarjetaEstadistica("Monto Total", f"${total_ventas:.2f}", icono=AppIcons.MONEY),
            ]
        elif self._tipo_seleccionado == "produccion":
            total_costo = sum(float(d.get("costo_real") or 0) for d in self._datos_actuales)
            tarjetas = [
                TarjetaEstadistica("Órdenes", total_registros, icono=AppIcons.PRODUCTION),
                TarjetaEstadistica("Costo Real Total", f"${total_costo:.2f}", icono=AppIcons.MONEY),
            ]
        elif self._tipo_seleccionado == "mermas":
            total_mermas = sum(float(d.get("cantidad") or 0) for d in self._datos_actuales)
            tarjetas = [
                TarjetaEstadistica("Mermas", total_registros, icono=AppIcons.ERROR),
                TarjetaEstadistica("Cantidad Total", f"{total_mermas:.2f}", icono=AppIcons.INGREDIENT),
            ]
        else:
            tarjetas = []

        self._resumen_container.controls = tarjetas
        self._safe_update(self._resumen_container)

    def _safe_update(self, control):
        """
        Llama a control.update() solo si el control ya está adjunto a la
        página. Flet lanza AssertionError ("Control must be added to the
        page first") si se llama .update() sobre un control individual
        antes de que el layout que lo contiene haya sido agregado a la
        página — algo que pasa aquí porque construir() llama a
        _consultar(None) (que a su vez llama _poblar_tabla y
        _actualizar_resumen) ANTES de hacer `return layout`, es decir,
        antes de que reporte_view() añada ese layout a la página.
        """
        if control.page is not None:
            control.update()

    def update(self):
        """Actualiza la página."""
        self.page.update()