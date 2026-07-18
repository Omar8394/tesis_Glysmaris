"""
============================================================
Sistema La Dulce Tía

Archivo:
    dashboard_view.py

Responsabilidad:
    Punto de entrada para el dashboard.

    Solo instancia el módulo y devuelve su vista.
============================================================
"""

from ui.modules.dashboard.dashboard_module import DashboardModule


def dashboard_view(page, content_area, usuario_actual):
    """
    Crea y devuelve la vista del dashboard.
    """
    module = DashboardModule (page, content_area, usuario_actual)
    
    return module.construir()
    