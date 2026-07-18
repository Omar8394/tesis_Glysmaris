# ui/modules/operaciones/recetas/recetas_view.py (o recetas.py)
"""
Vista principal de recetas.
Solo instancia el módulo.
"""

from __future__ import annotations
from ui.modules.operaciones.recetas.recetas_module import RecetasModule


def recetas_view(page, content_area):
    module = RecetasModule(page, content_area)
    layout = module.construir()
    return layout, module