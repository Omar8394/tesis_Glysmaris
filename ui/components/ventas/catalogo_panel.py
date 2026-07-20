import flet as ft
from ui.components.buscador import Buscador
from ui.components.selector import Selector
from ui.components.ventas.card_producto import CardProductoVenta
from ui.core.spacing import AppSpacing

class CatalogoPanel(ft.Column):
    def __init__(self, productos, on_agregar):
        super().__init__(expand=True, spacing=AppSpacing.SECTION_SPACING)
        self.productos = productos
        self.on_agregar = on_agregar
        self.productos_filtrados = productos[:]

        # Buscador
        self.buscador = Buscador(
            buscar=self.filtrar,
            placeholder="Buscar producto...",
            width=300
        )

        # Filtros (categoría, clasificación, ocultar agotados)
        self.filtro_categoria = Selector(
            etiqueta="Categoría",
            opciones=self.obtener_categorias(),
            on_change=self.filtrar,
            width=200
        )
        self.filtro_agotados = ft.Checkbox(
            label="Ocultar agotados",
            value=True,
            on_change=self.filtrar
        )

        # Grid de tarjetas estilizado
        self.grid = ft.GridView(
            expand=True,
            max_extent=240,               # Ampliado ligeramente para acomodar botones cómodamente
            spacing=AppSpacing.CONTROL_SPACING,
            run_spacing=AppSpacing.CONTROL_SPACING,
            child_aspect_ratio=1.35,      # Proporción adecuada para evitar truncar textos
        )

        self.controls = [
            ft.Row([self.buscador, self.filtro_categoria, self.filtro_agotados], wrap=True),
            ft.Divider(),
            self.grid
        ]

        self.actualizar_grid()

    def obtener_categorias(self):
        cats = set(p.get('categoria') for p in self.productos if p.get('categoria'))
        return sorted(cats)

    def filtrar(self, e=None):
        texto = self.buscador.obtener().lower()
        categoria = self.filtro_categoria.value
        ocultar_agotados = self.filtro_agotados.value

        self.productos_filtrados = [
            p for p in self.productos
            if (texto in p['nombre'].lower() or texto in p.get('descripcion', '').lower())
            and (not categoria or p.get('categoria') == categoria)
            and (not ocultar_agotados or p.get('stock_actual', 0) > 0)
        ]
        self.actualizar_grid()

    def actualizar_grid(self):
        self.grid.controls.clear()
        for p in self.productos_filtrados:
            tarjeta = CardProductoVenta(
                producto=p,
                on_agregar=self.on_agregar
            )
            self.grid.controls.append(tarjeta)
        if self.page:
            self.update()  