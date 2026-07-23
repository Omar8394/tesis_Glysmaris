# ui/components/ingrediente_formulario.py

from __future__ import annotations
import flet as ft
from typing import Callable
from ui.components.campo_texto import CampoTexto
from ui.components.autocompletado import AutoCompletado
from ui.components.selector import Selector
from ui.components.selector_fecha import SelectorFecha
from ui.components.tarjetas import TarjetaFormulario
from ui.components.boton import BotonPrimario, BotonSecundario
from ui.core.icons import AppIcons
from ui.core.spacing import AppSpacing


class IngredienteFormulario(ft.UserControl):
    """
    Formulario de ingredientes reutilizable.
    No conoce el servicio. Solo recibe datos y devuelve un dict al guardar.
    """

    def __init__(
        self,
        page: ft.Page,
        on_guardar: callable,
        on_cancelar: callable,
        datos_iniciales: dict = None,
        buscar_nombres: Callable[[str], list] | None = None,
    ):
        super().__init__()
        self.page = page
        self.on_guardar = on_guardar
        self.on_cancelar = on_cancelar
        self.datos_iniciales = datos_iniciales or {}
        # ✅ El formulario sigue sin conocer el service: recibe un callback
        # ya conectado desde IngredienteModule para pedir sugerencias.
        self.buscar_nombres = buscar_nombres
        # ✅ El campo "Stock" significa cosas distintas según el modo:
        # - Crear: cantidad de ARTÍCULOS que estás ingresando (se multiplica
        #   por "Contenido por unidad" en el service).
        # - Editar: cantidad REAL restante, ya en la unidad base del
        #   ingrediente (no se vuelve a multiplicar).
        self._es_edicion = bool(self.datos_iniciales)
        self._crear_campos()

    def _crear_campos(self):
        datos = self.datos_iniciales
        # Campos
        self.nombre = AutoCompletado(
            etiqueta="Nombre del ingrediente",
            buscar=self.buscar_nombres,
            width=350,
        )
        if datos.get("nombre_ingrediente"):
            self.nombre.establecer(datos.get("nombre_ingrediente"))
        self.stock = CampoTexto(
            etiqueta="Stock actual" if self._es_edicion else "Cantidad de artículos",
            width=170,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint="Ej: si compraste 3 bolsas, poné 3" if not self._es_edicion else None,
            value=str(datos.get("stock_actual", "")),
        )
        self.unidad = Selector(
            etiqueta="Unidad de medida",
            opciones=["g", "kg", "ml", "L", "unidad"],
            valor=datos.get("unidad_medida"),
            width=170,
        )
        self.costo = CampoTexto(
            etiqueta="Costo ($)",
            width=170,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(datos.get("costo_unitario", "")),
        )
        # ✅ Antes era texto libre ("1kg / 200ml") y nunca se usaba para
        # calcular nada -- por eso el stock de ingredientes en g/ml quedaba
        # mal. Ahora es numérico, EN LA MISMA "Unidad de medida" elegida
        # arriba (ej. si unidad = g y cada artículo trae 500g, acá va 500).
        self.contenido = CampoTexto(
            etiqueta="Contenido por unidad (en la unidad de medida)",
            width=250,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint="Ej: 500 (si cada artículo trae 500g)",
            value=str(datos.get("contenido_unidad", "") or ""),
        )
        self.categoria = Selector(
            etiqueta="Categoría",
            opciones=[
                "Decoración",
                "Elaboración",
                "Esencias",
                "Lácteos",
                "Chocolate",
                "Frutas",
                "Otros",
            ],
            valor=datos.get("categoria"),
            width=300,
        )
        self.fecha_ingreso = SelectorFecha(
            page=self.page,
            etiqueta="Fecha ingreso",
            width=190,
        )
        self.fecha_caducidad = SelectorFecha(
            page=self.page,
            etiqueta="Fecha vencimiento",
            width=190,
        )
        if datos:
            self.fecha_ingreso.establecer(datos.get("fecha_ingreso"))
            self.fecha_caducidad.establecer(datos.get("fecha_caducidad"))

        self.perecedero = ft.Switch(
            label="Perecedero",
            value=datos.get("perecedero", False),
        )
        self.refrigerado = ft.Switch(
            label="Refrigerado",
            value=datos.get("refrigerado", False),
        )
        self.descripcion = CampoTexto(
            etiqueta="Descripción",
            multiline=True,
            width=350,
            value=datos.get("descripcion", ""),
        )

    def build(self):
        """Construye la tarjeta del formulario."""
        fila1 = ft.Row([self.nombre, self.costo, self.stock], spacing=AppSpacing.CONTROL_SPACING)
        fila2 = ft.Row([self.contenido, self.unidad], spacing=AppSpacing.CONTROL_SPACING)
        fila3 = ft.Row(
            [self.categoria, self.fecha_ingreso, self.fecha_caducidad],
            spacing=AppSpacing.CONTROL_SPACING,
            wrap=True,
        )
        fila4 = ft.Row([self.perecedero, self.refrigerado], spacing=AppSpacing.CONTROL_SPACING)
        fila5 = ft.Row([self.descripcion], spacing=AppSpacing.CONTROL_SPACING)

        btn_guardar = BotonPrimario(
            texto="Guardar",
            icono=AppIcons.SAVE,
            on_click=self._guardar,
        )
        btn_cancelar = BotonSecundario(
            texto="Cancelar",
            icono=AppIcons.CANCEL,
            on_click=self._cancelar,
        )
        fila_botones = ft.Row(
            [btn_guardar, btn_cancelar],
            alignment=ft.MainAxisAlignment.END,
            spacing=AppSpacing.BUTTON_SPACING,
        )

        return TarjetaFormulario(
            titulo="Agregar Ingrediente" if not self.datos_iniciales else "Editar Ingrediente",
            contenido=[fila1, fila2, fila3, fila4, fila5, fila_botones],
            expand=False,
            width=750,
        )

    def _guardar(self, e):
        datos = {
            "nombre": self.nombre.obtener(),
            "stock": float(self.stock.value) if self.stock.value else 0,
            "unidad": self.unidad.value,
            "costo": float(self.costo.value) if self.costo.value else 0,
            "contenido_unidad": float(self.contenido.value) if self.contenido.value else 1,
            "categoria": self.categoria.value,
            "fecha_ingreso": self.fecha_ingreso.obtener() or None,
            "caducidad": self.fecha_caducidad.obtener() or None,
            "perecedero": self.perecedero.value,
            "refrigerado": self.refrigerado.value,
            "descripcion": self.descripcion.value,
        }
        self.on_guardar(datos)

    def _cancelar(self, e):
        self.on_cancelar()

    def establecer_datos(self, datos: dict):
        # ✅ Si se reutiliza esta misma instancia para editar un lote,
        # "Stock" pasa a significar la cantidad real restante en unidad
        # base (no cantidad de artículos) -- ver comentario en __init__.
        self._es_edicion = True
        self.nombre.establecer(datos.get("nombre_ingrediente", ""))
        self.stock.value = str(datos.get("stock_actual", ""))
        self.unidad.value = datos.get("unidad_medida")
        self.costo.value = str(datos.get("costo_unitario", ""))
        self.contenido.value = str(datos.get("contenido_unidad", "") or "")
        self.categoria.value = datos.get("categoria")
        self.fecha_ingreso.establecer(datos.get("fecha_ingreso"))
        self.fecha_caducidad.establecer(datos.get("fecha_caducidad"))
        self.perecedero.value = datos.get("perecedero", False)
        self.refrigerado.value = datos.get("refrigerado", False)
        self.descripcion.value = datos.get("descripcion", "")
        self.update()