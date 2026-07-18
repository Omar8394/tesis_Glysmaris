from __future__ import annotations

import flet as ft

from ui.components.costos_panel import CostosPanel   # <-- importación


class RecetasForm(ft.Container):

    TIPOS_RECETA = [
        "Base",
        "Relleno",
        "Cobertura",
        "Receta clásica",
        "Otro",
    ]

    UNIDADES = [
        "g",
        "kg",
        "ml",
        "L",
        "unidad",
        "1 taza",
        "1/2 taza",
        "1/3 taza",
        "1/4 taza",
        "cucharada",
        "cucharadita",
    ]

    TITULOS_ORIGEN = {
        "base": "Ingredientes de la Base",
        "relleno": "Ingredientes del Relleno",
        "cobertura": "Ingredientes de la Cobertura",
    }

    def __init__(self):
        super().__init__(expand=True)

        # Eventos públicos (igual que antes)
        self.on_agregar = None
        self.on_guardar = None
        self.on_nuevo = None
        self.on_cancelar = None
        self.on_calcular = None

        self.on_base_changed = None
        self.on_relleno_changed = None
        self.on_cobertura_changed = None

        self.on_editar_cantidad = None
        self.on_eliminar = None

        # ---------------------------------------------------
        # Campos principales
        # ---------------------------------------------------
        self.txt_nombre = ft.TextField(
            label="Nombre de la receta",
            expand=True,
        )

        self.dd_tipo = ft.Dropdown(
            label="Tipo",
            width=220,
            value="Base",
            options=[ft.dropdown.Option(x) for x in self.TIPOS_RECETA],
        )

        # ---------------------------------------------------
        # Ingredientes propios
        # ---------------------------------------------------
        self.dd_ingrediente = ft.Dropdown(
            label="Ingrediente",
            width=260,
        )

        self.txt_cantidad = ft.TextField(
            label="Cantidad",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.dd_unidad = ft.Dropdown(
            label="Unidad",
            width=170,
            value="g",
            options=[ft.dropdown.Option(x) for x in self.UNIDADES],
        )

        self.btn_agregar = ft.IconButton(
            icon=ft.icons.ADD,
            tooltip="Agregar ingrediente",
            on_click=self._agregar,
        )

        self.tbl_propios = self._construir_tabla()

        # ---------------------------------------------------
        # Componentes opcionales
        # ---------------------------------------------------
        self.chk_base = ft.Checkbox(label="Usa Base")
        self.chk_relleno = ft.Checkbox(label="Usa Relleno")
        self.chk_cobertura = ft.Checkbox(label="Usa Cobertura")

        self.dd_base = ft.Dropdown(label="Base", disabled=True, width=320)
        self.dd_relleno = ft.Dropdown(label="Relleno", disabled=True, width=320)
        self.dd_cobertura = ft.Dropdown(label="Cobertura", disabled=True, width=320)

        self.chk_base.on_change = self._habilitar_dropdowns
        self.chk_relleno.on_change = self._habilitar_dropdowns
        self.chk_cobertura.on_change = self._habilitar_dropdowns

        self.dd_base.on_change = lambda e: self._cambiar_componente(self.on_base_changed, self.dd_base.value)
        self.dd_relleno.on_change = lambda e: self._cambiar_componente(self.on_relleno_changed, self.dd_relleno.value)
        self.dd_cobertura.on_change = lambda e: self._cambiar_componente(self.on_cobertura_changed, self.dd_cobertura.value)

        self.tbl_base = self._construir_tabla()
        self.tbl_relleno = self._construir_tabla()
        self.tbl_cobertura = self._construir_tabla()

        self.sec_base = self._construir_seccion("base", self.tbl_base)
        self.sec_relleno = self._construir_seccion("relleno", self.tbl_relleno)
        self.sec_cobertura = self._construir_seccion("cobertura", self.tbl_cobertura)

        # ---------------------------------------------------
        # Panel de costos (integrado)
        # ---------------------------------------------------
        self.panel_costos = CostosPanel()

        # ---------------------------------------------------
        # Botones
        # ---------------------------------------------------
        self.btn_nuevo = ft.ElevatedButton(
            "Nueva",
            icon=ft.icons.ADD,
            on_click=lambda e: self._evento(self.on_nuevo),
        )

        self.btn_guardar = ft.ElevatedButton(
            "Guardar",
            icon=ft.icons.SAVE,
            on_click=lambda e: self._evento(self.on_guardar),
        )

        self.btn_cancelar = ft.OutlinedButton(
            "Cancelar",
            icon=ft.icons.CLOSE,
            visible=False,
            on_click=lambda e: self._evento(self.on_cancelar),
        )

        # ---------------------------------------------------
        # Layout
        # ---------------------------------------------------
        self.content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            controls=[
                ft.Row([self.btn_nuevo, self.btn_guardar, self.btn_cancelar]),
                ft.Divider(),
                ft.Row([self.txt_nombre, self.dd_tipo]),
                ft.Text("Ingredientes propios", weight=ft.FontWeight.BOLD),
                ft.Row(
                    [self.dd_ingrediente, self.txt_cantidad, self.dd_unidad, self.btn_agregar],
                    wrap=True,
                ),
                ft.Container(
                    content=self.tbl_propios,
                    border=ft.border.all(1, "#2D3748"),
                    border_radius=5,
                    padding=5,
                ),
                ft.Divider(),
                ft.Text("Componentes opcionales", weight=ft.FontWeight.BOLD),
                self.chk_base,
                self.dd_base,
                self.sec_base,
                self.chk_relleno,
                self.dd_relleno,
                self.sec_relleno,
                self.chk_cobertura,
                self.dd_cobertura,
                self.sec_cobertura,
                ft.Divider(),
                # Panel de costos integrado
                self.panel_costos,
                ft.Divider(),
            ],
        )

    # =========================================================
    # HELPERS DE CONSTRUCCIÓN
    # =========================================================

    def _construir_tabla(self) -> ft.DataTable:
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Ingrediente", weight="bold")),
                ft.DataColumn(ft.Text("Cantidad", weight="bold")),
                ft.DataColumn(ft.Text("Unidad", weight="bold")),
                ft.DataColumn(ft.Text("")),
            ],
            rows=[],
            column_spacing=20,
            heading_row_color=ft.colors.BLACK12,
        )

    def _construir_seccion(self, origen: str, tabla: ft.DataTable) -> ft.Column:
        return ft.Column(
            visible=False,
            spacing=5,
            controls=[
                ft.Text(
                    self.TITULOS_ORIGEN[origen],
                    weight=ft.FontWeight.W_500,
                    size=12,
                    color=ft.colors.GREY_600,
                ),
                ft.Container(
                    content=tabla,
                    border=ft.border.all(1, "#2D3748"),
                    border_radius=5,
                    padding=5,
                ),
            ],
        )

    # =========================================================
    # EVENTOS
    # =========================================================

    def _evento(self, callback):
        if callback:
            callback()

    def _agregar(self, e):
        if self.on_agregar:
            self.on_agregar()

    def _cambiar_componente(self, callback, valor):
        if callback:
            callback(int(valor) if valor else None)

    def _habilitar_dropdowns(self, e):
        self.dd_base.disabled = not self.chk_base.value
        self.dd_relleno.disabled = not self.chk_relleno.value
        self.dd_cobertura.disabled = not self.chk_cobertura.value

        if not self.chk_base.value and self.dd_base.value:
            self.dd_base.value = None
            self._cambiar_componente(self.on_base_changed, None)

        if not self.chk_relleno.value and self.dd_relleno.value:
            self.dd_relleno.value = None
            self._cambiar_componente(self.on_relleno_changed, None)

        if not self.chk_cobertura.value and self.dd_cobertura.value:
            self.dd_cobertura.value = None
            self._cambiar_componente(self.on_cobertura_changed, None)

        if self.page:
            self.update()

    # =========================================================
    # CARGAS
    # =========================================================

    def cargar_ingredientes(self, ingredientes):
        self.dd_ingrediente.options = [
            ft.dropdown.Option(str(i["id_ingrediente"]), i["nombre_ingrediente"])
            for i in ingredientes
        ]
        if self.page:
            self.update()

    def cargar_bases(self, recetas):
        self.dd_base.options = [
            ft.dropdown.Option(str(r["id_receta"]), r["nombre_receta"])
            for r in recetas
        ]
        if self.page:
            self.update()

    def cargar_rellenos(self, recetas):
        self.dd_relleno.options = [
            ft.dropdown.Option(str(r["id_receta"]), r["nombre_receta"])
            for r in recetas
        ]
        if self.page:
            self.update()

    def cargar_coberturas(self, recetas):
        self.dd_cobertura.options = [
            ft.dropdown.Option(str(r["id_receta"]), r["nombre_receta"])
            for r in recetas
        ]
        if self.page:
            self.update()

    # =========================================================
    # TABLAS DE INGREDIENTES
    # =========================================================

    def mostrar_ingredientes(self, ingredientes):
        grupos = {
            "propio": [],
            "base": [],
            "relleno": [],
            "cobertura": [],
        }

        for ing in ingredientes:
            origen = ing.get("origen", "propio")
            grupos.setdefault(origen, []).append(ing)

        self._llenar_tabla(self.tbl_propios, grupos["propio"])
        self._llenar_tabla(self.tbl_base, grupos["base"])
        self._llenar_tabla(self.tbl_relleno, grupos["relleno"])
        self._llenar_tabla(self.tbl_cobertura, grupos["cobertura"])

        self.sec_base.visible = bool(grupos["base"])
        self.sec_relleno.visible = bool(grupos["relleno"])
        self.sec_cobertura.visible = bool(grupos["cobertura"])

        if self.page:
            self.update()

    def _llenar_tabla(self, tabla: ft.DataTable, ingredientes: list[dict]):
        tabla.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(ing["nombre"])),
                    ft.DataCell(
                        ft.TextField(
                            value=str(ing["cantidad"]),
                            width=90,
                            dense=True,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            on_change=lambda e, uid=ing["uid"]: self._cambiar_cantidad(
                                uid, e.control.value
                            ),
                        )
                    ),
                    ft.DataCell(ft.Text(ing["unidad"])),
                    ft.DataCell(
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=ft.colors.RED_400,
                            tooltip="Quitar ingrediente",
                            on_click=lambda e, uid=ing["uid"]: self._eliminar(uid),
                        )
                    ),
                ]
            )
            for ing in ingredientes
        ]

    def _cambiar_cantidad(self, uid, valor):
        if self.on_editar_cantidad:
            self.on_editar_cantidad(uid, valor)

    def _eliminar(self, uid):
        if self.on_eliminar:
            self.on_eliminar(uid)

    # =========================================================
    # DATOS
    # =========================================================

    def obtener_datos(self):
        return {
            "nombre": self.txt_nombre.value.strip(),
            "tipo": self.dd_tipo.value,
            "ingrediente": self.dd_ingrediente.value,
            "cantidad": self.txt_cantidad.value,
            "unidad": self.dd_unidad.value,
        }

    def cargar(self, receta: dict):
        self.txt_nombre.value = receta.get("nombre_receta", "")
        self.dd_tipo.value = receta.get("tipo_receta", "Base")
        if self.page:
            self.update()

    def limpiar(self):
        self.txt_nombre.value = ""
        self.dd_tipo.value = "Base"
        self.dd_ingrediente.value = None
        self.txt_cantidad.value = ""
        self.dd_unidad.value = "g"
        self.chk_base.value = False
        self.chk_relleno.value = False
        self.chk_cobertura.value = False
        self.dd_base.value = None
        self.dd_relleno.value = None
        self.dd_cobertura.value = None
        self.mostrar_ingredientes([])
        self._habilitar_dropdowns(None)
        # Limpiar también el panel de costos
        self.panel_costos.actualizar(0.0, 0.0)

    def modo_edicion(self, activo=True):
        self.btn_cancelar.visible = activo
        self.btn_guardar.text = "Actualizar" if activo else "Guardar"
        if self.page:
            self.update()

    # =========================================================
    # ACTUALIZAR COSTOS (desde el módulo)
    # =========================================================

    def actualizar_costos(self, subtotal: float, sugerido: float):
        """Actualiza el panel de costos con nuevos valores."""
        self.panel_costos.actualizar(subtotal, sugerido)