from __future__ import annotations
from typing import Any, Dict
from ui.core.services.base.service_result import ServiceResult
from ui.core.repositories.operaciones.mi_negocio_repository import ParametrosNegocioRepository
from ui.core.services.operaciones.activo_service import ActivoService


class ParametrosNegocioService:
    """
    Maneja los parámetros globales del negocio: cuánto vale la hora de
    trabajo y cuántas horas se trabajan al mes.

    A partir de esos dos valores, y de lo ya cargado en ACTIVOS
    (servicios con costo mensual, y herramientas/utensilios/mobiliario
    con vida útil), calcula el desglose de costo por hora que después
    usa ProductoService para prorratear mano de obra y costos
    indirectos en cada producto.
    """

    def __init__(self, repositorio: ParametrosNegocioRepository, activo_service: ActivoService):
        self.repo = repositorio
        self.activo_service = activo_service

    # =====================================================
    # VALIDACIÓN
    # =====================================================

    def validar(self, datos: Dict[str, Any]) -> ServiceResult:
        errores = {}

        try:
            costo_hora = float(datos.get("costo_hora_trabajo", 0))
            if costo_hora < 0:
                errores["costo_hora_trabajo"] = "El valor de la hora no puede ser negativo."
        except (TypeError, ValueError):
            errores["costo_hora_trabajo"] = "El valor de la hora debe ser un número."

        try:
            horas_mes = float(datos.get("horas_trabajo_mes", 0))
            if horas_mes < 0:
                errores["horas_trabajo_mes"] = "Las horas de trabajo al mes no pueden ser negativas."
        except (TypeError, ValueError):
            errores["horas_trabajo_mes"] = "Las horas de trabajo al mes deben ser un número."

        if errores:
            return ServiceResult.error("Errores de validación", errores)
        return ServiceResult.ok()

    # =====================================================
    # LECTURA / ESCRITURA
    # =====================================================

    def obtener(self) -> ServiceResult:
        """
        Devuelve los parámetros actuales (costo_hora_trabajo,
        horas_trabajo_mes). Si todavía no se cargó nada, devuelve
        ceros para que la pantalla arranque con los campos vacíos.
        """
        datos = self.repo.obtener_actual() or {
            "costo_hora_trabajo": 0.0,
            "horas_trabajo_mes": 0.0,
        }
        return ServiceResult.ok("", datos)

    def guardar(self, datos: Dict[str, Any]) -> ServiceResult:
        validacion = self.validar(datos)
        if validacion.fallo:
            return validacion

        self.repo.guardar(datos)
        return ServiceResult.ok("Datos guardados correctamente.")

    # =====================================================
    # DESGLOSE DE COSTO POR HORA
    # =====================================================

    def obtener_desglose(self) -> ServiceResult:
        """
        Calcula el desglose de costo por hora:

            - Mano de obra: el costo_hora_trabajo cargado directamente.
            - Servicios: suma de los activos tipo 'servicio' (o con
              modalidad_costo 'mensual') / horas_trabajo_mes.
            - Depreciación: suma de la depreciación mensual de los
              activos depreciables (herramienta, utensilio, mobiliario
              comprados) / horas_trabajo_mes.

        Si todavía no se cargaron horas de trabajo al mes, no se puede
        prorratear nada (división por cero), así que servicios y
        depreciación quedan en 0 y el total es solo la mano de obra.
        """
        parametros = self.repo.obtener_actual() or {}
        costo_hora_trabajo = float(parametros.get("costo_hora_trabajo", 0) or 0)
        horas_trabajo_mes = float(parametros.get("horas_trabajo_mes", 0) or 0)

        if horas_trabajo_mes <= 0:
            return ServiceResult.ok("", {
                "costo_hora_trabajo": costo_hora_trabajo,
                "tasa_servicios_por_hora": 0.0,
                "tasa_depreciacion_por_hora": 0.0,
                "costo_hora_total": costo_hora_trabajo,
            })

        activos = self.activo_service.listar()

        total_servicios_mensual = 0.0
        total_depreciacion_mensual = 0.0

        for activo in activos:
            if activo.get("estado") != "activo":
                continue

            # Servicios: costos mensuales recurrentes (luz, agua, gas,
            # alquiler de herramientas, etc.)
            if activo.get("tipo") == "servicio" or activo.get("modalidad_costo") == "mensual":
                total_servicios_mensual += float(activo.get("costo_unitario", 0) or 0)

            # Depreciación: activos propios con vida útil registrada.
            if activo.get("tipo") in ActivoService.TIPOS_DEPRECIABLES:
                total_depreciacion_mensual += self.activo_service.calcular_depreciacion_mensual(
                    activo["id_activo"]
                )

        tasa_servicios_por_hora = total_servicios_mensual / horas_trabajo_mes
        tasa_depreciacion_por_hora = total_depreciacion_mensual / horas_trabajo_mes
        costo_hora_total = costo_hora_trabajo + tasa_servicios_por_hora + tasa_depreciacion_por_hora

        return ServiceResult.ok("", {
            "costo_hora_trabajo": costo_hora_trabajo,
            "tasa_servicios_por_hora": tasa_servicios_por_hora,
            "tasa_depreciacion_por_hora": tasa_depreciacion_por_hora,
            "costo_hora_total": costo_hora_total,
        })