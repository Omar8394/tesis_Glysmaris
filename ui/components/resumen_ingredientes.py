# ui/components/resumen_ingredientes.py

from __future__ import annotations
import flet as ft
from ui.components.tarjetas import TarjetaResumen
from ui.core.icons import AppIcons


class ResumenIngredientes(ft.Row):
    """
    Muestra tarjetas de resumen para el módulo de ingredientes.
    """

    def __init__(self):
        super().__init__()
        self.spacing = 10
        self.wrap = True

        # Inicializamos con valores por defecto (0)

        self.total_tarjeta = TarjetaResumen(titulo="Total Ingredientes", valor=0, icono=AppIcons.INGREDIENT, width= 170)
        self.stock_tarjeta = TarjetaResumen(titulo="Stock Bajo ⚠️", valor=0, icono=AppIcons.WARNING, color="warning", width= 170)
        self.caducar_tarjeta = TarjetaResumen(titulo="Por Caducar 🕒", valor=0, icono=AppIcons.CALENDAR, color="error", width= 170)
        self.categorias_tarjeta = TarjetaResumen(titulo="Categorías", valor=0, icono=AppIcons.CATEGORY, color="info", width= 170)
        # ✅ Nueva tarjeta: perecederos/refrigerados próximos a vencer (vida útil
        # más corta => riesgo de pérdida si no se avisa a tiempo).
        self.fragiles_tarjeta = TarjetaResumen(titulo="Frágiles por Vencer ❄️", valor=0, icono=AppIcons.WARNING, color="error", width= 170)
        self.controls = [
            self.total_tarjeta,
            self.stock_tarjeta,
            self.caducar_tarjeta,
            self.categorias_tarjeta,
            self.fragiles_tarjeta,
        ]

    def actualizar(self, total: int, stock_bajo: int, por_caducar: int, categorias: int, fragiles_por_vencer: int = 0):
        """
        Actualiza los valores de las tarjetas.
        """
        self.total_tarjeta.content.controls[1].controls[0].value = str(total)
        self.stock_tarjeta.content.controls[1].controls[0].value = str(stock_bajo)
        self.caducar_tarjeta.content.controls[1].controls[0].value = str(por_caducar)
        self.categorias_tarjeta.content.controls[1].controls[0].value = str(categorias)
        self.fragiles_tarjeta.content.controls[1].controls[0].value = str(fragiles_por_vencer)
        self.update()