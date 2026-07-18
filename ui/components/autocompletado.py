"""
============================================================
Sistema La Dulce Tía

Archivo:
    autocompletado.py

Responsabilidad:
    Campo de búsqueda con sugerencias reutilizable.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.campo_texto import CampoTexto
from ui.core.spacing import AppSpacing
from ui.core.theme_manager import ThemeManager

class AutoCompletado(ft.UserControl):
    """
    Campo de autocompletado reutilizable.

    No conoce la fuente de datos.
    Solo sabe pedir sugerencias mediante callbacks.
    """
    def __init__(

        self,

        etiqueta="Buscar",

        buscar: Callable[[str], list] | None = None,

        seleccionar: Callable[[str], None] | None = None,

        width=320,

        max_sugerencias=8,

    ):

        super().__init__()

        self.tema = ThemeManager.theme

        self.buscar = buscar

        self.seleccionar = seleccionar

        self.max_sugerencias = max_sugerencias

        self._width = width

        self.campo = CampoTexto(

            etiqueta=etiqueta,

            width=width,

            on_change=self._texto_cambiado,

        )

        self.lista_sugerencias = ft.Column(visible=False, spacing=0)

        # ✅ Guarda el resultado completo elegido de la lista de
        # sugerencias (p.ej. {"id":.., "nombre":..}), no solo el texto
        # que queda en el campo. Se resetea apenas el usuario vuelve a
        # escribir, para no arrastrar el id de una selección vieja.
        self._seleccionado = None

    def build(self):
        # Enfoque simple: la lista de sugerencias vive DEBAJO del campo,
        # dentro del flujo normal (sin Stack). Al aparecer, empuja hacia
        # abajo lo que esté debajo en el formulario/toolbar, en vez de
        # flotar por encima. Es más predecible y evita los problemas de
        # recorte (clipping) que tuvimos con el Stack + Container flotante.
        return ft.Container(
            content=ft.Column(
                controls=[
                    self.campo,             # Campo de texto arriba
                    self.lista_sugerencias  # Lista de sugerencias abajo
                ],
                spacing=5,
                tight=True,
            ),
            width=self._width,
        )

    def _texto_cambiado(self, e):

        texto = self.campo.value.strip()

        # El usuario está editando el texto a mano: ya no vale la
        # selección (ni el id) que pudiera haber de antes.
        self._seleccionado = None

        if not texto:

            self._ocultar()

            return

        if self.buscar is None:

            self._ocultar()

            return

        resultados = self.buscar(texto)

        self._mostrar_sugerencias(resultados)

    def _mostrar_sugerencias(self, resultados):
        # 1. Limpias los controles anteriores de la lista
        self.lista_sugerencias.controls.clear()

        # 2. Llenas la lista con los nuevos botones/opciones de los resultados
        #    Cada resultado puede ser un string suelto (compatibilidad con
        #    buscadores viejos) o un dict {"id":.., "nombre":..} (nuevo
        #    formato, necesario para poder guardar referencias reales).
        for res in resultados:
            texto_mostrado = res["nombre"] if isinstance(res, dict) else res
            self.lista_sugerencias.controls.append(
                ft.ListTile(
                    title=ft.Text(texto_mostrado),
                    on_click=lambda e, val=res: self._seleccionar(val)
                )
            )

        # 3. Haces visible la lista para que empuje el formulario de manera limpia
        self.lista_sugerencias.visible = True
        if self.page:
            self.update()

    def _seleccionar(

        self,

        valor,

    ):

        if isinstance(valor, dict):

            self.campo.value = valor.get("nombre", "")

            self._seleccionado = valor

        else:

            self.campo.value = valor

            self._seleccionado = None

        self._ocultar()

        if self.seleccionar:

            self.seleccionar(valor)

        self.update()


    def _ocultar(self):
        # Al ocultarse, los campos de abajo regresan a su posición original
        self.lista_sugerencias.visible = False
        if self.page:
            self.update()

    def obtener(self):
        """
        Devuelve el texto actual del campo.
        """

        return self.campo.value.strip()

    def obtener_id(self):
        """
        Devuelve el id del resultado elegido en la lista de sugerencias,
        o None si el usuario escribió texto libre sin seleccionar nada
        de la lista (o si el buscador todavía devuelve solo strings).
        """

        if self._seleccionado is None:

            return None

        return self._seleccionado.get("id")

    def establecer(self, valor, id=None):
        """
        Establece un valor en el campo. Si se pasa `id` (por ejemplo, al
        abrir el wizard en modo edición con un valor ya guardado), queda
        disponible en obtener_id() sin necesidad de que el usuario vuelva
        a elegir de la lista de sugerencias.
        """

        self.campo.value = valor or ""

        self._seleccionado = {"id": id, "nombre": valor} if id is not None else None

        self._ocultar()

        if self.page:
            self.update()

    def limpiar(self):
        """
        Limpia el campo y elimina las sugerencias.
        """

        self.campo.value = ""

        self._seleccionado = None

        self._ocultar()

        self.update()

    def enfocar(self):
        """
        Coloca el foco sobre el campo.
        """

        self.campo.focus()

    def actualizar(self):
        """
        Fuerza una actualización de las sugerencias.
        """

        texto = self.obtener()

        if not texto:

            self._ocultar()

            return

        if self.buscar:

            resultados = self.buscar(texto)

            self._mostrar_sugerencias(resultados)

    def mostrar(self, resultados):
        """
        Muestra manualmente una lista de resultados.
        """

        self._mostrar_sugerencias(resultados)

    def tiene_valor(self):
        """
        Indica si el campo contiene información.
        """

        return bool(self.obtener())

    def deshabilitar(self):

        self.campo.disabled = True

        self.update()

    def habilitar(self):

        self.campo.disabled = False

        self.update()

    def cambiar_busqueda(self, callback):

        self.buscar = callback

    def cambiar_seleccion(self, callback):

        self.seleccionar = callback