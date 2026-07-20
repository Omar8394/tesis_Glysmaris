"""
=============================================================
Sistema La Dulce Tía

Servicio de Recetas

Responsabilidad:
    Contiene toda la lógica de negocio del módulo de recetas.
    No contiene SQL. No contiene Flet.

Flujo: Ingredientes → Recetas (costo de ingredientes) → Productos (mano de obra, empaques, margen) → Producción → Ventas
=============================================================
"""

from __future__ import annotations

import re
import uuid
from typing import List, Dict, Optional

from ui.core.services.base.crud_service import CRUDService
from ui.core.services.base.service_result import ServiceResult
from ui.core.repositories.operaciones.ingrediente_repository import IngredienteRepository

ORIGENES_VALIDOS = ("propio", "base", "relleno", "cobertura")

# ==========================================================
# UNIDADES DE MEDIDA
# ==========================================================
# Cada unidad se clasifica por categoría (masa, volumen, conteo) y se
# guarda su factor de conversión hacia la unidad canónica de su
# categoría (gramo, mililitro, unidad respectivamente). Convertir entre
# dos unidades de la MISMA categoría es: cantidad * factor_origen / factor_destino.
#
# IMPORTANTE: si una unidad no está en este mapa, o si se intenta
# convertir entre categorías distintas (ej. "g" a "unidad"), se levanta
# un error explícito en vez de asumir un factor de 1 en silencio. Ese
# "factor 1 por defecto" era la causa del bug de precios inflados: una
# unidad mal escrita (p.ej. "gr" en vez de "g") no hacía match en el
# diccionario viejo y la cantidad en gramos se multiplicaba directo por
# el costo por kilogramo.
UNIDADES_CANONICAS = {
    # Masa -> gramo
    "g": ("masa", 1), "gr": ("masa", 1), "grs": ("masa", 1),
    "gramo": ("masa", 1), "gramos": ("masa", 1),
    "kg": ("masa", 1000), "kgs": ("masa", 1000),
    "kilo": ("masa", 1000), "kilos": ("masa", 1000),
    "kilogramo": ("masa", 1000), "kilogramos": ("masa", 1000),
    "mg": ("masa", 0.001), "miligramo": ("masa", 0.001), "miligramos": ("masa", 0.001),
    "lb": ("masa", 453.592), "lbs": ("masa", 453.592),
    "libra": ("masa", 453.592), "libras": ("masa", 453.592),
    "oz": ("masa", 28.3495), "onza": ("masa", 28.3495), "onzas": ("masa", 28.3495),

    # Volumen -> mililitro
    "ml": ("volumen", 1), "mls": ("volumen", 1),
    "mililitro": ("volumen", 1), "mililitros": ("volumen", 1),
    "l": ("volumen", 1000), "lt": ("volumen", 1000), "lts": ("volumen", 1000),
    "litro": ("volumen", 1000), "litros": ("volumen", 1000),
    "cucharada": ("volumen", 14.7868), "cucharadas": ("volumen", 14.7868),
    "cda": ("volumen", 14.7868), "cdas": ("volumen", 14.7868),
    "cucharadita": ("volumen", 4.92892), "cucharaditas": ("volumen", 4.92892),
    "cdta": ("volumen", 4.92892), "cdtas": ("volumen", 4.92892),
    "taza": ("volumen", 236.588), "tazas": ("volumen", 236.588),
    "1/2 taza": ("volumen", 118.294),
    "1/3 taza": ("volumen", 78.8627),
    "1/4 taza": ("volumen", 59.1471),

    # Conteo -> unidad
    "unidad": ("conteo", 1), "unidades": ("conteo", 1), "u": ("conteo", 1),
    "docena": ("conteo", 12), "docenas": ("conteo", 12),
}


