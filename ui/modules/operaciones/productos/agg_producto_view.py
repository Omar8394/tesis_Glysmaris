"""
Vista para agregar/editar productos.
Muestra campos: receta, nombre, tipo, mano de obra, empaques, costos indirectos, margen.
"""

from __future__ import annotations
import flet as ft
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.components.campo_texto import CampoTexto
from ui.components.selector import Selector
from ui.components.tarjetas import TarjetaFormulario
from ui.components.mensajes import MensajeSistema
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing
from ui.core.services.factory import ServiceFactory


class AggProductoView(ft.Container):
    def __init__(self, page, service, on_save, producto=None):
        super().__init__()
        self.page = page
        self.service = service
        self.on_save = on_save
        self.producto = producto
        self.expand = True
        self.padding = AppSpacing.LG

        # Servicios auxiliares
        self.recetas_service = ServiceFactory.get_recetas_service()
        self.activos_service = ServiceFactory.get_activo_service()

        # ----- CAMPOS -----
        # Receta (obligatorio)
        self.receta_selector = Selector(
            etiqueta="Receta base *",
            width=None,
            expand=True,
        )
        self._cargar_recetas()

        # Nombre (se autocompleta con la receta, pero puede editarse)
        self.nombre = CampoTexto(
            etiqueta="Nombre del producto *",
            expand=True,
        )

        self.tipo = Selector(
            etiqueta="Tipo de producto",
            opciones=["Dulce", "Salado", "Pasapalo", "Frío", "Porción", "Torta", "Cupcake", "Galleta", "Postre", "Otro"],
        )

        self.descripcion = CampoTexto(
            etiqueta="Descripción",
            multiline=True,
            expand=True,
        )

        # ----- COSTOS Y MÁRGENES -----
        self.mano_obra = CampoTexto(
            etiqueta="Mano de obra (ej: 0.4 = 40% del subtotal)",
            hint="0.4 (40%)",
            expand=True,
        )

        # Selección múltiple de empaques con Checkboxes
        self.empaques_container = ft.Column(spacing=5)
        self.empaques_checkboxes = []

        # Selección múltiple de costos indirectos con Checkboxes
        self.costos_container = ft.Column(spacing=5)
        self.costos_checkboxes = []

        self.margen = CampoTexto(
            etiqueta="Margen (%)",
            value="40",
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Previsualización de costos
        self.txt_costo_receta = ft.Text("Costo receta: $0.00", size=12, italic=True)
        self.txt_empaques = ft.Text("Empaques: $0.00", size=12, italic=True)
        self.txt_costos = ft.Text("Costos indirectos: $0.00", size=12, italic=True)
        self.txt_mano_obra = ft.Text("Mano de obra: $0.00", size=12, italic=True)
        self.txt_precio_final = ft.Text("Precio final sugerido: $0.00", size=14, weight="bold")

        self.btn_calcular = BotonPrimario(
            texto="Calcular precio",
            on_click=self._calcular,
        )

        self.btn_guardar = BotonPrimario(
            texto="Guardar",
            icono=AppIcons.SAVE,
            on_click=self._guardar,
            expand=True,
        )
        self.btn_cancelar = BotonSecundario(
            texto="Cancelar",
            icono=AppIcons.CANCEL,
            on_click=self._cancelar,
            expand=True,
        )

        # Cargar listas de activos
        self._cargar_activos()

        # Si estamos editando, cargar datos
        if self.producto:
            self._cargar_producto()

        self.content = self._crear_layout()

    def _cargar_recetas(self):
        resultado = self.recetas_service.listar()
        if resultado.exito:
            opciones = [f"{r['id_receta']} - {r['nombre_receta']}" for r in resultado.datos]
            self.receta_selector.establecer_opciones(opciones)
            if self.producto and self.producto.get("receta_id"):
                # Buscar el nombre de la receta para mostrarlo
                for r in resultado.datos:
                    if r["id_receta"] == self.producto["receta_id"]:
                        self.receta_selector.value = f"{r['id_receta']} - {r['nombre_receta']}"
                        break

    def _cargar_activos(self):
        # Empaques
        res = self.activos_service.obtener_por_tipo("empaque")
        if res.exito:
            self.empaques_checkboxes.clear()
            for activo in res.datos:
                cb = ft.Checkbox(
                    label=activo["nombre"],
                    value=False,
                    data=activo["id_activo"],
                )
                self.empaques_checkboxes.append(cb)
            self.empaques_container.controls = self.empaques_checkboxes

        # Costos indirectos
        res = self.activos_service.obtener_por_tipo("costo_indirecto")
        if res.exito:
            self.costos_checkboxes.clear()
            for activo in res.datos:
                cb = ft.Checkbox(
                    label=activo["nombre"],
                    value=False,
                    data=activo["id_activo"],
                )
                self.costos_checkboxes.append(cb)
            self.costos_container.controls = self.costos_checkboxes

    def _cargar_producto(self):
        self.nombre.value = self.producto.get("nombre_producto", "")
        self.tipo.value = self.producto.get("tipo_producto", "")
        self.descripcion.value = self.producto.get("descripcion_producto", "")
        self.mano_obra.value = str(self.producto.get("mano_obra", 0))
        self.margen.value = str(self.producto.get("margen_porcentaje", 40))

        # Pre-seleccionar empaques y costos indirectos si se almacenan en el producto
        # (esto requiere que guardes los IDs en una tabla relacional, pendiente de implementar)

    def _crear_layout(self):
        titulo = "Editar Producto" if self.producto else "Nuevo Producto"

        # Scrollable container para los checkboxes
        scroll_empaques = ft.Container(
            content=ft.Column(
                [self.empaques_container],
                scroll=ft.ScrollMode.AUTO,  # <--- MUEVE EL SCROLL A LA COLUMNA
                height=120,
            ),
            height=120,
            border=ft.border.all(1, "#2D3748"),
            border_radius=5,
            padding=5,
        )
        
        scroll_costos = ft.Container(
            content=ft.Column(
                [self.costos_container],
                scroll=ft.ScrollMode.AUTO,  # <--- MUEVE EL SCROLL A LA COLUMNA
                height=120,
            ),
            height=120,
            border=ft.border.all(1, "#2D3748"),
            border_radius=5,
            padding=5,
            
        )

        formulario = ft.Column(
            [
                self.receta_selector,
                self.nombre,
                ft.Row([self.tipo, self.margen], spacing=AppSpacing.SM),
                self.descripcion,
                ft.Divider(),
                ft.Text("Costos y márgenes", weight="bold"),
                self.mano_obra,
                ft.Text("Empaques (selecciona los que usarás)", size=12, italic=True),
                scroll_empaques,
                ft.Text("Costos indirectos (selecciona los que usarás)", size=12, italic=True),
                scroll_costos,
                self.btn_calcular,
                ft.Column(
                    [
                        self.txt_costo_receta,
                        self.txt_empaques,
                        self.txt_costos,
                        self.txt_mano_obra,
                        self.txt_precio_final,
                    ],
                    spacing=5,
                ),
                ft.Divider(),
                ft.Row([self.btn_guardar, self.btn_cancelar], spacing=AppSpacing.SM),
            ],
            spacing=AppSpacing.SM,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        return TarjetaFormulario(
            titulo=titulo,
            icono=AppIcons.PRODUCT,
            contenido=formulario,
            expand=True,
        )

    def _obtener_ids_seleccionados(self, checkboxes):
        """Devuelve los IDs de los checkboxes seleccionados."""
        return [cb.data for cb in checkboxes if cb.value]

    def _calcular(self, e=None):
        # Obtener ID de receta
        receta_text = self.receta_selector.value
        if not receta_text:
            MensajeSistema.advertencia(self.page, "Seleccione una receta.")
            return
        receta_id = int(receta_text.split(" - ")[0])

        # Obtener IDs de empaques y costos indirectos seleccionados
        empaques_ids = self._obtener_ids_seleccionados(self.empaques_checkboxes)
        costos_ids = self._obtener_ids_seleccionados(self.costos_checkboxes)

        try:
            mano_obra = float(self.mano_obra.value) if self.mano_obra.value else 0
        except ValueError:
            mano_obra = 0

        try:
            margen = float(self.margen.value) if self.margen.value else 40
        except ValueError:
            margen = 40

        # Llamar al servicio para calcular
        res = self.service.calcular_precio_final(
            receta_id=receta_id,
            mano_obra=mano_obra,
            ids_empaques=empaques_ids,
            ids_costos_indirectos=costos_ids,
            margen_porcentaje=margen,
        )
        if not isinstance(res, tuple):
            MensajeSistema.error(self.page, "Error en el cálculo.")
            return

        costo_receta, total_empaques, total_costos, mano_obra_val, precio_final = res

        # Actualizar previsualización
        self.txt_costo_receta.value = f"Costo receta: ${costo_receta:.2f}"
        self.txt_empaques.value = f"Empaques: ${total_empaques:.2f}"
        self.txt_costos.value = f"Costos indirectos: ${total_costos:.2f}"
        self.txt_mano_obra.value = f"Mano de obra: ${mano_obra_val:.2f}"
        self.txt_precio_final.value = f"Precio final sugerido: ${precio_final:.2f}"
        self.update()

    def _guardar(self, e):
        # Validar receta
        if not self.receta_selector.value:
            MensajeSistema.error(self.page, "Seleccione una receta.")
            return

        receta_id = int(self.receta_selector.value.split(" - ")[0])

        # Recolectar datos
        datos = {
            "nombre": self.nombre.value.strip(),
            "tipo": self.tipo.value or "Otro",
            "receta_id": receta_id,
            "descripcion": self.descripcion.value.strip(),
            "mano_obra": float(self.mano_obra.value) if self.mano_obra.value else 0,
            "margen_porcentaje": float(self.margen.value) if self.margen.value else 40,
            "ids_empaques": self._obtener_ids_seleccionados(self.empaques_checkboxes),
            "ids_costos_indirectos": self._obtener_ids_seleccionados(self.costos_checkboxes),
        }

        if self.producto:
            resultado = self.service.actualizar(self.producto["id_producto"], datos)
        else:
            resultado = self.service.crear(datos)

        if resultado.fallo:
            MensajeSistema.error(self.page, resultado.mensaje)
            return

        MensajeSistema.exito(self.page, resultado.mensaje)
        if self.on_save:
            self.on_save(datos)

    def _cancelar(self, e):
        if self.on_save:
            self.on_save(None)