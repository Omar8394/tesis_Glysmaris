"""
Vista principal de recursos del negocio.
Solo instancia el módulo.
"""

from __future__ import annotations

from ui.modules.operaciones.activos.activos_module import ActivoModule


def activos_view(page, content_area):
    """
    Crea y retorna la vista del módulo de recursos.
    """
    module = ActivoModule(page, content_area)
    layout = module.construir()
    return layout, module