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

import uuid
from typing import List, Dict, Optional

from ui.core.services.base.crud_service import CRUDService
from ui.core.services.base.service_result import ServiceResult
from ui.core.repositories.operaciones.ingrediente_repository import IngredienteRepository

ORIGENES_VALIDOS = ("propio", "base", "relleno", "cobertura")


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

        try:
            id_receta = self.repo.crear({
                "nombre": datos.get("nombre", "").strip(),
                "tipo": datos.get("tipo", "Base"),
                "descripcion": datos.get("descripcion", ""),
            })
        except Exception as e:
            return ServiceResult.error(f"Error al crear la receta: {str(e)}")

        ingredientes_consolidados = self.consolidar_ingredientes(
            datos.get("ingredientes") or [],
        )
        try:
            self.repo.reemplazar_ingredientes(id_receta, ingredientes_consolidados)
        except Exception as e:
            return ServiceResult.error(f"Error al guardar ingredientes: {str(e)}")

        return ServiceResult.ok(
            "Receta creada correctamente.",
            datos={"id_receta": id_receta},
        )

    def actualizar(self, identificador: int, datos: dict) -> ServiceResult:
        resultado = self.validar(datos)
        if resultado.fallo:
            return resultado

        try:
            success = self.repo.actualizar(identificador, {
                "nombre": datos.get("nombre", "").strip(),
                "tipo": datos.get("tipo", "Base"),
                "descripcion": datos.get("descripcion", ""),
            })
            if not success:
                return ServiceResult.error("No se pudo actualizar la receta.")
        except Exception as e:
            return ServiceResult.error(f"Error al actualizar: {str(e)}")

        ingredientes_consolidados = self.consolidar_ingredientes(
            datos.get("ingredientes") or [],
        )
        try:
            self.repo.reemplazar_ingredientes(identificador, ingredientes_consolidados)
        except Exception as e:
            return ServiceResult.error(f"Error al actualizar ingredientes: {str(e)}")

        return ServiceResult.ok("Receta actualizada correctamente.")

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

    def _obtener_factor_conversion(self, unidad_base: str, unidad_receta: str) -> float:
        """
        Devuelve el factor para convertir de unidad_receta a unidad_base.
        Ej: de 'g' a 'kg' → 0.001
        """
        FACTORES = {
            # A kg
            ("kg", "g"): 0.001,
            ("kg", "kg"): 1.0,
            ("kg", "lb"): 0.453592,
            ("kg", "oz"): 0.0283495,
            # A L
            ("L", "ml"): 0.001,
            ("L", "L"): 1.0,
            ("L", "cucharada"): 0.0147868,
            ("L", "cucharadita"): 0.00492892,
            ("L", "taza"): 0.236588,
            ("L", "1/2 taza"): 0.118294,
            ("L", "1/3 taza"): 0.0788627,
            ("L", "1/4 taza"): 0.0591471,
            # A unidad
            ("unidad", "unidad"): 1.0,
            ("unidad", "docena"): 1/12,
        }
        key = (unidad_base.lower(), unidad_receta.lower())
        return FACTORES.get(key, 1.0)

    def calcular_subtotal(self, ingredientes: List[Dict]) -> float:
        """
        Calcula el subtotal de ingredientes convirtiendo cantidades a la unidad base
        del ingrediente antes de multiplicar por el costo unitario.
        """
        todos = self.repo_ingredientes.listar()
        cache = {i["id_ingrediente"]: i for i in todos}

        subtotal = 0.0
        for item in ingredientes:
            bd = cache.get(item["id"])
            if not bd:
                continue

            costo_unitario = float(bd.get("costo_unitario", 0))
            unidad_base = bd.get("unidad_medida", "").lower()
            cantidad = float(item.get("cantidad", 0))
            unidad_receta = item.get("unidad", "").lower()

            # Convertir a unidad base
            if unidad_receta and unidad_receta != unidad_base:
                factor = self._obtener_factor_conversion(unidad_base, unidad_receta)
                cantidad = cantidad * factor

            subtotal += cantidad * costo_unitario

        return round(subtotal, 2)

    def calcular_precio_sugerido(self, ingredientes: List[Dict], factor: float = 3) -> float:
        """
        Calcula el precio sugerido basado únicamente en el subtotal de ingredientes.
        El factor 3 es un margen estándar (costo de ingredientes ≈ 33% del precio final).
        """
        subtotal = self.calcular_subtotal(ingredientes)
        return round(subtotal * factor, 2)

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