"""
Vista principal de usuarios.
Solo instancia el módulo.
"""

from __future__ import annotations
from ui.modules.seguridad.usuario_module import UsuarioModule


def usuarios_view(page, content_area):
    module = UsuarioModule(page, content_area)
    layout = module.construir()
    return layout, module