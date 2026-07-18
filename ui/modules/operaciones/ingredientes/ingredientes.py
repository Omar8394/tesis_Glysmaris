"""
Vista principal de ingredientes.
Solo instancia el módulo.
"""

# ui/modules/operaciones/ingredientes/ingredientes_view.py

# ui/modules/operaciones/ingredientes/ingredientes_view.py

# ui/modules/operaciones/ingredientes/ingredientes_view.py
# ui/modules/operaciones/ingredientes/ingredientes_view.py

# ui/modules/operaciones/ingredientes/ingredientes_view.py

from __future__ import annotations
from ui.modules.operaciones.ingredientes.ingrediente_module import IngredienteModule


def ingredientes_view(page, content_area):
    module = IngredienteModule(page, content_area)
    layout = module.construir()
    return layout, module