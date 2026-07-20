"""
Repositorio para la tabla PRODUCTOS (y sus tablas relacionadas).

Soporta los 3 tipos de producto del wizard:
    - individual: usa receta_id + PRODUCTO_PRESENTACIONES
    - elaborado:  usa PRODUCTO_COMPONENTES (ingrediente/producto/subproducto)
    - combo:      usa PRODUCTO_COMBO_ITEMS + precio_combo/descuento_combo

Empaques y costos indirectos son ambos "ACTIVOS" (lo que en la UI se
llama "recursos"), diferenciados por ACTIVOS.tipo ('empaque' /
'costo_indirecto'), y se relacionan con el producto a través de una
única tabla puente: PRODUCTO_ACTIVO.

⚠️ Requiere las tablas nuevas descritas en el esquema (ver notas
enviadas aparte): PRODUCTO_PRESENTACIONES, PRODUCTO_COMPONENTES,
PRODUCTO_ACTIVO, PRODUCTO_COMBO_ITEMS, y las columnas nuevas en
PRODUCTOS (categoria, mano_obra_es_porcentaje, costo_total,
precio_combo, descuento_combo). GASTOS_INDIRECTOS y PRODUCTO_GASTO
quedan reemplazadas por ACTIVOS/PRODUCTO_ACTIVO.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from ui.core.repositories.base.crud_repository import CRUDRepository


class ProductoRepository(CRUDRepository):
    TABLA = "PRODUCTOS"

    # Alias de columnas para que las filas devueltas ya calcen con las
    # claves que espera el resto de la UI (nombre, tipo, descripcion...)
    COLUMNAS_SELECT = """
        p.id_producto,
        p.nombre_producto AS nombre,
        p.tipo_producto AS tipo,
        p.categoria,
        p.receta_id,
        r.nombre_receta,
        p.descripcion_producto AS descripcion,
        p.peso,
        p.unidad_peso,
        p.costo_receta,
        p.mano_obra,
        p.tiempo_preparacion_minutos,
        p.empaques AS empaques_total,
        p.costos_indirectos AS costos_indirectos_total,
        p.costo_total,
        p.margen_porcentaje,
        p.precio_final,
        p.precio_combo,
        p.descuento_combo,
        p.activo
    """

    def __init__(self, conexion):
        super().__init__(conexion)

    # ============================================================
    # CREAR / ACTUALIZAR
    # ============================================================

    def crear(self, datos: Dict[str, Any]) -> int:
        query = """
            INSERT INTO PRODUCTOS
            (nombre_producto, tipo_producto, categoria, receta_id, descripcion_producto,
             costo_receta, mano_obra, empaques, costos_indirectos,
             costo_total, margen_porcentaje, precio_final, precio_combo, descuento_combo, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """
        cursor = self._cursor()
        cursor.execute(query, self._valores_principales(datos))
        nuevo_id = cursor.lastrowid
        self._guardar_relaciones(nuevo_id, datos)
        self._commit()
        return nuevo_id

    def actualizar(self, identificador: int, datos: Dict[str, Any]) -> bool:
        query = """
            UPDATE PRODUCTOS
            SET nombre_producto=%s, tipo_producto=%s, categoria=%s, receta_id=%s,
                descripcion_producto=%s, costo_receta=%s, mano_obra=%s,
                empaques=%s, costos_indirectos=%s,
                costo_total=%s, margen_porcentaje=%s, precio_final=%s,
                precio_combo=%s, descuento_combo=%s
            WHERE id_producto=%s
        """
        cursor = self._cursor()
        cursor.execute(query, self._valores_principales(datos) + (identificador,))
        actualizado = cursor.rowcount > 0

        # Las relaciones (presentaciones/componentes/activos/combo) se
        # reemplazan por completo: más simple y seguro que hacer diff.
        self._limpiar_relaciones(identificador)
        self._guardar_relaciones(identificador, datos)

        self._commit()
        return actualizado

    def _valores_principales(self, datos: Dict[str, Any]) -> Tuple:
        tipo = datos["tipo"]
        return (
            datos["nombre"],
            tipo,
            datos.get("categoria"),
            datos.get("id_receta") if tipo == "individual" else None,
            datos.get("descripcion", ""),
            datos.get("costo_receta", 0),
            datos.get("mano_obra", 0),
            datos.get("empaques_total", 0),
            datos.get("costos_indirectos_total", 0),
            datos.get("costo_total", 0),
            datos.get("margen_porcentaje", 40),
            datos.get("precio_final", 0),
            datos.get("precio_combo") if tipo == "combo" else None,
            datos.get("descuento_combo", 0) if tipo == "combo" else 0,
        )

    # ============================================================
    # RELACIONES (presentaciones / componentes / activos / combo)
    # ============================================================

    def _guardar_relaciones(self, id_producto: int, datos: Dict[str, Any]):
        tipo = datos["tipo"]

        if tipo == "individual":
            self._guardar_presentaciones(id_producto, datos.get("presentaciones", []))

        elif tipo == "elaborado":
            self._guardar_componentes(id_producto, datos.get("componentes", []))

        elif tipo == "combo":
            self._guardar_combo_items(id_producto, datos.get("productos_combo", []))

        # Empaques y costos indirectos aplican tanto a individual como
        # a elaborado (no a combo, que no tiene costeo propio).
        if tipo in ("individual", "elaborado"):
            self._guardar_activos(
                id_producto,
                datos.get("empaques", []),
                datos.get("costos_indirectos", []),
            )

    def _limpiar_relaciones(self, id_producto: int):
        cursor = self._cursor()
        cursor.execute("DELETE FROM PRODUCTO_PRESENTACIONES WHERE id_producto=%s", (id_producto,))
        cursor.execute("DELETE FROM PRODUCTO_COMPONENTES WHERE id_producto=%s", (id_producto,))
        cursor.execute("DELETE FROM PRODUCTO_ACTIVO WHERE id_producto=%s", (id_producto,))
        cursor.execute("DELETE FROM PRODUCTO_COMBO_ITEMS WHERE id_producto_combo=%s", (id_producto,))

    def _guardar_presentaciones(self, id_producto: int, presentaciones: List[Dict]):
        if not presentaciones:
            return
        cursor = self._cursor()
        for p in presentaciones:
            cursor.execute(
                "INSERT INTO PRODUCTO_PRESENTACIONES (id_producto, nombre, precio) VALUES (%s, %s, %s)",
                (id_producto, p["nombre"], p.get("precio", 0)),
            )

    def _guardar_componentes(self, id_producto: int, componentes: List[Dict]):
        """
        Cada componente llega como {"tipo": "ingrediente"|"producto"|"subproducto",
        "id": <int>, "cantidad": <float>}. "producto" y "subproducto" apuntan
        ambos a PRODUCTOS (un subproducto es, para el esquema, un producto más).
        """
        if not componentes:
            return
        cursor = self._cursor()
        for c in componentes:
            tipo_c = c["tipo"]
            id_ingrediente = c["id"] if tipo_c == "ingrediente" else None
            id_producto_componente = c["id"] if tipo_c in ("producto", "subproducto") else None
            cursor.execute(
                """
                INSERT INTO PRODUCTO_COMPONENTES
                    (id_producto, tipo_componente, id_ingrediente, id_producto_componente, cantidad_necesaria)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (id_producto, tipo_c, id_ingrediente, id_producto_componente, c.get("cantidad", 0)),
            )

    def _guardar_activos(self, id_producto: int, empaques: List[Dict], costos_indirectos: List[Dict]):
        cursor = self._cursor()
        for item in (empaques or []) + (costos_indirectos or []):
            cursor.execute(
                """
                INSERT INTO PRODUCTO_ACTIVO (id_producto, id_activo, cantidad_necesaria)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE cantidad_necesaria = cantidad_necesaria + VALUES(cantidad_necesaria)
                """,
                (id_producto, item["id_activo"], item.get("cantidad", 1)),
            )

    def _guardar_combo_items(self, id_producto_combo: int, productos_combo: List[Dict]):
        if not productos_combo:
            return
        cursor = self._cursor()
        for item in productos_combo:
            cursor.execute(
                """
                INSERT INTO PRODUCTO_COMBO_ITEMS (id_producto_combo, id_producto_incluido, cantidad)
                VALUES (%s, %s, %s)
                """,
                (id_producto_combo, item["id_producto"], item.get("cantidad", 1)),
            )

    # ============================================================
    # LECTURA
    # ============================================================

    def listar(self, filtro: Optional[str] = None, solo_activos: bool = True) -> List[Dict]:
        """
        Listado "liviano" para el catálogo: sin las relaciones hijas
        (no hacen falta para las tarjetas). Para el detalle completo
        de un producto usar obtener().
        """
        query = f"""
            SELECT {self.COLUMNAS_SELECT}
            FROM PRODUCTOS p
            LEFT JOIN RECETAS r ON p.receta_id = r.id_receta
        """
        condiciones = []
        params: List[Any] = []
        if filtro:
            condiciones.append("p.nombre_producto LIKE %s")
            params.append(f"{filtro}%")
        if solo_activos:
            condiciones.append("p.activo = TRUE")
        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)
        query += " ORDER BY p.id_producto DESC"
        cursor = self._cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def obtener(self, identificador: int) -> Optional[Dict]:
        query = f"""
            SELECT {self.COLUMNAS_SELECT}
            FROM PRODUCTOS p
            LEFT JOIN RECETAS r ON p.receta_id = r.id_receta
            WHERE p.id_producto = %s
        """
        cursor = self._cursor()
        cursor.execute(query, (identificador,))
        producto = cursor.fetchone()
        if not producto:
            return None

        producto["presentaciones"] = self._obtener_presentaciones(identificador)
        producto["componentes"] = self._obtener_componentes(identificador)
        empaques, costos_indirectos = self._obtener_activos(identificador)
        producto["empaques"] = empaques
        producto["costos_indirectos"] = costos_indirectos
        producto["productos_combo"] = self._obtener_combo_items(identificador)
        return producto

    def _obtener_presentaciones(self, id_producto: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT nombre, precio FROM PRODUCTO_PRESENTACIONES WHERE id_producto=%s",
            (id_producto,),
        )
        return cursor.fetchall()

    def _obtener_componentes(self, id_producto: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT
                pc.tipo_componente AS tipo,
                pc.cantidad_necesaria AS cantidad,
                COALESCE(pc.id_ingrediente, pc.id_producto_componente) AS id,
                COALESCE(i.nombre_ingrediente, pr.nombre_producto) AS nombre
            FROM PRODUCTO_COMPONENTES pc
            LEFT JOIN INGREDIENTES i ON pc.id_ingrediente = i.id_ingrediente
            LEFT JOIN PRODUCTOS pr ON pc.id_producto_componente = pr.id_producto
            WHERE pc.id_producto=%s
            """,
            (id_producto,),
        )
        return cursor.fetchall()

    def _obtener_activos(self, id_producto: int) -> Tuple[List[Dict], List[Dict]]:
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT a.tipo, a.nombre, a.id_activo AS id, pa.cantidad_necesaria AS cantidad
            FROM PRODUCTO_ACTIVO pa
            JOIN ACTIVOS a ON pa.id_activo = a.id_activo
            WHERE pa.id_producto=%s
            """,
            (id_producto,),
        )
        filas = cursor.fetchall()
        empaques = [f for f in filas if f["tipo"] == "empaque"]
        costos_indirectos = [f for f in filas if f["tipo"] == "costo_indirecto"]
        return empaques, costos_indirectos

    def _obtener_combo_items(self, id_producto_combo: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT pci.id_producto_incluido AS id_producto, pci.cantidad, p.nombre_producto AS nombre
            FROM PRODUCTO_COMBO_ITEMS pci
            JOIN PRODUCTOS p ON pci.id_producto_incluido = p.id_producto
            WHERE pci.id_producto_combo=%s
            """,
            (id_producto_combo,),
        )
        return cursor.fetchall()

    # ============================================================
    # ELIMINAR / BUSCAR
    # ============================================================

    def eliminar(self, identificador: int) -> bool:
        # Desactivar en lugar de eliminar
        query = "UPDATE PRODUCTOS SET activo = FALSE WHERE id_producto = %s"
        cursor = self._cursor()
        cursor.execute(query, (identificador,))
        self._commit()
        return cursor.rowcount > 0

    def buscar(self, texto: str) -> List[Dict]:
        return self.listar(texto)