"""
Punto de entrada para el módulo de Cuentas por Cobrar y Clientes.
Similar a ingredientes.py.
"""
from __future__ import annotations

from ui.modules.operaciones.cuentas_por_cobrar.cuentas_por_cobrar_module import CuentasPorCobrarModule


def cuentas_por_cobrar_view(page, content_area):
    module = CuentasPorCobrarModule(page, usuario=getattr(page, "usuario_actual", None))
    layout = module.construir()
    return layout, module