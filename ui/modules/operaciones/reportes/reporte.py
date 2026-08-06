from __future__ import annotations
from ui.modules.operaciones.reportes.reporte_module import ReporteModule

def reporte_view(page, content_area):
    module = ReporteModule(page, content_area)
    layout = module.construir()
    return layout, module