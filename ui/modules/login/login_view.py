"""
============================================================
Sistema La Dulce Tía

Archivo:
    login_view.py

Responsabilidad:
    Punto de entrada para el módulo de login.

    Solo instancia el módulo y devuelve su vista.
============================================================
"""

from ui.modules.login.login_module import LoginModule


def login_view(page, auth_service, on_login_success):
    """
    Crea y devuelve la vista del módulo de login.
    """
    module = LoginModule(page, auth_service, on_login_success)
    return module.construir()