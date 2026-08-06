"""
============================================================
Sistema La Dulce Tía

Archivo:
    estadisticas_service.py

Responsabilidad:
    Reglas de negocio del módulo de Estadísticas y Analítica.

    Interpreta los datos crudos entregados por
    EstadisticasRepository: clasifica temporadas de alta/baja
    demanda y arma los mensajes que consumirá la vista.

    No contiene SQL ni conoce la conexión a base de datos.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from typing import Any, Dict, List

from ui.core.repositories.operaciones.estadisticas_repository import (
    EstadisticasRepository,
)
from ui.core.services.base.service_result import ServiceResult


class EstadisticasService:
    """
    Servicio del módulo de Estadísticas.

    No hereda de CRUDService: este módulo no gestiona una
    entidad propia (sólo lectura y agregación), por lo que el
    contrato crear/actualizar/eliminar/validar no aplica.
    """

    # Umbrales de clasificación de temporada (regla de negocio)
    UMBRAL_ALTA_DEMANDA = 1.4
    UMBRAL_BAJA_DEMANDA = 0.6

    def __init__(self, repositorio: EstadisticasRepository):
        self._repositorio = repositorio

    # ------------------------------------------------------------------
    # Rendimiento de productos
    # ------------------------------------------------------------------
    def obtener_rendimiento_productos(
        self,
        dias: int = 30,
        limite: int = 20,
    ) -> ServiceResult:
        """
        Devuelve el top de productos más vendidos en el rango
        de días indicado.
        """

        try:
            datos = self._repositorio.obtener_rendimiento_productos(
                dias=dias,
                limite=limite,
            )
        except Exception as error:
            return ServiceResult.error(
                f"No se pudo obtener el rendimiento de productos: {error}"
            )

        if not datos:
            return ServiceResult.ok(
                mensaje="No hay ventas registradas en el período seleccionado.",
                datos=[],
            )

        return ServiceResult.ok(datos=datos)

    # ------------------------------------------------------------------
    # Inteligencia de temporadas
    # ------------------------------------------------------------------
    def obtener_recomendaciones_temporada(self) -> ServiceResult:
        """
        Analiza las ventas del mes actual contra el promedio
        mensual del último año y clasifica cada producto en
        alta demanda, baja demanda, o ninguna (dentro de rango).
        """

        try:
            registros = self._repositorio.obtener_ventas_anuales_por_producto()
        except Exception as error:
            return ServiceResult.error(
                f"No se pudo analizar la tendencia de temporada: {error}"
            )

        alta_demanda: List[Dict[str, Any]] = []
        baja_demanda: List[Dict[str, Any]] = []

        for registro in registros:
            meses_previos = registro.get("meses_previos_con_ventas") or 0

            # Sin al menos un mes previo de historial no hay una base
            # real contra la cual comparar el mes actual; esperamos
            # al menos 1 mes previo con ventas para poder clasificar
            # el producto.
            if meses_previos < 1:
                continue

            # IMPORTANTE: el promedio se calcula únicamente con
            # meses previos al actual (ventas_meses_previos /
            # meses_previos_con_ventas). El mes actual NUNCA debe
            # entrar en su propio promedio de comparación, porque
            # eso sesga el índice hacia 1.0 y amortigua cualquier
            # desviación real (un pico de demanda parecería menor
            # de lo que es, y una caída también).
            promedio_mensual = (
                registro["ventas_meses_previos"] / meses_previos
            )

            if promedio_mensual <= 0:
                continue

            indice = registro["ventas_mes_actual"] / promedio_mensual

            if indice >= self.UMBRAL_ALTA_DEMANDA:
                alta_demanda.append(
                    {
                        "nombre": registro["nombre_producto"],
                        "razon": (
                            f"Ventas {round((indice - 1) * 100)}% superiores "
                            "al promedio habitual este mes."
                        ),
                    }
                )
            elif indice <= self.UMBRAL_BAJA_DEMANDA:
                baja_demanda.append(
                    {
                        "nombre": registro["nombre_producto"],
                        "razon": (
                            f"Caída del {round((1 - indice) * 100)}% en "
                            "demanda respecto al año."
                        ),
                    }
                )

        return ServiceResult.ok(
            datos={"alta": alta_demanda, "baja": baja_demanda},
        )

    # ------------------------------------------------------------------
    # Mermas
    # ------------------------------------------------------------------
    def obtener_reporte_mermas(self, limite: int = 10) -> ServiceResult:
        """
        Devuelve el reporte de pérdidas/mermas con mayor costo
        asociado.
        """

        try:
            datos = self._repositorio.obtener_reporte_mermas(limite=limite)
        except Exception as error:
            return ServiceResult.error(
                f"No se pudo obtener el reporte de mermas: {error}"
            )

        if not datos:
            return ServiceResult.ok(
                mensaje="No hay mermas registradas.",
                datos=[],
            )

        return ServiceResult.ok(datos=datos)