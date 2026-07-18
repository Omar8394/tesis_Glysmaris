"""
============================================================
Sistema La Dulce Tía

Archivo:
    produccion_service.py

Responsabilidad:
    Servicio central del módulo de producción.
    Contiene toda la lógica de negocio.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ui.core.services.base.crud_service import CRUDService
from ui.core.services.base.service_result import ServiceResult


class ProduccionService(CRUDService):
    """Servicio de producción."""

    ESTADOS_VALIDOS = ["pendiente", "en_proceso", "finalizada", "cancelada"]
    PRIORIDADES_VALIDAS = ["baja", "media", "alta", "urgente"]
    TIPOS_MERMA_VALIDOS = ["recuperable", "no_recuperable"]
    MOTIVOS_MERMA_VALIDOS = ["quemado", "rotura", "contaminacion", "error_preparacion", "decoracion", "otro"]

    def __init__(self, repositorio):
        """Recibe el repositorio por inyección de dependencias."""
        self.repo = repositorio
        # Servicios auxiliares (opcionales, se inyectan desde factory)
        self._ingrediente_service = None
        self._activo_service = None
        self._producto_service = None

    def set_servicios_auxiliares(
        self,
        ingrediente_service=None,
        activo_service=None,
        producto_service=None,
    ):
        """Inyecta servicios auxiliares (todos opcionales)."""
        self._ingrediente_service = ingrediente_service
        self._activo_service = activo_service
        self._producto_service = producto_service

    # =========================================================
    # MÉTODOS OBLIGATORIOS DE CRUDService
    # =========================================================

    def validar(self, datos: Dict[str, Any]) -> ServiceResult:
        errores = {}

        fecha = datos.get("fecha_planificada")
        if not fecha:
            errores["fecha_planificada"] = "La fecha planificada es obligatoria."

        detalles = datos.get("detalles", [])
        if not detalles:
            errores["detalles"] = "Debe agregar al menos un producto."

        prioridad = datos.get("prioridad", "media")
        if prioridad not in self.PRIORIDADES_VALIDAS:
            errores["prioridad"] = f"Prioridad no válida: {prioridad}"

        if errores:
            return ServiceResult.error("Errores de validación", errores)
        return ServiceResult.ok()

    def crear(self, datos: Dict[str, Any]) -> ServiceResult:
        return self.crear_orden(datos)

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> ServiceResult:
        orden = self.repo.obtener_orden(identificador)
        if not orden:
            return ServiceResult.error("La orden no existe.")
        if orden["estado"] != "pendiente":
            return ServiceResult.error("Solo se pueden actualizar órdenes pendientes.")
        if self.repo.actualizar_orden(identificador, datos):
            return ServiceResult.ok("Orden actualizada.")
        return ServiceResult.error("Error al actualizar.")

    def eliminar(self, identificador: Any) -> ServiceResult:
        orden = self.repo.obtener_orden(identificador)
        if not orden:
            return ServiceResult.error("La orden no existe.")
        if orden["estado"] != "pendiente":
            return ServiceResult.error("Solo se pueden eliminar órdenes pendientes.")
        if self.repo.eliminar_orden(identificador):
            return ServiceResult.ok("Orden eliminada.")
        return ServiceResult.error("Error al eliminar.")

    def obtener(self, identificador: Any) -> Optional[Dict]:
        orden = self.repo.obtener_orden(identificador)
        if not orden:
            return None
        return {
            "orden": orden,
            "detalles": self.repo.listar_detalles_por_orden(identificador),
            "mermas": self.repo.listar_mermas_por_orden(identificador),
            "costos": self.repo.listar_costos_por_orden(identificador),
            "historial": self.repo.listar_historial_por_orden(identificador),
        }

    def listar(self, filtros: Optional[Dict] = None) -> List[Dict]:
        return self.repo.listar_ordenes(filtros)

    def buscar(self, texto: str) -> List[Dict]:
        return self.repo.listar_ordenes({"buscar": texto})

    # =========================================================
    # MÉTODOS ESPECÍFICOS DE PRODUCCIÓN
    # =========================================================

    def crear_orden(self, datos: Dict[str, Any]) -> ServiceResult:
        validacion = self.validar(datos)
        if validacion.fallo:
            return validacion

        numero_orden = self._generar_numero_orden()

        datos_orden = {
            "numero_orden": numero_orden,
            "fecha_planificada": datos["fecha_planificada"],
            "hora_estimada": datos.get("hora_estimada"),
            "prioridad": datos.get("prioridad", "media"),
            "responsable": datos.get("responsable", ""),
            "estado": "pendiente",
            "notas": datos.get("notas", ""),
            "costo_estimado": datos.get("costo_estimado", 0.0),
            "tiempo_estimado_minutos": datos.get("tiempo_estimado_minutos", 0),
            "creado_por": datos.get("creado_por", ""),
        }

        id_orden = self.repo.crear_orden(datos_orden)

        for det in datos.get("detalles", []):
            self.repo.crear_detalle({
                "id_orden": id_orden,
                "id_producto": det["id_producto"],
                "id_presentacion": det.get("id_presentacion"),
                "cantidad_planificada": det["cantidad"],
                "modificaciones": det.get("modificaciones", ""),
            })

        orden = self.repo.obtener_orden(id_orden)
        return ServiceResult.ok(
            f"Orden {numero_orden} creada exitosamente.",
            {"orden": orden, "detalles": self.repo.listar_detalles_por_orden(id_orden)}
        )

    def iniciar_produccion(self, id_orden: int) -> ServiceResult:
        orden = self.repo.obtener_orden(id_orden)
        if not orden:
            return ServiceResult.error("La orden no existe.")
        if orden["estado"] != "pendiente":
            return ServiceResult.error(f"No se puede iniciar una orden en estado '{orden['estado']}'.")

        self.repo.actualizar_estado_orden(id_orden, "en_proceso")
        return ServiceResult.ok("Producción iniciada.")

    def finalizar_produccion(self, id_orden: int, datos_finalizacion: Dict[str, Any]) -> ServiceResult:
        orden = self.repo.obtener_orden(id_orden)
        if not orden:
            return ServiceResult.error("La orden no existe.")
        if orden["estado"] != "en_proceso":
            return ServiceResult.error(f"No se puede finalizar una orden en estado '{orden['estado']}'.")

        detalles = self.repo.listar_detalles_por_orden(id_orden)
        for detalle in detalles:
            id_detalle = detalle["id_detalle"]
            datos_detalle = datos_finalizacion.get("detalles", {}).get(str(id_detalle), {})
            cantidad_obtenida = datos_detalle.get("cantidad_obtenida", detalle["cantidad_planificada"])
            rendimiento = (cantidad_obtenida / detalle["cantidad_planificada"]) * 100 if detalle["cantidad_planificada"] > 0 else 0

            self.repo.actualizar_detalle(id_detalle, {
                "cantidad_obtenida": cantidad_obtenida,
                "rendimiento_porcentaje": rendimiento,
                "precio_final": datos_detalle.get("precio_final", 0.0),
                "costo_calculado": datos_detalle.get("costo_calculado", 0.0),
                "disponible_venta": datos_detalle.get("disponible_venta", True),
            })

        for merma in datos_finalizacion.get("mermas", []):
            self.repo.crear_merma({
                "id_orden": id_orden,
                "id_detalle": merma.get("id_detalle"),
                "id_producto": merma.get("id_producto"),
                "cantidad": merma["cantidad"],
                "tipo_merma": merma["tipo_merma"],
                "motivo": merma["motivo"],
                "descripcion": merma.get("descripcion", ""),
                "costo_asociado": merma.get("costo_asociado", 0.0),
            })

        self.repo.actualizar_estado_orden(id_orden, "finalizada")
        return ServiceResult.ok("Orden finalizada exitosamente.")

    def cancelar_orden(self, id_orden: int) -> ServiceResult:
        orden = self.repo.obtener_orden(id_orden)
        if not orden:
            return ServiceResult.error("La orden no existe.")
        if orden["estado"] not in ["pendiente", "en_proceso"]:
            return ServiceResult.error(f"No se puede cancelar una orden en estado '{orden['estado']}'.")

        self.repo.actualizar_estado_orden(id_orden, "cancelada")
        return ServiceResult.ok("Orden cancelada.")

    def analizar_orden_temporal(self, datos: Dict[str, Any]) -> ServiceResult:
        """
        Analiza disponibilidad de productos sin guardar en BD.
        Versión simplificada: asume que todo es posible.
        """
        detalles = datos.get("detalles", [])
        if not detalles:
            return ServiceResult.error("No hay productos para analizar.")

        resultados = []
        costo_estimado = 0
        tiempo_estimado = 0

        for det in detalles:
            id_producto = det["id_producto"]
            cantidad = det["cantidad"]

            nombre = f"Producto {id_producto}"
            costo_unitario = 0
            tiempo_unitario = 0

            if self._producto_service:
                prod = self._producto_service.obtener(id_producto)
                if prod:
                    nombre = prod.get("nombre_producto", nombre)
                    costo_unitario = prod.get("costo_receta", 0)
                    tiempo_unitario = prod.get("tiempo_preparacion_minutos", 0)

            costo_estimado += costo_unitario * cantidad
            tiempo_estimado += tiempo_unitario * cantidad

            resultados.append({
                "nombre": nombre,
                "cantidad_solicitada": cantidad,
                "cantidad_posible": cantidad,
                "resultado": "completo",
                "faltantes": [],
            })

        return ServiceResult.ok(
            "Análisis completado.",
            {
                "resultados": resultados,
                "total_faltantes": 0,
                "costo_estimado": costo_estimado,
                "tiempo_estimado": tiempo_estimado,
            }
        )

    def _generar_numero_orden(self) -> str:
        ultimo = self.repo.obtener_ultimo_numero_orden()
        if ultimo:
            partes = ultimo.split("-")
            if len(partes) == 3:
                try:
                    secuencia = int(partes[2]) + 1
                except ValueError:
                    secuencia = 1
            else:
                secuencia = 1
        else:
            secuencia = 1

        año = datetime.now().year
        return f"ORD-{año}-{secuencia:05d}"