"""
============================================================
Sistema La Dulce Tía

Archivo:
    mi_negocio.py

Responsabilidad:
    Punto de entrada del módulo "Mi Negocio", con la misma forma que
    el resto de los *_view() que ya usa DashboardModule
    (ingredientes_view, recetas_view, productos_view, activos_view,
    produccion_view): arma el service real vía ServiceFactory y
    devuelve (layout, module) listo para colgar en content_area.

    MiNegocioView (en mi_negocio_view.py) ya carga sus datos solo en
    __init__ (ParametrosNegocioService.obtener() es una lectura
    síncrona, no requiere que el control ya esté montado en la
    página), así que acá no hace falta un módulo "controlador"
    separado: la vista misma se devuelve como layout y como module.

⚠️ Ajustar:
    Este archivo asume que ServiceFactory expone
    `get_parametros_negocio_service()`, análogo a
    `get_auth_service()` (ver dashboard_module.py, _logout). Si el
    getter real tiene otro nombre, corregirlo acá abajo.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Callable

from ui.core.services.factory import ServiceFactory
from ui.modules.operaciones.activos.mi_negocio_view import MiNegocioView


def mi_negocio_view(
        page,
        content_area,
        on_ir_a_activos: Callable[[], None] | None = None,
    ):
        parametros_service = ServiceFactory.get_parametros_negocio_service()

        module = MiNegocioView(
            page=page,
            content_area=content_area,
            parametros_service=parametros_service,
            on_ir_a_activos=on_ir_a_activos,
        )

        # module.crear() ejecuta el ciclo de vida de Module: construye el
        # esqueleto (construir()) e inicializa (on_init()). Los datos NO
        # se cargan acá todavía — eso lo hace dashboard_module.py llamando
        # a module.cargar() después de agregar layout a content_area,
        # mismo patrón que usa _ir_recursos con activos_view.
        layout = module.crear()

        return layout, module