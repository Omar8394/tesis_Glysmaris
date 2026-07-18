# ui/layouts/tabla_con_resumen_layout.py

from __future__ import annotations
import flet as ft
from ui.core.spacing import AppSpacing


class TablaConResumenLayout(ft.Container):
    """
    Layout reutilizable para módulos que muestran:
    - Resumen (opcional) con tarjetas
    - Toolbar (Renderizado en capa superior para flotar sobre la tabla)
    - Tabla
    - Paginador
    - Overlay (opcional, se superpone)
    """

    def __init__(
        self,
        resumen: ft.Control | None = None,
        toolbar: ft.Control | None = None,
        tabla: ft.Control | None = None,
        paginador: ft.Control | None = None,
        overlay: ft.Control | None = None,
        padding=AppSpacing.LG,
        expand=True,
    ):
        super().__init__()
        self.expand = expand
        self.padding = padding

        # 1. Controles inferiores (La tabla y su paginador)
        controles_inferiores = []
        if tabla:
            controles_inferiores.append(tabla)
        if paginador:
            controles_inferiores.append(paginador)

        # Creamos una columna para la tabla, pero reservamos un espacio vacío 
        # arriba equivalente a la altura del Toolbar para que no se encimen.
        columna_tabla = ft.Column(
            controls=[
                ft.Container(height=65), # 💡 Espacio en blanco reservado para el Toolbar
                *controles_inferiores
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            expand=True,
        )

        # 2. Forzamos el orden de pintura (Layering) mediante un Stack.
        # Colocamos la tabla PRIMERO (capa de fondo) y el toolbar SEGUNDO (capa del frente).
        # Esto garantiza que el overflow del AutoCompletado flote legítimamente sobre la tabla.
        bloque_interactivo = ft.Stack(
            controls=[
                columna_tabla, # Se pinta abajo
                ft.Container(content=toolbar, top=0, left=0, right=0, height=65) if toolbar else ft.Container() # Se pinta arriba
            ],
            expand=True,
            clip_behavior=ft.ClipBehavior.NONE, # 💡 Evita que se corten las sugerencias
        )

        # 3. Construimos la estructura principal uniendo el resumen y el bloque interactivo
        controles_principales = []
        if resumen:
            controles_principales.append(resumen)
        controles_principales.append(bloque_interactivo)

        contenido_principal = ft.Column(
            controls=controles_principales,
            spacing=AppSpacing.CONTROL_SPACING,
            expand=True,
            scroll= None,
            tight=True,
        )

        if overlay:
            self.content = ft.Stack(
                [
                    ft.Container(
                        content=contenido_principal,
                        expand=True,
                        padding=0,
                    ),
                    overlay,
                ],
                expand=True,
            )
        else:
            self.content = ft.Container(
                content=contenido_principal,
                expand=True,
                padding=0,
            )