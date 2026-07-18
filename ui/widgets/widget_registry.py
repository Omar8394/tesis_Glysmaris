class WidgetRegistry:
    def __init__(self):
        self._widgets = {}
        self._orden = []
        # Añadimos atributos necesarios para los nuevos métodos
        self._rol = None          # Debes establecerlo según tu lógica
        self._permisos = {}       # Ejemplo: {"widget1": ["ver", "editar"]}

    def registrar(
        self,
        nombre,
        widget,
        visible=True,
        orden=None,
    ):
        self._widgets[nombre] = {
            "widget": widget,
            "visible": visible,
            "orden": orden if orden is not None else len(self._widgets),
            "habilitado": True,   # Por defecto habilitado
            "minimizado": False,  # Por defecto no minimizado
            "nombre": nombre,     # Para usarlo en obtener_controles
        }

    def obtener(
        self,
        nombre: str,
    ):
        """Devuelve la información de un widget registrado."""
        return self._widgets.get(nombre)

    def obtener_widget(
        self,
        nombre: str,
    ):
        """Devuelve únicamente la instancia del widget."""
        info = self.obtener(nombre)
        if info is None:
            return None
        return info["widget"]

    def existe(
        self,
        nombre: str,
    ) -> bool:
        return nombre in self._widgets

    # ============================================================
    # VISIBILIDAD
    # ============================================================

    def mostrar(
        self,
        nombre: str,
    ):
        if self.existe(nombre):
            self._widgets[nombre]["visible"] = True

    def ocultar(
        self,
        nombre: str,
    ):
        if self.existe(nombre):
            self._widgets[nombre]["visible"] = False

    def habilitar(
        self,
        nombre: str,
    ):
        if self.existe(nombre):
            self._widgets[nombre]["habilitado"] = True

    def deshabilitar(
        self,
        nombre: str,
    ):
        if self.existe(nombre):
            self._widgets[nombre]["habilitado"] = False

    def minimizar(
        self,
        nombre: str,
    ):
        if self.existe(nombre):
            self._widgets[nombre]["minimizado"] = True

    def restaurar(
        self,
        nombre: str,
    ):
        if self.existe(nombre):
            self._widgets[nombre]["minimizado"] = False

    # ============================================================
    # ORDEN
    # ============================================================

    def cambiar_orden(
        self,
        nombre: str,
        orden: int,
    ):
        if self.existe(nombre):
            self._widgets[nombre]["orden"] = orden

    def widgets_ordenados(self):
        return sorted(
            self._widgets.values(),
            key=lambda item: item["orden"],
        )

    # ============================================================
    # RESPONSIVE
    # ============================================================

    def on_resize(
        self,
        responsive_info,
    ):
        for info in self._widgets.values():
            widget = info["widget"]
            widget.on_resize(responsive_info)

    # ============================================================
    # CONTROLES
    # ============================================================

    def tiene_permiso(self, nombre_widget, rol):
        """
        Método auxiliar para verificar permisos.
        Debes implementarlo según tu lógica.
        """
        # Ejemplo: si no hay roles o permisos definidos, devuelve True
        if not self._permisos:
            return True
        # Lógica personalizada aquí...
        return True

    def obtener_controles(self):
        controles = []
        for info in self.widgets_ordenados():
            # Verificar habilitado
            if not info.get("habilitado", True):
                continue
            # Verificar visible
            if not info.get("visible", True):
                continue
            # Verificar minimizado
            if info.get("minimizado", False):
                continue
            # Verificar permisos (necesitas definir self._rol y self.tiene_permiso)
            if not self.tiene_permiso(info["nombre"], self._rol):
                continue

            # Agregar el control
            controles.append(info["widget"].crear())

        return controles

    def actualizar(self):
        for info in self._widgets.values():
            info["widget"].actualizar()

    def actualizar_tema(self):
        for info in self._widgets.values():
            info["widget"].actualizar_tema()

    def limpiar(self):
        self._widgets.clear()
    # ============================================================
    # PREFERENCIAS DEL USUARIO
    # ============================================================

    def guardar_preferencias(self):
        """
        Genera un diccionario con la configuración actual
        de los widgets para ser almacenado en la base de datos
        o en un archivo de configuración.
        """

        preferencias = {}

        for nombre, info in self._widgets.items():

            preferencias[nombre] = {

                "visible": info["visible"],

                "orden": info["orden"],

                "minimizado": info["minimizado"],

            }

        return preferencias

    def cargar_preferencias(
        self,
        preferencias: dict,
    ):
        """
        Aplica las preferencias guardadas por el usuario.
        """

        if not preferencias:
            return

        for nombre, config in preferencias.items():

            if not self.existe(nombre):
                continue

            info = self._widgets[nombre]

            info["visible"] = config.get(
                "visible",
                info["visible"],
            )

            info["orden"] = config.get(
                "orden",
                info["orden"],
            )

            info["minimizado"] = config.get(
                "minimizado",
                info["minimizado"],
            )

    # ============================================================
    # ACTUALIZACIÓN
    # ============================================================

    def actualizar(self):
        """
        Actualiza todos los widgets registrados.
        """

        for info in self._widgets.values():

            widget = info["widget"]

            widget.actualizar()

    def actualizar_tema(self):
        """
        Notifica a todos los widgets que el tema cambió.
        """

        for info in self._widgets.values():

            widget = info["widget"]

            widget.actualizar_tema()

    # ============================================================
    # ELIMINAR
    # ============================================================

    def eliminar(
        self,
        nombre: str,
    ):

        if self.existe(nombre):

            del self._widgets[nombre]

    # ============================================================
    # LIMPIAR
    # ============================================================

    def limpiar(self):
        """
        Elimina todos los widgets registrados.
        """

        self._widgets.clear()

    # ============================================================
    # MÉTODOS ESPECIALES
    # ============================================================

    def __len__(self):

        return len(self._widgets)

    def __iter__(self):

        return iter(self._widgets.values())

    def __contains__(
        self,
        nombre,
    ):

        return nombre in self._widgets

    def __repr__(self):

        return (

            f"<WidgetRegistry widgets={len(self)}>"

        )




# ============================================================
# INSTANCIA GLOBAL
# ============================================================
widget_registry = WidgetRegistry()