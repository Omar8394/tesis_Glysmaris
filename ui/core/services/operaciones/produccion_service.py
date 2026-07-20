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
        self._recetas_service = None

    def set_servicios_auxiliares(
        self,
        ingrediente_service=None,
        activo_service=None,
        producto_service=None,
        recetas_service=None,
    ):
        """Inyecta servicios auxiliares (todos opcionales)."""
        self._ingrediente_service = ingrediente_service
        self._activo_service = activo_service
        self._producto_service = producto_service
        self._recetas_service = recetas_service

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
        if not self._ingrediente_service or not self._activo_service:
            return ServiceResult.error("Faltan servicios de inventario configurados.")

        detalles = self.repo.listar_detalles_por_orden(id_orden)
        if not detalles:
            return ServiceResult.error("La orden no tiene productos.")

        # 1) Validación final: resolver requerimientos y confirmar stock
        #    ANTES de descontar nada. Si algo falla acá, no se toca el
        #    inventario.
        requerimientos_por_detalle = []
        for detalle in detalles:
            resultado_req = self._resolver_requerimientos_producto(
                detalle["id_producto"], detalle["cantidad_planificada"]
            )
            if resultado_req.fallo:
                return ServiceResult.error(f"No se puede iniciar: {resultado_req.mensaje}")
            req = resultado_req.datos

            for ing in req["ingredientes"]:
                disp = self._ingrediente_service.verificar_disponibilidad(ing["id_ingrediente"], ing["cantidad"])
                if disp.fallo or not disp.datos["suficiente"]:
                    return ServiceResult.error(
                        f"Stock insuficiente de '{ing['nombre']}' para fabricar '{req['nombre_producto']}'."
                    )
            for emp in req["empaques"]:
                activo = self._activo_service.obtener(emp["id_activo"])
                disponible = float(activo.get("stock_actual", 0)) if activo else 0.0
                if disponible < emp["cantidad"]:
                    return ServiceResult.error(
                        f"Stock insuficiente de '{emp['nombre']}' para fabricar '{req['nombre_producto']}'."
                    )

            requerimientos_por_detalle.append((detalle, req))

        # 2) Descuento real + bitácora en PRODUCCION_INGREDIENTES_RESERVADOS /
        #    PRODUCCION_ACTIVOS_RESERVADOS (necesaria para poder devolver el
        #    stock si la orden se cancela más adelante).
        for detalle, req in requerimientos_por_detalle:
            for ing in req["ingredientes"]:
                resultado_desc = self._ingrediente_service.descontar_stock(ing["id_ingrediente"], ing["cantidad"])
                if resultado_desc.fallo:
                    return ServiceResult.error(
                        f"Error al descontar '{ing['nombre']}' (orden ya quedó parcialmente descontada, revisar manualmente): {resultado_desc.mensaje}"
                    )
                for lote in resultado_desc.datos:
                    self.repo.crear_reserva_ingrediente({
                        "id_orden": id_orden,
                        "id_detalle": detalle["id_detalle"],
                        "id_producto": detalle["id_producto"],
                        "id_ingrediente": ing["id_ingrediente"],
                        "id_lote": lote["id_lote"],
                        "cantidad_reservada": lote["cantidad_descontada"],
                        "cantidad_consumida": lote["cantidad_descontada"],
                    })

            for emp in req["empaques"]:
                resultado_desc = self._activo_service.descontar_stock(emp["id_activo"], emp["cantidad"])
                if resultado_desc.fallo:
                    return ServiceResult.error(
                        f"Error al descontar '{emp['nombre']}' (orden ya quedó parcialmente descontada, revisar manualmente): {resultado_desc.mensaje}"
                    )
                self.repo.crear_reserva_activo({
                    "id_orden": id_orden,
                    "id_detalle": detalle["id_detalle"],
                    "id_producto": detalle["id_producto"],
                    "id_activo": emp["id_activo"],
                    "cantidad_reservada": emp["cantidad"],
                    "cantidad_consumida": emp["cantidad"],
                })

        datos_orden = dict(orden)
        datos_orden["fecha_inicio"] = datetime.now()
        self.repo.actualizar_orden(id_orden, datos_orden)
        self.repo.actualizar_estado_orden(id_orden, "en_proceso")
        return ServiceResult.ok("Producción iniciada. Inventario descontado.")

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
                "cantidad_planificada": detalle["cantidad_planificada"],
                "cantidad_obtenida": cantidad_obtenida,
                "rendimiento_porcentaje": rendimiento,
                "precio_final": datos_detalle.get("precio_final", 0.0),
                "costo_calculado": datos_detalle.get("costo_calculado", 0.0),
                "disponible_venta": datos_detalle.get("disponible_venta", True),
            })

        # Mermas (y, si son recuperables, el subproducto que generaron).
        # El subproducto se registra colgado del mismo id_merma -- es solo
        # bitácora: no existe todavía una tabla de "stock de subproductos"
        # que se pueda descontar en otra producción; si más adelante querés
        # que un subproducto se pueda usar como componente real de otra
        # receta/producto, eso es una función aparte.
        for merma in datos_finalizacion.get("mermas", []):
            id_merma = self.repo.crear_merma({
                "id_orden": id_orden,
                "id_detalle": merma.get("id_detalle"),
                "id_producto": merma.get("id_producto"),
                "cantidad": merma["cantidad"],
                "tipo_merma": merma["tipo_merma"],
                "motivo": merma["motivo"],
                "descripcion": merma.get("descripcion", ""),
                "costo_asociado": merma.get("costo_asociado", 0.0),
            })

            subproducto = merma.get("subproducto")
            if merma["tipo_merma"] == "recuperable" and subproducto:
                self.repo.crear_subproducto({
                    "id_merma": id_merma,
                    "id_detalle": merma.get("id_detalle"),
                    "id_producto_subproducto": subproducto["id_producto_subproducto"],
                    "cantidad": subproducto["cantidad"],
                    "unidad": subproducto.get("unidad", ""),
                })

        datos_orden = dict(orden)
        datos_orden["fecha_fin"] = datetime.now()
        self.repo.actualizar_orden(id_orden, datos_orden)
        self.repo.actualizar_estado_orden(id_orden, "finalizada")
        return ServiceResult.ok("Orden finalizada exitosamente.")

    def cancelar_orden(self, id_orden: int) -> ServiceResult:
        orden = self.repo.obtener_orden(id_orden)
        if not orden:
            return ServiceResult.error("La orden no existe.")
        if orden["estado"] not in ["pendiente", "en_proceso"]:
            return ServiceResult.error(f"No se puede cancelar una orden en estado '{orden['estado']}'.")

        if orden["estado"] == "en_proceso":
            self._devolver_inventario_orden(id_orden)
            mensaje = "Orden cancelada. El inventario descontado fue devuelto."
        else:
            mensaje = "Orden cancelada."

        self.repo.actualizar_estado_orden(id_orden, "cancelada")
        return ServiceResult.ok(mensaje)

    def analizar_orden_temporal(self, datos: Dict[str, Any]) -> ServiceResult:
        """
        Analiza disponibilidad real de ingredientes y empaques para cada
        producto solicitado, sin guardar nada en BD. Determina, para cada
        producto, si se puede fabricar completo, parcial (según el insumo
        más limitante) o si es inviable.
        """
        detalles = datos.get("detalles", [])
        if not detalles:
            return ServiceResult.error("No hay productos para analizar.")
        if not self._ingrediente_service or not self._activo_service:
            return ServiceResult.error("Faltan servicios de inventario configurados.")

        resultados = []
        total_faltantes = 0
        costo_estimado = 0.0
        tiempo_estimado = 0.0

        for det in detalles:
            id_producto = det["id_producto"]
            cantidad_solicitada = det["cantidad"]

            resultado_req = self._resolver_requerimientos_producto(id_producto, cantidad_solicitada)
            if resultado_req.fallo:
                resultados.append({
                    "id_producto": id_producto,
                    "nombre": f"Producto {id_producto}",
                    "cantidad_solicitada": cantidad_solicitada,
                    "cantidad_posible": 0,
                    "resultado": "inviable",
                    "faltantes": [{
                        "tipo": "error",
                        "nombre": resultado_req.mensaje,
                        "necesario": 0, "disponible": 0, "faltante": 0,
                    }],
                })
                total_faltantes += 1
                continue

            req = resultado_req.datos
            costo_estimado += req["costo_unitario"] * cantidad_solicitada
            tiempo_estimado += req["tiempo_unitario"] * cantidad_solicitada

            faltantes = []
            proporcion_minima = 1.0  # menor proporción disponible entre todos los insumos

            for ing in req["ingredientes"]:
                disp = self._ingrediente_service.verificar_disponibilidad(ing["id_ingrediente"], ing["cantidad"])
                if disp.fallo:
                    faltantes.append({"tipo": "ingrediente", "nombre": ing["nombre"], "necesario": ing["cantidad"], "disponible": 0, "faltante": ing["cantidad"]})
                    proporcion_minima = 0
                    continue
                info = disp.datos
                if not info["suficiente"]:
                    faltantes.append({
                        "tipo": "ingrediente",
                        "nombre": ing["nombre"],
                        "necesario": ing["cantidad"],
                        "disponible": info["disponible"],
                        "faltante": info["faltante"],
                    })
                    if ing["cantidad"] > 0:
                        proporcion_minima = min(proporcion_minima, info["disponible"] / ing["cantidad"])

            for emp in req["empaques"]:
                activo = self._activo_service.obtener(emp["id_activo"])
                disponible = float(activo.get("stock_actual", 0)) if activo else 0.0
                if disponible < emp["cantidad"]:
                    faltantes.append({
                        "tipo": "empaque",
                        "nombre": emp["nombre"],
                        "necesario": emp["cantidad"],
                        "disponible": disponible,
                        "faltante": emp["cantidad"] - disponible,
                    })
                    if emp["cantidad"] > 0:
                        proporcion_minima = min(proporcion_minima, disponible / emp["cantidad"])

            if not faltantes:
                cantidad_posible = cantidad_solicitada
                resultado_estado = "completo"
            else:
                cantidad_posible = int(cantidad_solicitada * proporcion_minima)
                resultado_estado = "parcial" if cantidad_posible > 0 else "inviable"
                total_faltantes += len(faltantes)

            resultados.append({
                "id_producto": id_producto,
                "nombre": req["nombre_producto"],
                "cantidad_solicitada": cantidad_solicitada,
                "cantidad_posible": cantidad_posible,
                "resultado": resultado_estado,
                "faltantes": faltantes,
            })

        return ServiceResult.ok(
            "Análisis completado.",
            {
                "resultados": resultados,
                "total_faltantes": total_faltantes,
                "costo_estimado": costo_estimado,
                "tiempo_estimado": tiempo_estimado,
            }
        )

    # =========================================================
    # HELPERS PRIVADOS
    # =========================================================

    def _resolver_requerimientos_producto(self, id_producto: int, cantidad: float) -> ServiceResult:
        """
        Dado un producto y una cantidad a fabricar, devuelve qué
        ingredientes y qué empaques hacen falta, ya escalados a esa
        cantidad.

        - tipo 'individual': usa la receta vinculada. Si la receta rinde en
          'unidad', escala directo. Si rinde en masa/volumen (ej. "2000 g"),
          convierte usando el peso/unidad_peso del producto para saber
          cuántas unidades salen de una tanda completa de la receta.
        - tipo 'elaborado': usa PRODUCTO_COMPONENTES directo (cada
          componente ya define cuánto hace falta por 1 unidad de producto).
        - tipo 'combo': no se fabrica en Producción (agrupa productos ya
          fabricados), así que se rechaza acá.
        """
        if not self._producto_service:
            return ServiceResult.error("No hay servicio de productos configurado.")

        resultado_producto = self._producto_service.obtener(id_producto)
        if resultado_producto.fallo:
            return ServiceResult.error(f"Producto {id_producto} no encontrado.")
        producto = resultado_producto.datos
        nombre_producto = producto.get("nombre") or f"Producto {id_producto}"
        tipo = producto.get("tipo")

        ingredientes: List[Dict] = []

        if tipo == "individual":
            id_receta = producto.get("receta_id")
            if not id_receta:
                return ServiceResult.error(f"El producto '{nombre_producto}' no tiene receta asignada.")
            if not self._recetas_service:
                return ServiceResult.error("No hay servicio de recetas configurado.")

            resultado_receta = self._recetas_service.obtener(id_receta)
            if resultado_receta.fallo:
                return ServiceResult.error(f"No se pudo obtener la receta de '{nombre_producto}'.")

            receta = resultado_receta.datos["receta"]
            ingredientes_receta = resultado_receta.datos["ingredientes"]

            rendimiento_cantidad = float(receta.get("rendimiento_cantidad", 1) or 1)
            rendimiento_unidad = (receta.get("rendimiento_unidad") or "unidad").strip().lower()

            if rendimiento_unidad == "unidad":
                unidades_por_receta = rendimiento_cantidad
            else:
                peso_producto = float(producto.get("peso") or 0)
                unidad_peso_producto = producto.get("unidad_peso") or ""
                if not peso_producto:
                    return ServiceResult.error(
                        f"'{nombre_producto}' no tiene definido su peso/volumen, necesario porque "
                        f"su receta rinde en '{rendimiento_unidad}' y no en unidades."
                    )
                try:
                    rendimiento_en_unidad_producto = self._recetas_service.convertir_unidad(
                        rendimiento_cantidad, rendimiento_unidad, unidad_peso_producto
                    )
                except ValueError as e:
                    return ServiceResult.error(str(e))
                unidades_por_receta = rendimiento_en_unidad_producto / peso_producto

            if unidades_por_receta <= 0:
                return ServiceResult.error(f"El rendimiento de la receta de '{nombre_producto}' es inválido.")

            factor = cantidad / unidades_por_receta
            for ing in ingredientes_receta:
                # cantidad_necesaria está en la unidad con la que se cargó
                # ESA fila de la receta (ing["unidad"]), que puede no ser
                # la misma que la unidad base del ingrediente en stock
                # (ing["unidad_medida"], la que usa LOTES_INVENTARIO). Hay
                # que convertir antes de comparar contra el stock, si no
                # las cantidades quedan completamente disparatadas.
                unidad_receta = ing.get("unidad") or ing.get("unidad_medida")
                try:
                    cantidad_en_unidad_base = self._recetas_service.convertir_unidad(
                        float(ing["cantidad_necesaria"]), unidad_receta, ing["unidad_medida"]
                    )
                except ValueError as ex:
                    return ServiceResult.error(
                        f"No se pudo convertir '{ing['nombre_ingrediente']}' de '{unidad_receta}' "
                        f"a '{ing['unidad_medida']}' en la receta de '{nombre_producto}': {ex}"
                    )
                ingredientes.append({
                    "id_ingrediente": ing["id_ingrediente"],
                    "nombre": ing["nombre_ingrediente"],
                    "cantidad": cantidad_en_unidad_base * factor,
                })

        elif tipo == "elaborado":
            for comp in producto.get("componentes", []):
                if comp.get("tipo") != "ingrediente":
                    # componentes tipo "producto"/"subproducto" (anidados)
                    # quedan fuera de este análisis por ahora.
                    continue
                ingredientes.append({
                    "id_ingrediente": comp["id"],
                    "nombre": comp.get("nombre") or f"Ingrediente {comp['id']}",
                    "cantidad": float(comp.get("cantidad", 0)) * cantidad,
                })

        else:
            return ServiceResult.error(f"Los productos tipo '{tipo}' no se fabrican en Producción.")

        empaques = [
            {
                "id_activo": e["id"],
                "nombre": e.get("nombre") or f"Activo {e['id']}",
                "cantidad": float(e.get("cantidad", 0)) * cantidad,
            }
            for e in producto.get("empaques", [])
        ]

        return ServiceResult.ok(datos={
            "nombre_producto": nombre_producto,
            "ingredientes": ingredientes,
            "empaques": empaques,
            "costo_unitario": float(producto.get("precio_final") or 0),
            "tiempo_unitario": float(producto.get("tiempo_preparacion_minutos") or 0),
        })

    def _devolver_inventario_orden(self, id_orden: int) -> None:
        """Repone a inventario todo lo que se descontó al iniciar la orden
        (usado al cancelar una orden 'en_proceso')."""
        if self._ingrediente_service:
            for reserva in self.repo.listar_reservas_ingredientes_por_orden(id_orden):
                cantidad = float(reserva.get("cantidad_consumida", 0))
                if cantidad > 0 and reserva.get("id_lote"):
                    self._ingrediente_service.devolver_stock(reserva["id_lote"], cantidad)

        if self._activo_service:
            for reserva in self.repo.listar_reservas_activos_por_orden(id_orden):
                cantidad = float(reserva.get("cantidad_consumida", 0))
                if cantidad > 0:
                    self._activo_service.devolver_stock(reserva["id_activo"], cantidad)

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