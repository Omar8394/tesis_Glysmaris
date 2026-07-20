"""
============================================================
Sistema La Dulce Tía

Archivo:
    orden_card.py

Responsabilidad:
    Tarjeta que representa una orden de producción en el tablero.
    Muestra información resumida y botones de acción según el estado.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from datetime import datetime

import flet as ft

from ui.core.theme_manager import ThemeManager
from ui.core.typography import AppTypography
from ui.core.spacing import AppSpacing
from ui.core.icons import AppIcons
from ui.components.boton import BotonPrimario, BotonSecundario, BotonPeligro


class OrdenCard(ft.Card):
    """
    Tarjeta de una orden de producción.
    """

    def __init__(
        self,
        orden: dict,
        on_iniciar: callable = None,
        on_continuar: callable = None,
        on_finalizar: callable = None,
        on_ver_detalle: callable = None,
        on_cancelar: callable = None,
    ):
        self.tema = ThemeManager.theme
        self.orden = orden
        self.on_iniciar = on_iniciar
        self.on_continuar = on_continuar
        self.on_finalizar = on_finalizar
        self.on_ver_detalle = on_ver_detalle
        self.on_cancelar = on_cancelar

        # Construir contenido
        contenido = self._crear_contenido()
        super().__init__(
            content=ft.Container(
                content=contenido,
                padding=AppSpacing.MD,
                width=280,
            ),
            elevation=2,
            margin=5,
        )

    def _crear_contenido(self) -> ft.Column:
        """Construye el contenido de la tarjeta."""
        orden = self.orden
        estado = orden.get("estado", "pendiente")
        prioridad = orden.get("prioridad", "media")
        
        # Color según prioridad
        colores_prioridad = {
            "baja": ft.colors.BLUE,
            "media": ft.colors.GREEN,
            "alta": ft.colors.ORANGE,
            "urgente": ft.colors.RED,
        }
        color_prioridad = colores_prioridad.get(prioridad, ft.colors.GREY)

        # Icono según estado
        iconos_estado = {
            "pendiente": ft.icons.HOURGLASS_TOP,
            "en_proceso": ft.icons.PLAY_CIRCLE,
            "finalizada": ft.icons.CHECK_CIRCLE,
            "cancelada": ft.icons.CANCEL,
        }
        icono_estado = iconos_estado.get(estado, ft.icons.HELP)

        # Fecha
        fecha = orden.get("fecha_planificada", "")
        if fecha:
            fecha_str = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else str(fecha)
        else:
            fecha_str = "Sin fecha"

        # Responsable
        responsable = orden.get("responsable") or "No asignado"

        # Cantidad total (suma de cantidades planificadas)
        total_cantidad = self._calcular_total_cantidad()

        # Construir layout
        columna = ft.Column(
            [
                # Cabecera: número, prioridad, estado
                ft.Row(
                    [
                        ft.Text(
                            orden.get("numero_orden", "N/A"),
                            size=AppTypography.BODY,
                            weight="bold",
                        ),
                        ft.Container(expand=True),
                        ft.Icon(icono_estado, size=16, color=color_prioridad),
                        ft.Text(estado.capitalize(), size=12, color=color_prioridad),
                    ],
                    spacing=4,
                ),
                ft.Divider(height=2),
                # Cuerpo: cantidad, fecha, responsable
                ft.Row(
                    [
                        ft.Icon(ft.icons.PRODUCTION_QUANTITY_LIMITS, size=16, color=ft.colors.GREY),
                        ft.Text(f"{total_cantidad} unidades", size=14),
                    ],
                    spacing=4,
                ),
                ft.Row(
                    [
                        ft.Icon(ft.icons.CALENDAR_TODAY, size=16, color=ft.colors.GREY),
                        ft.Text(fecha_str, size=14),
                    ],
                    spacing=4,
                ),
                ft.Row(
                    [
                        ft.Icon(ft.icons.PERSON, size=16, color=ft.colors.GREY),
                        ft.Text(responsable, size=14),
                    ],
                    spacing=4,
                ),
                # Progreso: proxy honesto en base al tiempo transcurrido
                # desde fecha_inicio contra tiempo_estimado_minutos de la
                # orden. No es un avance físico reportado (eso requeriría
                # que alguien lo cargue a mano), pero es un dato real
                # derivado de columnas que sí existen -- no un valor
                # inventado. Si falta fecha_inicio o tiempo_estimado, no
                # se muestra nada en vez de mostrar un número falso.
                self._crear_barra_progreso() if estado == "en_proceso" and self._calcular_progreso() is not None else ft.Container(),
                # Botones de acción según estado
                self._crear_botones_accion(),
            ],
            spacing=AppSpacing.CONTROL_SPACING,
            tight=True,
        )

        return columna

    def _calcular_total_cantidad(self) -> int:
        """Suma las cantidades planificadas de todos los productos de la orden."""
        # Esta información debería venir en el dict de la orden, o se obtiene del service.
        # Por ahora, si viene en los datos, la usamos; si no, 0.
        return self.orden.get("total_cantidad", 0)

    def _calcular_progreso(self) -> int | None:
        """
        Progreso estimado = tiempo transcurrido desde fecha_inicio /
        tiempo_estimado_minutos de la orden, acotado a 0-100. Devuelve
        None si falta alguno de los dos datos (orden vieja sin
        fecha_inicio registrada, o sin tiempo estimado) -- en ese caso
        no se muestra la barra, no se inventa un número.
        """
        fecha_inicio = self.orden.get("fecha_inicio")
        tiempo_estimado = self.orden.get("tiempo_estimado_minutos")

        if not fecha_inicio or not tiempo_estimado:
            return None

        try:
            tiempo_estimado = float(tiempo_estimado)
            if tiempo_estimado <= 0:
                return None
            transcurrido_minutos = (datetime.now() - fecha_inicio).total_seconds() / 60
            return int(min(100, max(0, (transcurrido_minutos / tiempo_estimado) * 100)))
        except (TypeError, ValueError):
            return None

    def _crear_barra_progreso(self) -> ft.Container:
        """Barra de progreso estimado para órdenes en proceso."""
        progreso = self._calcular_progreso() or 0
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(f"{progreso}% (estimado)", size=12, color=ft.colors.GREY),
                    ft.Container(
                        width=150,
                        height=6,
                        bgcolor=ft.colors.GREY_300,
                        border_radius=3,
                        content=ft.Container(
                            width=progreso / 100 * 150,
                            height=6,
                            bgcolor=self.tema.primary,
                            border_radius=3,
                        ),
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.only(top=4),
        )

    def _crear_botones_accion(self) -> ft.Container:
        """Genera los botones según el estado de la orden."""
        estado = self.orden.get("estado", "pendiente")
        botones = []

        if estado == "pendiente":
            # Pendiente: Iniciar, Ver detalle, Cancelar
            if self.on_iniciar:
                botones.append(
                    BotonPrimario(
                        texto="Iniciar",
                        icono=AppIcons.PLAY,
                        on_click=lambda e: self._ejecutar_callback(self.on_iniciar),
                        expand=True,
                        width=None,
                    )
                )
            if self.on_ver_detalle:
                botones.append(
                    BotonSecundario(
                        texto="Detalle",
                        icono=AppIcons.EYE,
                        on_click=lambda e: self._ejecutar_callback(self.on_ver_detalle),
                        expand=True,
                        width=None,
                    )
                )
            if self.on_cancelar:
                botones.append(
                    BotonPeligro(
                        texto="Cancelar",
                        icono=AppIcons.CANCEL,
                        on_click=lambda e: self._ejecutar_callback(self.on_cancelar),
                        expand=True,
                        width=None,
                    )
                )

        elif estado == "en_proceso":
            # En proceso: Continuar, Finalizar, Ver detalle
            if self.on_continuar:
                botones.append(
                    BotonPrimario(
                        texto="Continuar",
                        icono=AppIcons.PLAY,
                        on_click=lambda e: self._ejecutar_callback(self.on_continuar),
                        expand=True,
                        width=None,
                    )
                )
            if self.on_finalizar:
                botones.append(
                    BotonPrimario(
                        texto="Finalizar",
                        icono=AppIcons.CHECK,
                        on_click=lambda e: self._ejecutar_callback(self.on_finalizar),
                        expand=True,
                        width=None,
                    )
                )
            if self.on_ver_detalle:
                botones.append(
                    BotonSecundario(
                        texto="Detalle",
                        icono=AppIcons.EYE,
                        on_click=lambda e: self._ejecutar_callback(self.on_ver_detalle),
                        expand=True,
                        width=None,
                    )
                )

        elif estado == "finalizada":
            # Finalizada: Ver detalle (solo detalle)
            if self.on_ver_detalle:
                botones.append(
                    BotonSecundario(
                        texto="Ver Detalles",
                        icono=AppIcons.EYE,
                        on_click=lambda e: self._ejecutar_callback(self.on_ver_detalle),
                        expand=True,
                        width=None,
                    )
                )

        # Si no hay botones, mostramos un texto de estado
        if not botones:
            return ft.Container(
                content=ft.Text("Sin acciones disponibles", size=12, color=ft.colors.GREY),
                padding=ft.padding.only(top=8),
            )

        # Distribuir botones en filas (máximo 2 por fila)
        filas = []
        for i in range(0, len(botones), 2):
            fila = ft.Row(
                botones[i:i+2],
                spacing=AppSpacing.SM,
                alignment=ft.MainAxisAlignment.CENTER,
            )
            filas.append(fila)

        return ft.Container(
            content=ft.Column(filas, spacing=4),
            padding=ft.padding.only(top=8),
        )

    def _ejecutar_callback(self, callback):
        """Ejecuta el callback pasando el id de la orden."""
        if callback:
            callback(self.orden.get("id_orden"))