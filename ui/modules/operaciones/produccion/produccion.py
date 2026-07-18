"""
Vista principal de producción.
Solo instancia el módulo.
"""

from __future__ import annotations

from ui.modules.operaciones.produccion.produccion_module import ProduccionModule


def produccion_view(page, content_area):
    module = ProduccionModule(page, content_area)
    layout = module.construir()
    return layout, module