class RecetasService(CRUDService):

    def __init__(self, recetas_repository, ingredientes_repository=None):
        self.repo = recetas_repository
        if ingredientes_repository is None:
            conexion = recetas_repository._conexion
            self.repo_ingredientes = IngredienteRepository(conexion)
        else:
            self.repo_ingredientes = ingredientes_repository

    # ==========================================================
    # CONTRATO CRUD (CRUDService)
    # ==========================================================

    def validar(self, datos: dict) -> ServiceResult:
        errores = {}
        nombre = (datos.get("nombre") or "").strip()
        ingredientes = datos.get("ingredientes") or []

        if not nombre:
            errores["nombre"] = "Debe indicar un nombre."
        elif len(nombre) < 3:
            errores["nombre"] = "Nombre demasiado corto."

        if not ingredientes:
            errores["ingredientes"] = "Debe agregar al menos un ingrediente."

        rendimiento_unidad = (datos.get("rendimiento_unidad") or "").strip()
        if not rendimiento_unidad:
            errores["rendimiento_unidad"] = "Debe indicar la unidad de rendimiento."
        elif self._normalizar_unidad(rendimiento_unidad) not in UNIDADES_CANONICAS:
            errores["rendimiento_unidad"] = f"Unidad de rendimiento no reconocida: '{rendimiento_unidad}'."

        try:
            rendimiento_cantidad = float(datos.get("rendimiento_cantidad", 0) or 0)
            if rendimiento_cantidad <= 0:
                errores["rendimiento_cantidad"] = "El rendimiento debe ser mayor a 0."
        except (TypeError, ValueError):
            errores["rendimiento_cantidad"] = "El rendimiento debe ser un número."

        if errores:
            return ServiceResult.error(
                "Revisá los datos de la receta.",
                errores=errores,
            )
        return ServiceResult.ok()

    def crear(self, datos: dict) -> ServiceResult:
        resultado = self.validar(datos)
        if resultado.fallo:
            return resultado

        ingredientes_raw = datos.get("ingredientes") or []

        try:
            costo_ingredientes = self.calcular_subtotal(ingredientes_raw)
        except ValueError as e:
            return ServiceResult.error(
                "No se pudo calcular el costo de la receta.",
                errores={"ingredientes": str(e)},
            )

        try:
            id_receta = self.repo.crear({
                "nombre": datos.get("nombre", "").strip(),
                "tipo": datos.get("tipo", "Base"),
                "descripcion": datos.get("descripcion", ""),
                "costo_ingredientes": costo_ingredientes,
                "rendimiento_cantidad": float(datos.get("rendimiento_cantidad", 1) or 1),
                "rendimiento_unidad": (datos.get("rendimiento_unidad") or "unidad").strip(),
            })
        except Exception as e:
            return ServiceResult.error(f"Error al crear la receta: {str(e)}")

        ingredientes_consolidados = self.consolidar_ingredientes(ingredientes_raw)
        try:
            self.repo.reemplazar_ingredientes(id_receta, ingredientes_consolidados)
        except Exception as e:
            return ServiceResult.error(f"Error al guardar ingredientes: {str(e)}")

        return ServiceResult.ok(
            "Receta creada correctamente.",
            datos={"id_receta": id_receta, "costo_ingredientes": costo_ingredientes},
        )

    def actualizar(self, identificador: int, datos: dict) -> ServiceResult:
        resultado = self.validar(datos)
        if resultado.fallo:
            return resultado

        ingredientes_raw = datos.get("ingredientes") or []

        try:
            costo_ingredientes = self.calcular_subtotal(ingredientes_raw)
        except ValueError as e:
            return ServiceResult.error(
                "No se pudo calcular el costo de la receta.",
                errores={"ingredientes": str(e)},
            )

        try:
            success = self.repo.actualizar(identificador, {
                "nombre": datos.get("nombre", "").strip(),
                "tipo": datos.get("tipo", "Base"),
                "descripcion": datos.get("descripcion", ""),
                "costo_ingredientes": costo_ingredientes,
                "rendimiento_cantidad": float(datos.get("rendimiento_cantidad", 1) or 1),
                "rendimiento_unidad": (datos.get("rendimiento_unidad") or "unidad").strip(),
            })
            if not success:
                return ServiceResult.error("No se pudo actualizar la receta.")
        except Exception as e:
            return ServiceResult.error(f"Error al actualizar: {str(e)}")

        ingredientes_consolidados = self.consolidar_ingredientes(ingredientes_raw)
        try:
            self.repo.reemplazar_ingredientes(identificador, ingredientes_consolidados)
        except Exception as e:
            return ServiceResult.error(f"Error al actualizar ingredientes: {str(e)}")

        return ServiceResult.ok(
            "Receta actualizada correctamente.",
            datos={"costo_ingredientes": costo_ingredientes},
        )

    def eliminar(self, identificador: int) -> ServiceResult:
        try:
            success = self.repo.eliminar(identificador)
            if not success:
                return ServiceResult.error("No se pudo eliminar la receta.")
            return ServiceResult.ok("Receta eliminada correctamente.")
        except Exception as e:
            return ServiceResult.error(str(e))

    def obtener(self, identificador: int) -> ServiceResult:
        try:
            receta = self.repo.obtener(identificador)
            if not receta:
                return ServiceResult.error("Receta no encontrada.")
            ingredientes = self.repo.obtener_ingredientes(identificador)
            return ServiceResult.ok(
                datos={
                    "receta": receta,
                    "ingredientes": ingredientes,
                }
            )
        except Exception as e:
            return ServiceResult.error(str(e))

    def listar(self, filtro: str = "") -> ServiceResult:
        try:
            recetas = self.repo.listar()
            if filtro:
                texto = filtro.strip().lower()
                recetas = [
                    r for r in recetas
                    if texto in (r.get("nombre_receta") or "").lower()
                ]
            return ServiceResult.ok(datos=recetas)
        except Exception as e:
            return ServiceResult.error(str(e))

    def buscar(self, texto: str) -> ServiceResult:
        try:
            recetas = self.repo.buscar(texto)
            return ServiceResult.ok(datos=recetas)
        except Exception as e:
            return ServiceResult.error(str(e))

    def guardar(self, datos: dict, identificador=None) -> ServiceResult:
        if identificador is None:
            return self.crear(datos)
        return self.actualizar(identificador, datos)

    # ==========================================================
    # CONSULTAS ESPECÍFICAS
    # ==========================================================

    def obtener_por_tipo(self, tipo: str) -> ServiceResult:
        try:
            recetas = self.repo.obtener_por_tipo(tipo)
            return ServiceResult.ok(datos=recetas)
        except Exception as e:
            return ServiceResult.error(str(e))

    def obtener_ingredientes_catalogo(self) -> ServiceResult:
        try:
            ingredientes = self.repo_ingredientes.listar()
            return ServiceResult.ok(datos=ingredientes)
        except Exception as e:
            return ServiceResult.error(str(e))

    # ==========================================================
    # LÓGICA DE INGREDIENTES EN MEMORIA
    # ==========================================================

    def sincronizar_componente(
        self,
        ingredientes: List[Dict],
        origen: str,
        id_receta_componente: Optional[int]
    ) -> List[Dict]:
        if origen not in ORIGENES_VALIDOS:
            raise ValueError(f"Origen inválido: {origen}")

        ingredientes = [ing for ing in ingredientes if ing.get("origen", "propio") != origen]

        if not id_receta_componente:
            return ingredientes

        ingredientes_receta = self.repo.obtener_ingredientes(id_receta_componente)
        for ing in ingredientes_receta:
            ingredientes.append({
                "uid": uuid.uuid4().hex,
                "id": ing["id_ingrediente"],
                "nombre": ing["nombre_ingrediente"],
                "cantidad": float(ing["cantidad_necesaria"]),
                "unidad": ing["unidad"],
                "origen": origen,
                "origen_receta_id": id_receta_componente,
            })
        return ingredientes

    def quitar_componente(self, ingredientes: List[Dict], origen: str) -> List[Dict]:
        return self.sincronizar_componente(ingredientes, origen, None)

    def preparar_ingredientes_para_edicion(self, ingredientes_bd: List[Dict]) -> List[Dict]:
        return [
            {
                "uid": uuid.uuid4().hex,
                "id": ing["id_ingrediente"],
                "nombre": ing["nombre_ingrediente"],
                "cantidad": float(ing["cantidad_necesaria"]),
                "unidad": ing["unidad"],
                "origen": "propio",
            }
            for ing in ingredientes_bd
        ]

    def consolidar_ingredientes(self, ingredientes: List[Dict]) -> List[Dict]:
        consolidado = {}
        for ing in ingredientes:
            id_ing = ing["id"]
            if id_ing in consolidado:
                consolidado[id_ing]["cantidad"] += float(ing["cantidad"])
            else:
                consolidado[id_ing] = {
                    "id_ingrediente": id_ing,
                    "cantidad": float(ing["cantidad"]),
                    "unidad": ing["unidad"],
                }
        return list(consolidado.values())

    def agregar_ingrediente(
        self,
        ingredientes: List[Dict],
        id_ingrediente: int,
        nombre: str,
        cantidad: float,
        unidad: str
    ) -> List[Dict]:
        for ing in ingredientes:
            if ing.get("id") == id_ingrediente and ing.get("origen", "propio") == "propio":
                ing["cantidad"] += cantidad
                return ingredientes

        ingredientes.append({
            "uid": uuid.uuid4().hex,
            "id": id_ingrediente,
            "nombre": nombre,
            "cantidad": cantidad,
            "unidad": unidad,
            "origen": "propio",
        })
        return ingredientes

    def actualizar_cantidad(self, ingredientes: List[Dict], uid: str, nueva_cantidad: float) -> List[Dict]:
        for ing in ingredientes:
            if ing.get("uid") == uid:
                ing["cantidad"] = nueva_cantidad
                break
        return ingredientes

    def eliminar_ingrediente(self, ingredientes: List[Dict], uid: str) -> List[Dict]:
        return [ing for ing in ingredientes if ing.get("uid") != uid]

    # ==========================================================
    # COSTOS (solo ingredientes, con conversión de unidades)
    # ==========================================================

    def _normalizar_unidad(self, unidad: str) -> str:
        return (unidad or "").strip().lower().rstrip(".")

    def convertir_unidad(self, cantidad: float, unidad_origen: str, unidad_destino: str) -> float:
        """
        Convierte 'cantidad' de unidad_origen a unidad_destino. Solo funciona
        entre unidades de la MISMA magnitud (masa con masa, volumen con
        volumen, conteo con conteo) — no hay conversión entre masa y volumen,
        porque eso depende de la densidad de cada ingrediente y es una fuente
        común de error. Si un ingrediente se maneja en inventario en Kg/g,
        la receta debe cargarlo también en una unidad de masa (g, kg, lb, oz);
        si se maneja en L/ml, la receta debe usar una unidad de volumen
        (ml, L, cucharada, taza, etc.); si se maneja por Unidad, la receta
        debe usar "unidad" o "docena".

        Lanza ValueError si alguna unidad no se reconoce, o si son de
        magnitudes distintas. Nunca devuelve un factor "por defecto" sin
        avisar — eso es justo lo que causaba costos inflados en silencio
        antes de este fix.
        """
        origen = self._normalizar_unidad(unidad_origen)
        destino = self._normalizar_unidad(unidad_destino)

        if origen == destino:
            return cantidad

        info_origen = UNIDADES_CANONICAS.get(origen)
        info_destino = UNIDADES_CANONICAS.get(destino)

        if not info_origen or not info_destino:
            desconocida = unidad_origen if not info_origen else unidad_destino
            raise ValueError(f"unidad no reconocida: '{desconocida}'")

        categoria_origen, factor_origen = info_origen
        categoria_destino, factor_destino = info_destino

        if categoria_origen != categoria_destino:
            raise ValueError(
                f"la receta usa '{unidad_origen}' pero este ingrediente se maneja en "
                f"'{unidad_destino}' ({categoria_destino}). Corregí la unidad en la receta "
                f"para que sea del mismo tipo (masa con masa, volumen con volumen, o "
                f"conteo con conteo)."
            )

        cantidad_canonica = cantidad * factor_origen
        return cantidad_canonica / factor_destino

    def _parsear_contenido_unidad(self, contenido: str) -> Optional[tuple]:
        """
        Parsea el campo 'contenido_unidad' del ingrediente (ej. '500 g',
        '1kg', '750ml') en (cantidad, unidad). Devuelve None si el campo
        está vacío o no tiene un formato reconocible.
        """
        if not contenido:
            return None
        match = re.match(r"^\s*([\d]+(?:[.,][\d]+)?)\s*([a-zA-Zñáéíóú]+)\s*$", contenido.strip())
        if not match:
            return None
        cantidad_str, unidad_str = match.groups()
        try:
            cantidad = float(cantidad_str.replace(",", "."))
        except ValueError:
            return None
        if cantidad <= 0:
            return None
        return cantidad, unidad_str

    def _convertir_a_unidad_base(self, cantidad: float, unidad_receta: str, unidad_base: str, bd: Dict) -> float:
        """
        Convierte la cantidad de la receta a la unidad_medida del ingrediente.

        Camino normal: misma magnitud (g<->kg, ml<->L, etc.) -> convertir_unidad directo.

        Camino especial: el ingrediente se compra por 'unidad' (ej. una
        barra/paquete) pero la receta lo usa por peso o volumen (ej.
        mantequilla comprada como "1 unidad" que contiene 500 g, usada en
        la receta como "250 g"). En ese caso se usa el campo
        contenido_unidad del ingrediente (ej. "500 g") para saber cuánto
        trae cada unidad comprada, y se calcula qué fracción de esa unidad
        se está usando en la receta. Esa fracción es lo que se multiplica
        después por el costo_unitario (que es el costo de UNA unidad
        completa comprada).
        """
        try:
            return self.convertir_unidad(cantidad, unidad_receta, unidad_base)
        except ValueError:
            pass

        contenido = self._parsear_contenido_unidad(bd.get("contenido_unidad", ""))
        if not contenido:
            raise ValueError(
                f"la receta usa '{unidad_receta}' pero este ingrediente se maneja en "
                f"'{unidad_base}'. Corregí la unidad en la receta, o completá el campo "
                f"'contenido por unidad' del ingrediente (ej. '500 g') para poder calcular "
                f"el costo por porción."
            )

        contenido_cantidad, contenido_unidad_str = contenido
        try:
            cantidad_en_unidad_contenido = self.convertir_unidad(cantidad, unidad_receta, contenido_unidad_str)
        except ValueError:
            raise ValueError(
                f"la receta usa '{unidad_receta}' pero el 'contenido por unidad' registrado "
                f"para este ingrediente está en '{contenido_unidad_str}', que es de otra "
                f"magnitud. Revisá esos datos."
            )

        return cantidad_en_unidad_contenido / contenido_cantidad

    def calcular_subtotal(self, ingredientes: List[Dict]) -> float:
        """
        Calcula el subtotal de ingredientes convirtiendo cantidades a la unidad
        en que está valorado cada ingrediente (unidad_medida) antes de
        multiplicar por su costo_unitario. Si el ingrediente se compra por
        'unidad' pero la receta lo usa por peso/volumen, usa el campo
        contenido_unidad para calcular la fracción de esa unidad que se usó.

        Puede lanzar ValueError si algún ingrediente trae una unidad que no
        se puede resolver de ninguna de las dos formas — esto es intencional:
        es preferible frenar con un mensaje claro a calcular un costo erróneo.
        """
        todos = self.repo_ingredientes.listar()
        cache = {i["id_ingrediente"]: i for i in todos}

        subtotal = 0.0
        for item in ingredientes:
            bd = cache.get(item["id"])
            if not bd:
                continue

            costo_unitario = float(bd.get("costo_unitario", 0))
            unidad_base = bd.get("unidad_medida", "")
            cantidad = float(item.get("cantidad", 0))
            unidad_receta = item.get("unidad", "")

            if self._normalizar_unidad(unidad_receta) != self._normalizar_unidad(unidad_base):
                try:
                    cantidad = self._convertir_a_unidad_base(cantidad, unidad_receta, unidad_base, bd)
                except ValueError as e:
                    nombre = bd.get("nombre_ingrediente", f"id {item['id']}")
                    raise ValueError(f"{nombre}: {e}") from e

            subtotal += cantidad * costo_unitario

        return round(subtotal, 2)

    def recalcular_costo(self, identificador: int) -> ServiceResult:
        """
        Vuelve a calcular el costo de ingredientes de una receta ya guardada
        (leyendo sus ingredientes y costos actuales) y lo persiste en la
        columna costo_ingredientes. Útil para refrescar el costo cuando
        cambia el precio de algún ingrediente en el inventario, sin tener
        que reabrir y volver a guardar la receta manualmente.
        """
        try:
            ingredientes_bd = self.repo.obtener_ingredientes(identificador)
        except Exception as e:
            return ServiceResult.error(str(e))

        ingredientes = [
            {
                "id": ing["id_ingrediente"],
                "cantidad": float(ing["cantidad_necesaria"]),
                "unidad": ing["unidad"],
            }
            for ing in ingredientes_bd
        ]

        try:
            costo = self.calcular_subtotal(ingredientes)
        except ValueError as e:
            return ServiceResult.error(
                "No se pudo recalcular el costo de la receta.",
                errores={"ingredientes": str(e)},
            )

        try:
            self.repo.actualizar_costo(identificador, costo)
        except Exception as e:
            return ServiceResult.error(f"Error al guardar el costo: {str(e)}")

        return ServiceResult.ok(
            "Costo recalculado correctamente.",
            datos={"costo_ingredientes": costo},
        )

    # ==========================================================
    # STOCK
    # ==========================================================

    def verificar_stock(self, ingredientes: List[Dict]) -> ServiceResult:
        consolidado = self.consolidar_ingredientes(ingredientes)
        todos = self.repo_ingredientes.listar()
        cache = {i["id_ingrediente"]: i for i in todos}
        faltantes = []
        for item in consolidado:
            bd = cache.get(item["id_ingrediente"])
            if bd:
                stock = float(bd.get("stock_actual", 0))
                solicitado = float(item["cantidad"])
                if solicitado > stock:
                    faltantes.append({
                        "ingrediente": bd["nombre_ingrediente"],
                        "stock": stock,
                        "solicitado": solicitado,
                    })
        return ServiceResult.ok(datos=faltantes)