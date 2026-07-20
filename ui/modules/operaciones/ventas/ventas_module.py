from ui.modules.base.module import Module
from ui.modules.operaciones.ventas.ventas import VentasView
from ui.core.services.factory import ServiceFactory

class VentasModule(Module):
    def __init__(self, page, usuario=None):
        super().__init__(page, usuario)
        self.producto_service = ServiceFactory.get_producto_service()
        self.activo_service = ServiceFactory.get_activo_service()
        self.cliente_service = ServiceFactory.get_cliente_service()  # por definir
        self.carrito = []  # lista de dicts: {producto, cantidad, agregados, ...}
        self.view = None

    def construir(self):
        self.view = VentasView(
            on_agregar_producto=self.agregar_producto,
            on_cambiar_cantidad=self.cambiar_cantidad,
            on_eliminar_producto=self.eliminar_producto,
            on_abrir_agregados=self.abrir_agregados,
            on_continuar_cobro=self.continuar_cobro,
            on_finalizar_venta=self.finalizar_venta,
            productos_disponibles=self.cargar_productos(),
            activos_disponibles=self.cargar_activos(),
        )
        return self.view

    def cargar_productos(self):
        # Obtener productos con stock disponible para venta
        resultado = self.producto_service.listar_disponibles()  # método hipotético
        return resultado.datos if resultado.exito else []

    def cargar_activos(self):
        # Activos que pueden usarse como agregados (velas, toppers, empaques...)
        resultado = self.activo_service.listar_agregados()  # método hipotético
        return resultado.datos if resultado.exito else []

    def agregar_producto(self, producto):
        # Buscar si ya existe en el carrito
        for item in self.carrito:
            if item['producto']['id_producto'] == producto['id_producto']:
                item['cantidad'] += 1
                self.view.actualizar_carrito(self.carrito)
                return
        # Nuevo ítem
        self.carrito.append({
            'producto': producto,
            'cantidad': 1,
            'agregados': [],
            'personalizado': False
        })
        self.view.actualizar_carrito(self.carrito)

    def cambiar_cantidad(self, index, nueva_cantidad):
        if nueva_cantidad <= 0:
            self.eliminar_producto(index)
        else:
            self.carrito[index]['cantidad'] = nueva_cantidad
            self.view.actualizar_carrito(self.carrito)

    def eliminar_producto(self, index):
        del self.carrito[index]
        self.view.actualizar_carrito(self.carrito)

    def abrir_agregados(self, index):
        # Abre la sección de agregados para el producto en el índice
        self.view.mostrar_panel_agregados(index, self.carrito[index])

    def continuar_cobro(self):
        # Cambia el panel derecho al modo de pago
        total = self.calcular_total()
        self.view.mostrar_panel_pago(total)

    def finalizar_venta(self, datos_pago):
        # Aquí se llama al servicio de ventas para guardar
        pass

    def calcular_total(self):
        total = 0
        for item in self.carrito:
            precio = item['producto']['precio_venta']
            total += precio * item['cantidad']
            # Sumar agregados
            for agg in item['agregados']:
                total += agg['costo'] * agg['cantidad']
        return total