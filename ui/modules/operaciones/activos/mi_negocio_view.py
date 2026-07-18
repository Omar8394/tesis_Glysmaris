"""
============================================================
Sistema La Dulce Tía

Archivo:
    mi_negocio_view.py

Responsabilidad:
    Pantalla de configuración de negocio ("Mi Negocio" / "Costos
    Fijos"). Acá el usuario carga lo que NO cambia todos los días:

        - Cuánto vale su hora de trabajo (mano de obra).
        - Cuántas horas trabaja al mes (para prorratear todo lo demás).

    Y ve, calculado automáticamente a partir de lo que ya cargó en
    ACTIVOS (servicios y herramientas), el desglose de:

        - Tasa de servicios por hora (facturas mensuales / horas mes).
        - Tasa de depreciación por hora (activos con vida útil).
        - Costo total por hora (mano de obra + ambas tasas).

    Ese costo total por hora es justo lo que ProductoService usa
    después, multiplicado por tiempo_preparacion_minutos, para
    calcular mano de obra y costos indirectos de cada producto — el
    usuario ya no tiene que volver a cargar nada de esto al crear un
    producto.

    ⚠️ No gestiona altas/bajas de ACTIVOS individuales (servicios,
    herramientas). Eso vive en la pantalla de Activos; acá solo se
    lee el total ya cargado, vía ParametrosNegocioService.

    Sigue el mismo patrón que el resto de los módulos del sistema
    (ver ActivoModule): hereda de Module, construye su vista en
    construir() y expone cargar() para refrescar los datos cuando el
    módulo se vuelve a mostrar.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from ui.modules.base.module import Module
from ui.components.campo_texto import CampoTexto
from ui.components.boton import BotonPrimario
from ui.components.tarjetas import TarjetaFormulario
from ui.components.mensajes import MensajeSistema
from ui.core.spacing import AppSpacing
from ui.core.typography import AppTypography
from ui.core.icons import AppIcons


class MiNegocioView(Module):
    """
    Pantalla de configuración de tasas del negocio.
    """

    def __init__(
        self,
        page: ft.Page,
        content_area: ft.Control,
        parametros_service,
        on_ir_a_activos: Callable[[], None] | None = None,
    ):
        super().__init__(page)  # Module espera solo page (+ usuario opcional)
        self.content_area = content_area
        self._service = parametros_service
        self.on_ir_a_activos = on_ir_a_activos

        # En lugar de crear el contenedor aquí, lo construiremos en _cargar_y_renderizar
        self.contenedor = None
        self.layout_principal = None

    # ------------------------------------------------------------
    #  Construcción e inicialización (mismo patrón que ProductoModule)
    # ------------------------------------------------------------

    def construir(self) -> ft.Control:
        """
        Devuelve el esqueleto del módulo. Los datos se cargan recién
        en cargar(), que debe invocarse después de que este control ya
        esté agregado a la página.
        """
        # Estructura similar a ProductoModule: un Stack con un Container expandido
        # y un Column para el contenido.
        if self.layout_principal is None:
            self.contenedor = ft.Column(
                spacing=AppSpacing.SECTION_SPACING,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )

            contenido_principal = ft.Container(
                content=self.contenedor,
                expand=True,
                padding=AppSpacing.LG,
            )

            self.layout_principal = ft.Stack(
                expand=True,
                controls=[contenido_principal],
            )

            # Carga inicial (se ejecutará una vez que el control esté en la página)
            self.cargar()

        return self.layout_principal

    def on_show(self):
        """Se ejecuta cuando el módulo se hace visible."""
        self.cargar()

    def cargar(self):
        """Recarga los datos desde el servicio y re-renderiza."""
        self._cargar_y_renderizar()

    # ------------------------------------------------------------
    #  Carga / render
    # ------------------------------------------------------------

    def _cargar_y_renderizar(self):
        resultado = self._service.obtener()
        datos = resultado.datos if resultado.exito else {}

        self.txt_costo_hora = CampoTexto(
            etiqueta="Valor de tu hora de trabajo",
            width=220,
            hint="Ej: 2.00",
            value=str(datos.get("costo_hora_trabajo", "") or ""),
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.txt_horas_mes = CampoTexto(
            etiqueta="Horas de trabajo al mes",
            width=220,
            hint="Ej: 160",
            value=str(datos.get("horas_trabajo_mes", "") or ""),
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        tarjeta_mano_obra = TarjetaFormulario(
            titulo="Mano de obra",
            subtitulo=(
                "Estos dos valores son la base para calcular todo lo "
                "demás: mano de obra y costos indirectos de cada "
                "producto se prorratean a partir de las horas que "
                "trabajás al mes."
            ),
            contenido=[
                ft.Row(
                    [self.txt_costo_hora, self.txt_horas_mes],
                    spacing=AppSpacing.CONTROL_SPACING,
                ),
                BotonPrimario(
                    texto="Guardar",
                    icono=AppIcons.SAVE,
                    on_click=self._guardar,
                ),
            ],
            expand=False,  # ❗ No expandir para evitar colapso
        )

        tarjeta_desglose = self._tarjeta_desglose()

        # Reemplazar contenido del contenedor
        self.contenedor.controls = [
            tarjeta_mano_obra,
            tarjeta_desglose,
        ]

        # Forzar actualización si el control ya está en la página
        if self.layout_principal and self.layout_principal.page:
            self.layout_principal.update()

    def _tarjeta_desglose(self):
        resultado = self._service.obtener_desglose()
        desglose = resultado.datos if resultado.exito else {
            "costo_hora_trabajo": 0.0,
            "tasa_servicios_por_hora": 0.0,
            "tasa_depreciacion_por_hora": 0.0,
            "costo_hora_total": 0.0,
        }

        filas = [
            ("Mano de obra", desglose["costo_hora_trabajo"]),
            ("Servicios (luz, agua, gas...)", desglose["tasa_servicios_por_hora"]),
            ("Depreciación de herramientas", desglose["tasa_depreciacion_por_hora"]),
        ]

        filas_widgets = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(titulo),
                    ft.Text(f"${valor:.2f} / hora"),
                ],
            )
            for titulo, valor in filas
        ]

        total = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Costo total por hora", weight=AppTypography.BOLD),
                ft.Text(
                    f"${desglose['costo_hora_total']:.2f} / hora",
                    weight=AppTypography.BOLD,
                    color=self.tema.primary,
                ),
            ],
        )

        contenido = [*filas_widgets, ft.Divider(), total]

        if desglose["tasa_servicios_por_hora"] == 0 and desglose["tasa_depreciacion_por_hora"] == 0:
            color_aviso = getattr(self.tema, "warning", self.tema.error)
            contenido.append(
                ft.Container(
                    padding=AppSpacing.SM,
                    border_radius=8,
                    bgcolor=color_aviso + "15",
                    content=ft.Text(
                        "Todavía no hay servicios ni herramientas cargados "
                        "en Activos, o falta cargar las horas de trabajo "
                        "al mes arriba — por eso el desglose da $0.",
                        size=AppTypography.SMALL,
                        color=color_aviso,
                    ),
                )
            )

        if self.on_ir_a_activos:
            contenido.append(
                ft.TextButton(
                    text="Gestionar servicios y herramientas en Activos",
                    icon=AppIcons.NEXT,
                    on_click=lambda e: self.on_ir_a_activos(),
                )
            )

        return TarjetaFormulario(
            titulo="Costos indirectos (calculado)",
            subtitulo="Esto se recalcula solo, a partir de lo que tengas cargado en Activos.",
            contenido=contenido,
            expand=False,  # ❗ No expandir
        )

    # ------------------------------------------------------------
    #  Guardar
    # ------------------------------------------------------------

    def _guardar(self, e):
        try:
            costo_hora = float(self.txt_costo_hora.value or 0)
        except ValueError:
            costo_hora = 0

        try:
            horas_mes = float(self.txt_horas_mes.value or 0)
        except ValueError:
            horas_mes = 0

        resultado = self._service.guardar({
            "costo_hora_trabajo": costo_hora,
            "horas_trabajo_mes": horas_mes,
        })

        if resultado.exito:
            MensajeSistema.exito(self.page, resultado.mensaje)
        else:
            MensajeSistema.error(self.page, resultado.mensaje)

        # Re-renderizar todo
        self.cargar()