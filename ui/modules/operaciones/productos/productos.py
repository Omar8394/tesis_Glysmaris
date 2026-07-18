from ui.modules.operaciones.productos.producto_module import ProductoModule
from ui.core.services.factory import ServiceFactory


def productos_view(page, content_area):
    module = ProductoModule(
        page,
        content_area,
        producto_service=ServiceFactory.get_producto_service(),
        recetas_service=ServiceFactory.get_recetas_service(),
        activo_service=ServiceFactory.get_activo_service(),
        ingrediente_service=ServiceFactory.get_ingrediente_service(),
    )
    return module.construir(), module