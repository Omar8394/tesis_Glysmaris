import flet as ft
from ui.components.autocompletado import AutoCompletado
from ui.components.campo_texto import CampoTexto
from ui.components.boton import BotonSecundario
from ui.components.productos.tabla_seleccion import TablaSeleccion
from ui.core.spacing import AppSpacing

class PanelAgregados(ft.Container):
    def __init__(self, index, agregados, activos_disponibles, on_agregar_agregado, on_quitar_agregado):
        self.index = index
        self.agregados = agregados
        self.activos_disponibles = activos_disponibles
        self.on_agregar_agregado = on_agregar_agregado
        self.on_quitar_agregado = on_quitar_agregado

        # Autocompletado para buscar activos
        self.buscador_activo = AutoCompletado(
            etiqueta="Agregado (activo)",
            buscar=self._buscar_activos,
            width=250
        )
        self.cantidad_activo = CampoTexto(
            etiqueta="Cantidad",
            value="1",
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        self.btn_agregar = BotonSecundario(
            texto="Agregar",
            icono=ft.icons.ADD,
            on_click=self._agregar,
            width=80
        )

        # Tabla de agregados ya añadidos
        self.tabla = TablaSeleccion(
            columnas=[("nombre", "Nombre"), ("cantidad", "Cantidad"), ("costo", "Costo")],
            on_eliminar=self._quitar
        )
        self.tabla.reemplazar(self.agregados)

        super().__init__(padding=AppSpacing.MD, bgcolor="gray50", border_radius=5)
        self.content = ft.Column([
            ft.Row([self.buscador_activo, self.cantidad_activo, self.btn_agregar], spacing=AppSpacing.SM),
            self.tabla
        ], spacing=AppSpacing.SM)

    def _buscar_activos(self, texto):
        # Filtrar activos disponibles (tipo adecuado)
        return [a for a in self.activos_disponibles if texto.lower() in a['nombre'].lower()]

    def _agregar(self, e):
        nombre = self.buscador_activo.obtener()
        if not nombre:
            return
        # Buscar el activo completo
        activo = next((a for a in self.activos_disponibles if a['nombre'] == nombre), None)
        if not activo:
            return
        cantidad = int(self.cantidad_activo.value or 1)
        # Crear el agregado
        agregado = {
            'id_activo': activo['id_activo'],
            'nombre': activo['nombre'],
            'cantidad': cantidad,
            'costo': activo['costo_unitario'] * cantidad
        }
        self.on_agregar_agregado(agregado)
        self.buscador_activo.limpiar()
        self.cantidad_activo.value = "1"
        self.update()

    def _quitar(self, idx):
        self.on_quitar_agregado(idx)