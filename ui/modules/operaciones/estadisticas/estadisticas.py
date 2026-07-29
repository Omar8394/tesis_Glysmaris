"""
============================================================
Sistema La Dulce Tía

Archivo:
    estadisticas.py

Responsabilidad:
    Punto de entrada del módulo de Estadísticas para el
    DashboardModule. Sigue el mismo contrato que el resto de
    módulos (ingredientes_view, productos_view, ventas_view, etc.):
    recibe (page, content_area) y devuelve (layout, module).

Nota de arquitectura:
    EstadisticasView ya obtiene y arma todos sus datos (vía
    EstadisticasService/ServiceFactory) dentro de su propio
    __init__ -- no expone un método cargar() adicional, a
    diferencia de otros módulos. Por eso este wrapper no define
    cargar(): DashboardModule ya verifica con
    hasattr(module, 'cargar') antes de invocarlo, así que
    simplemente no lo llama para este módulo.
============================================================
"""

from __future__ import annotations

import flet as ft

from ui.modules.operaciones.estadisticas.estadisticas_view import EstadisticasView


def estadisticas_view(page: ft.Page, content_area: ft.Container):
    """
    Crea la vista de Estadísticas.

    page / content_area se reciben solo para respetar la firma
    común de *_view(); EstadisticasView no los necesita porque
    obtiene sus datos directamente del ServiceFactory.
    """
    module = EstadisticasView()
    layout = module
    return layout, module