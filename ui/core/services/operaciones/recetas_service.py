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
#
# DECISIÓN DE PRODUCTO: se trabaja solo con unidades básicas de medida
# (g, kg, ml, L, unidad). Se eliminaron cucharada/cucharadita/taza (y
# sus fracciones), docena, oz, lb y mg porque eran fuente de errores:
# eran ambiguas (una "taza" no pesa/mide igual según el ingrediente) o
# no correspondían a cómo realmente se registra el inventario. Se
# mantienen únicamente pequeñas variantes de escritura (gr, litro,
# etc.) para tolerar cómo pudo haberse tipeado antes en la base, pero
# el formulario ya no ofrece más que las 5 unidades básicas.
UNIDADES_CANONICAS = {
    # Masa -> gramo
    "g": ("masa", 1), "gr": ("masa", 1), "grs": ("masa", 1),
    "gramo": ("masa", 1), "gramos": ("masa", 1),
    "kg": ("masa", 1000), "kgs": ("masa", 1000),
    "kilo": ("masa", 1000), "kilos": ("masa", 1000),
    "kilogramo": ("masa", 1000), "kilogramos": ("masa", 1000),

    # Volumen -> mililitro
    "ml": ("volumen", 1), "mls": ("volumen", 1),
    "mililitro": ("volumen", 1), "mililitros": ("volumen", 1),
    "l": ("volumen", 1000), "lt": ("volumen", 1000), "lts": ("volumen", 1000),
    "litro": ("volumen", 1000), "litros": ("volumen", 1000),

    # Conteo -> unidad
    "unidad": ("conteo", 1), "unidades": ("conteo", 1), "u": ("conteo", 1),
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

        # Se consolida (y se valida la conversión de unidades) ANTES de
        # escribir nada en la base: si esto falla, no queremos dejar una
        # receta creada sin sus ingredientes.
        try:
            ingredientes_consolidados = self.consolidar_ingredientes(ingredientes_raw)
        except ValueError as e:
            return ServiceResult.error(
                "No se pudieron combinar los ingredientes repetidos.",
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
            ingredientes_consolidados = self.consolidar_ingredientes(ingredientes_raw)
        except ValueError as e:
            return ServiceResult.error(
                "No se pudieron combinar los ingredientes repetidos.",
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
        """
        Combina en una sola entrada por id_ingrediente todas las filas de
        trabajo (propias + las traídas de base/relleno/cobertura).

        ❌ Bug anterior: si el mismo ingrediente aparecía dos veces con
        unidades distintas (ej. 100 g como propio + 0.5 kg traído de una
        Base), se sumaban los números crudos (100 + 0.5 = 100.5) sin
        convertir, y el resultado se guardaba con la unidad de la
        PRIMERA aparición. Esto corrompía en silencio la cantidad
        guardada en RECETA_INGREDIENTES y, por lo tanto, costos futuros.

        ✅ Ahora: la cantidad de cada aparición nueva se convierte a la
        unidad ya registrada para ese ingrediente antes de sumar. Si las
        unidades son de magnitudes incompatibles (ej. g vs unidad), se
        deja que convertir_unidad levante ValueError en vez de sumar
        números que no significan lo mismo.
        """
        consolidado = {}
        for ing in ingredientes:
            id_ing = ing["id"]
            cantidad = float(ing["cantidad"])
            unidad = ing["unidad"]

            if id_ing in consolidado:
                entrada = consolidado[id_ing]
                cantidad_convertida = self.convertir_unidad(cantidad, unidad, entrada["unidad"])
                entrada["cantidad"] += cantidad_convertida
            else:
                consolidado[id_ing] = {
                    "id_ingrediente": id_ing,
                    "cantidad": cantidad,
                    "unidad": unidad,
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
        """
        ❌ Bug anterior: si el ingrediente ya estaba en la lista (mismo
        id, origen "propio") se hacía 'ing["cantidad"] += cantidad' sin
        importar si la unidad nueva coincidía con la ya guardada. Ej.:
        agregar "Harina, 500, g" y luego "Harina, 2, kg" daba 502,
        etiquetado como "g", en vez de 2500 g reales.

        ✅ Ahora: la cantidad nueva se convierte a la unidad ya guardada
        antes de sumar. Si son de magnitudes distintas (ej. g vs
        unidad), convertir_unidad levanta ValueError y quien llama debe
        mostrarle el error al usuario en vez de sumar números que no
        significan lo mismo.
        """
        for ing in ingredientes:
            if ing.get("id") == id_ingrediente and ing.get("origen", "propio") == "propio":
                cantidad_convertida = self.convertir_unidad(cantidad, unidad, ing["unidad"])
                ing["cantidad"] += cantidad_convertida
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
        (ml, L); si se maneja por Unidad, la receta debe usar "unidad".

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
        Parsea el campo 'contenido_unidad' del ingrediente. Acepta dos
        formatos:
          - Número puro, ej. '100', '500', '1.5' -> se asume que está
            expresado en la misma 'unidad_medida' que ya tiene el
            ingrediente (que es como realmente se carga: el usuario
            escribe el número acá y elige la unidad en el combobox
            'Unidad de medida', no vuelve a escribirla en este campo).
          - Número + unidad en el mismo texto, ej. '500 g', '1kg', '750ml'
            -> por si en algún ingrediente sí se cargó así.

        Devuelve (cantidad, unidad_o_None). unidad es None cuando el
        campo es un número puro; en ese caso quien llama debe asumir la
        unidad_medida del ingrediente. Devuelve None si el campo está
        vacío o no tiene un formato reconocible.
        """
        if not contenido:
            return None
        texto = str(contenido).strip()

        # Número puro (sin unidad en el texto)
        match_numero = re.match(r"^([\d]+(?:[.,][\d]+)?)$", texto)
        if match_numero:
            try:
                cantidad = float(match_numero.group(1).replace(",", "."))
            except ValueError:
                return None
            return (cantidad, None) if cantidad > 0 else None

        # Número + unidad en el mismo texto
        match = re.match(r"^\s*([\d]+(?:[.,][\d]+)?)\s*([a-zA-Zñáéíóú]+)\s*$", texto)
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

    def calcular_subtotal(self, ingredientes: List[Dict]) -> float:
        """
        costo_unitario SIEMPRE representa el precio de UN paquete/frasco/
        pieza completa tal como se compró (lo que el usuario escribió en
        el campo 'Costo ($)' del formulario de ingredientes), nunca el
        precio "por gramo" o "por ml".

        Cuando el ingrediente tiene 'Contenido por unidad' (ej. '500 g',
        '100 ml') definido, ese campo indica cuánto producto real trae
        CADA paquete comprado. El costo de usar una cantidad de la receta
        es entonces:

            costo_item = costo_unitario * (cantidad_usada / contenido_del_paquete)

        Esto debe aplicarse SIEMPRE que 'Contenido por unidad' esté
        definido, sin importar si la unidad de la receta coincide o no
        con la 'unidad_medida' del ingrediente.

        ❌ Bug anterior: la conversión de unidades solo consultaba
        'Contenido por unidad' cuando la conversión directa entre
        unidad_receta y unidad_medida FALLABA (ej. kg -> g). Pero si
        ambas unidades eran la misma magnitud, o directamente la misma
        unidad (ml con ml, g con g), la conversión directa "funcionaba"
        (devolvía la cantidad tal cual, sin fraccionar), y el costo
        terminaba siendo costo_unitario * cantidad_en_gramos_o_ml en vez
        de costo_unitario * fracción_del_paquete. Ejemplo real: esencia
        de vainilla, frasco de 100 ml a $5, receta pide 100 ml -> como
        'ml' = 'ml', el sistema calculaba $5 * 100 = $500 en vez de
        $5 * (100/100) = $5.

        Si el ingrediente NO tiene 'Contenido por unidad' definido, se
        asume que costo_unitario ya es el precio directo por unidad_medida
        (ej. $8 por kg), y simplemente se convierte la cantidad de la
        receta a esa unidad_medida.
        """
        todos = self.repo_ingredientes.listar()
        cache = {i["id_ingrediente"]: i for i in todos}

        subtotal = 0.0
        for item in ingredientes:
            bd = cache.get(item["id"])
            if not bd:
                continue

            nombre = bd.get("nombre_ingrediente", f"id {item['id']}")
            costo_unitario = float(bd.get("costo_unitario", 0))
            unidad_medida = bd.get("unidad_medida", "")
            cantidad_receta = float(item.get("cantidad", 0))
            unidad_receta = item.get("unidad", "")
            contenido_unidad = bd.get("contenido_unidad", "")

            if contenido_unidad:
                parsed = self._parsear_contenido_unidad(contenido_unidad)
                if not parsed:
                    raise ValueError(
                        f"El campo 'Contenido por unidad' del ingrediente '{nombre}' tiene un "
                        f"formato inválido. Usa un número (ej. '500', asumiendo la unidad de "
                        f"medida del ingrediente) o número + unidad (ej. '500 g', '100 ml')."
                    )
                contenido_cantidad, contenido_unidad_str = parsed
                # Si el campo fue un número puro (ej. '100'), no trae unidad
                # propia -> se asume la unidad_medida del ingrediente (así es
                # como realmente se carga: el número va en este campo y la
                # unidad se elige en el combobox 'Unidad de medida').
                unidad_objetivo = contenido_unidad_str or unidad_medida
                try:
                    cantidad_en_contenido = self.convertir_unidad(
                        cantidad_receta, unidad_receta, unidad_objetivo
                    )
                except ValueError as e:
                    raise ValueError(
                        f"{nombre}: la receta usa '{unidad_receta}' pero el 'Contenido por "
                        f"unidad' de este ingrediente está en '{unidad_objetivo}', de otra "
                        f"magnitud. Corregí la unidad en la receta o el campo del ingrediente."
                    ) from e

                fraccion_del_paquete = cantidad_en_contenido / contenido_cantidad
                subtotal += costo_unitario * fraccion_del_paquete
            else:
                # Sin 'Contenido por unidad': costo_unitario ya es el precio
                # directo por unidad_medida (ej. $8/kg).
                try:
                    cantidad_en_unidad_medida = self.convertir_unidad(
                        cantidad_receta, unidad_receta, unidad_medida
                    )
                except ValueError as e:
                    raise ValueError(f"{nombre}: {e}") from e
                subtotal += costo_unitario * cantidad_en_unidad_medida

        return subtotal

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
        """
        ❌ Bug anterior (doble): 'todos = self.repo_ingredientes.listar()'
        devuelve una fila POR LOTE (no por ingrediente), así que el
        diccionario 'cache = {i["id_ingrediente"]: i for i in todos}' se
        pisaba a sí mismo cuando un ingrediente tenía varios lotes -- solo
        quedaba el stock_actual de UN lote, no la suma real disponible.
        Además comparaba 'item["cantidad"]' (en la unidad de la receta,
        ej. kg) directo contra 'stock_actual' (que ya vive en la unidad
        base del ingrediente, ej. g) sin convertir.

        ✅ Ahora: 'cache' solo se usa para datos que NO cambian entre
        lotes (nombre_ingrediente, unidad_medida); el stock real se pide
        con obtener_stock(), que sí suma todos los lotes vigentes. La
        cantidad de la receta se convierte a la unidad_medida del
        ingrediente antes de comparar, igual que ya hace calcular_subtotal().
        """
        try:
            consolidado = self.consolidar_ingredientes(ingredientes)
        except ValueError as e:
            return ServiceResult.error(
                "No se pudo verificar el stock por un problema de unidades.",
                errores={"ingredientes": str(e)},
            )

        todos = self.repo_ingredientes.listar()
        cache = {i["id_ingrediente"]: i for i in todos}
        faltantes = []
        for item in consolidado:
            id_ingrediente = item["id_ingrediente"]
            bd = cache.get(id_ingrediente)
            if not bd:
                continue

            nombre = bd.get("nombre_ingrediente", f"id {id_ingrediente}")
            unidad_medida = bd.get("unidad_medida", "")

            try:
                cantidad_necesaria = self.convertir_unidad(
                    float(item["cantidad"]), item["unidad"], unidad_medida
                )
            except ValueError as e:
                # Unidad incompatible: no se puede comparar con el stock,
                # se informa como falta en vez de comparar números que no
                # significan lo mismo.
                faltantes.append({
                    "ingrediente": nombre,
                    "error": str(e),
                })
                continue

            stock = self.repo_ingredientes.obtener_stock(id_ingrediente)
            if cantidad_necesaria > stock:
                faltantes.append({
                    "ingrediente": nombre,
                    "stock": stock,
                    "solicitado": cantidad_necesaria,
                })
        return ServiceResult.ok(datos=faltantes)