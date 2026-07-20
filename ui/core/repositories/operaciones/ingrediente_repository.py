"""
============================================================
Sistema La Dulce Tía

Archivo:
    ingrediente_repository.py

Responsabilidad:
    Acceso a datos de la tabla INGREDIENTES.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

# ui/core/repositories/operaciones/ingrediente_repository.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ui.core.repositories.base.crud_repository import CRUDRepository

class IngredienteRepository(CRUDRepository):
    TABLA = "INGREDIENTES"

    def __init__(self, conexion):
        super().__init__(conexion)

    def crear(self, datos: Dict[str, Any]) -> int:
        query = """
            INSERT INTO INGREDIENTES
            (nombre_ingrediente, unidad_medida, categoria, perecedero, refrigerado, 
             descripcion, contenido_unidad)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            datos["nombre"], datos["unidad"], datos["categoria"],
            datos.get("perecedero", False), datos.get("refrigerado", False),
            datos.get("descripcion"), datos.get("contenido_unidad")
        )
        cursor = self._cursor()
        cursor.execute(query, valores)
        self._commit()
        return cursor.lastrowid
    
    def crear_lote(self, id_ingrediente: int, datos: Dict[str, Any]) -> bool:
        query = """
            INSERT INTO LOTES_INVENTARIO
            (id_ingrediente, stock_inicial, stock_actual, costo_unitario, fecha_ingreso, fecha_caducidad)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (
            id_ingrediente, datos["stock"], datos["stock"], datos["costo"],
            datos.get("fecha_ingreso"), datos.get("caducidad")
        )
        cursor = self._cursor()
        cursor.execute(query, valores)
        self._commit()
        return cursor.rowcount > 0

    def listar(self, filtro: Optional[str] = None) -> List[Dict]:
        # Hacemos JOIN para pintar cada lote individual en tu tabla de Flet.
        # ✅ id_lote e id_ingrediente viajan SEPARADOS (antes se pisaba
        # id_ingrediente con el alias de id_lote, y todo el resto del código
        # terminaba operando por error sobre el lote como si fuera el
        # ingrediente maestro).
        query = """
            SELECT l.id_lote, i.id_ingrediente, i.nombre_ingrediente, l.stock_actual, 
                   i.unidad_medida, l.costo_unitario, l.fecha_caducidad, i.categoria, 
                   i.perecedero, i.refrigerado, l.fecha_ingreso, i.descripcion, i.contenido_unidad
            FROM LOTES_INVENTARIO l
            JOIN INGREDIENTES i ON l.id_ingrediente = i.id_ingrediente
            WHERE l.stock_actual > 0
        """
        valores = []
        if filtro:
            query += " AND i.nombre_ingrediente LIKE %s"
            valores.append(f"{filtro}%")
            
        # PEPS: El lote que vence primero va arriba de la tabla
        query += " ORDER BY l.fecha_caducidad ASC"
        
        cursor = self._cursor()
        cursor.execute(query, valores)
        return cursor.fetchall()

    def obtener_lote(self, id_lote: int) -> Optional[Dict]:
        """✅ Trae un lote puntual con sus datos de ingrediente maestro unidos,
        para poblar el formulario de edición. Usa id_lote, que es lo que
        realmente identifica cada fila de la tabla en pantalla."""
        query = """
            SELECT l.id_lote, i.id_ingrediente, i.nombre_ingrediente, l.stock_actual,
                   i.unidad_medida, l.costo_unitario, l.fecha_caducidad, i.categoria,
                   i.perecedero, i.refrigerado, l.fecha_ingreso, i.descripcion, i.contenido_unidad
            FROM LOTES_INVENTARIO l
            JOIN INGREDIENTES i ON l.id_ingrediente = i.id_ingrediente
            WHERE l.id_lote = %s
        """
        cursor = self._cursor()
        cursor.execute(query, (id_lote,))
        return cursor.fetchone()

    def obtener(self, identificador: int) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM INGREDIENTES WHERE id_ingrediente = %s", (identificador,))
        return cursor.fetchone()

    def obtener_por_nombre(self, nombre: str) -> Optional[Dict]:
        """✅ Busca por nombre exacto SIN distinguir mayúsculas/minúsculas
        (para detectar duplicados como 'Harina' vs 'harina')."""
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM INGREDIENTES WHERE LOWER(nombre_ingrediente) = LOWER(%s)",
            (nombre.strip(),),
        )
        return cursor.fetchone()

    def actualizar(self, identificador: int, datos: Dict[str, Any]) -> bool:
        """
        Actualiza SOLO los campos del ingrediente MAESTRO (INGREDIENTES).
        ✅ Antes esta query mezclaba columnas que ya no existen en
        INGREDIENTES (stock_actual, costo_unitario, fecha_caducidad,
        fecha_ingreso) — esas viven en LOTES_INVENTARIO desde que se
        implementó FIFO. Para tocar un lote puntual usar actualizar_lote().
        """
        query = """
            UPDATE INGREDIENTES SET
                nombre_ingrediente=%s, unidad_medida=%s, categoria=%s,
                perecedero=%s, refrigerado=%s, descripcion=%s, contenido_unidad=%s
            WHERE id_ingrediente=%s
        """
        valores = (
            datos["nombre"], datos["unidad"], datos.get("categoria"),
            datos.get("perecedero", False), datos.get("refrigerado", False),
            datos.get("descripcion"), datos.get("contenido_unidad"),
            identificador,
        )
        cursor = self._cursor()
        cursor.execute(query, valores)
        self._commit()
        return cursor.rowcount > 0

    def actualizar_lote(self, id_lote: int, datos: Dict[str, Any]) -> bool:
        """✅ Nuevo: actualiza un lote puntual (stock/costo/fechas) en
        LOTES_INVENTARIO, y de paso los campos maestros en INGREDIENTES
        (nombre, unidad, categoría, etc.), ya que el formulario de edición
        edita ambas cosas a la vez. Recibe id_lote, que es el ID real que
        identifica la fila seleccionada en la tabla."""
        cursor = self._cursor()

        cursor.execute(
            "SELECT id_ingrediente FROM LOTES_INVENTARIO WHERE id_lote = %s",
            (id_lote,),
        )
        fila = cursor.fetchone()
        if not fila:
            return False
        id_ingrediente = fila["id_ingrediente"]

        cursor.execute(
            """
            UPDATE INGREDIENTES SET
                nombre_ingrediente=%s, unidad_medida=%s, categoria=%s,
                perecedero=%s, refrigerado=%s, descripcion=%s, contenido_unidad=%s
            WHERE id_ingrediente=%s
            """,
            (
                datos["nombre"], datos["unidad"], datos.get("categoria"),
                datos.get("perecedero", False), datos.get("refrigerado", False),
                datos.get("descripcion"), datos.get("contenido_unidad"),
                id_ingrediente,
            ),
        )

        cursor.execute(
            """
            UPDATE LOTES_INVENTARIO SET
                stock_actual=%s, costo_unitario=%s, fecha_ingreso=%s, fecha_caducidad=%s
            WHERE id_lote=%s
            """,
            (
                datos["stock"], datos["costo"],
                datos.get("fecha_ingreso"), datos.get("caducidad"),
                id_lote,
            ),
        )

        self._commit()
        return cursor.rowcount > 0

    def registrar_perdida(
        self,
        id_lote: int,
        cantidad: float,
        motivo: str,
        descripcion: str = "",
    ) -> bool:
        """
        Registra una merma/baja de un lote. Siempre guarda una fila en
        PERDIDAS_INVENTARIO con nombre_ingrediente/unidad_medida "congelados"
        en el momento (no solo el id_lote), para que el historial de
        pérdidas siga siendo útil para reportes aunque el lote (o el
        ingrediente) se borre después.

        Hay dos comportamientos según el motivo:
        - 'error_registro' (el usuario cargó el lote por error, no es una
          merma real): se elimina el lote POR COMPLETO de LOTES_INVENTARIO
          (no solo se pone stock en 0), sin importar la cantidad recibida.
          Si ese era el último lote del ingrediente, también se elimina el
          ingrediente maestro, para que si se vuelve a cargar más adelante
          se trate como uno nuevo en vez de ofrecer "agregar otro lote".
        - cualquier otro motivo (caducidad, daño, otro): comportamiento
          original -- se descuenta 'cantidad' de stock_actual (con piso en
          0) y el lote se mantiene, para conservar el historial real de
          inventario físico.
        """
        cursor = self._cursor()

        cursor.execute(
            """
            SELECT l.id_ingrediente, l.stock_actual, l.costo_unitario,
                   i.nombre_ingrediente, i.unidad_medida
            FROM LOTES_INVENTARIO l
            JOIN INGREDIENTES i ON i.id_ingrediente = l.id_ingrediente
            WHERE l.id_lote = %s
            """,
            (id_lote,),
        )
        lote = cursor.fetchone()
        if not lote:
            return False

        id_ingrediente = lote["id_ingrediente"]
        stock_actual = float(lote["stock_actual"])
        costo_unitario = float(lote["costo_unitario"])

        # Un error de registro siempre se corrige eliminando el lote
        # completo, sin importar qué cantidad haya tipeado el usuario.
        if motivo == "error_registro":
            cantidad = stock_actual
        else:
            cantidad = min(cantidad, stock_actual)  # nunca descontar más de lo que hay

        costo_perdida = round(cantidad * costo_unitario, 2)

        cursor.execute(
            """
            INSERT INTO PERDIDAS_INVENTARIO
                (id_lote, nombre_ingrediente, unidad_medida, cantidad, motivo, descripcion, costo_perdida)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_lote, lote["nombre_ingrediente"], lote["unidad_medida"],
                cantidad, motivo, descripcion, costo_perdida,
            ),
        )

        if motivo == "error_registro":
            cursor.execute("DELETE FROM LOTES_INVENTARIO WHERE id_lote = %s", (id_lote,))
        else:
            cursor.execute(
                "UPDATE LOTES_INVENTARIO SET stock_actual = stock_actual - %s WHERE id_lote = %s",
                (cantidad, id_lote),
            )

        self._commit()

        if motivo == "error_registro":
            self._eliminar_ingrediente_si_quedo_sin_lotes(id_ingrediente)

        return True

    def _eliminar_ingrediente_si_quedo_sin_lotes(self, id_ingrediente: int) -> None:
        """
        Tras eliminar un lote por error de registro, si no le quedan más
        lotes a ese ingrediente, se borra también el ingrediente maestro.
        Si el ingrediente sigue en uso (le queda otro lote, o está
        referenciado en alguna receta), simplemente se deja como está --
        no es un error, solo significa que el ingrediente sigue vigente.
        """
        cursor = self._cursor()
        cursor.execute(
            "SELECT COUNT(*) AS total FROM LOTES_INVENTARIO WHERE id_ingrediente = %s",
            (id_ingrediente,),
        )
        if cursor.fetchone()["total"] > 0:
            return
        try:
            cursor.execute("DELETE FROM INGREDIENTES WHERE id_ingrediente = %s", (id_ingrediente,))
            self._commit()
        except Exception:
            # Referenciado en alguna receta u otra tabla -- se deja como está.
            pass

    def eliminar(self, identificador: int) -> bool:
        cursor = self._cursor()
        cursor.execute("DELETE FROM INGREDIENTES WHERE id_ingrediente = %s", (identificador,))
        self._commit()
        return cursor.rowcount > 0

    def buscar(self, texto: str) -> List[Dict]:
        return self.listar(texto)

    # Métodos específicos (opcionales, pero útiles)
    def obtener_recetas(self, identificador: int) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("""
            SELECT r.id_receta, r.nombre_receta, ri.cantidad_necesaria, ri.unidad
            FROM RECETA_INGREDIENTES ri
            JOIN RECETAS r ON ri.id_receta = r.id_receta
            WHERE ri.id_ingrediente = %s
        """, (identificador,))
        return cursor.fetchall()

    def obtener_stock(self, identificador: int) -> float:
        """✅ Antes consultaba INGREDIENTES.stock_actual, columna que ya no
        existe ahí (se movió a LOTES_INVENTARIO). Además, con FIFO el stock
        real disponible de un ingrediente es la SUMA de todos sus lotes
        vigentes, no un único valor. Recibe id_ingrediente (el maestro),
        que es lo que efectivamente guarda RECETA_INGREDIENTES."""
        cursor = self._cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(stock_actual), 0) AS total FROM LOTES_INVENTARIO WHERE id_ingrediente = %s",
            (identificador,),
        )
        row = cursor.fetchone()
        return float(row["total"]) if row else 0.0

    def descontar_stock_peps(self, id_ingrediente: int, cantidad: float) -> Optional[List[Dict]]:
        """
        Descuenta 'cantidad' del ingrediente en orden PEPS (el lote que
        vence primero se consume primero), usado al iniciar una orden de
        producción.

        Devuelve la lista de lotes afectados
        [{"id_lote": ..., "cantidad_descontada": ...}, ...] para poder
        revertir el descuento más adelante si la orden se cancela (ver
        devolver_stock_lote). Si el stock total disponible es menor que
        'cantidad', no descuenta nada y devuelve None.
        """
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT id_lote, stock_actual FROM LOTES_INVENTARIO
            WHERE id_ingrediente = %s AND stock_actual > 0
            ORDER BY fecha_caducidad ASC
            """,
            (id_ingrediente,),
        )
        lotes = cursor.fetchall()

        disponible = sum(float(l["stock_actual"]) for l in lotes)
        if disponible < cantidad:
            return None

        restante = cantidad
        afectados: List[Dict] = []
        for lote in lotes:
            if restante <= 0:
                break
            stock_lote = float(lote["stock_actual"])
            tomar = min(stock_lote, restante)
            cursor.execute(
                "UPDATE LOTES_INVENTARIO SET stock_actual = stock_actual - %s WHERE id_lote = %s",
                (tomar, lote["id_lote"]),
            )
            afectados.append({"id_lote": lote["id_lote"], "cantidad_descontada": tomar})
            restante -= tomar

        self._commit()
        return afectados

    def devolver_stock_lote(self, id_lote: int, cantidad: float) -> bool:
        """
        Repone 'cantidad' al stock_actual de un lote específico. Se usa al
        cancelar una orden de producción que ya había descontado inventario
        (estado 'en_proceso'): se repone exactamente a los mismos lotes de
        los que se tomó, usando el registro de PRODUCCION_INGREDIENTES_RESERVADOS.
        """
        cursor = self._cursor()
        cursor.execute(
            "UPDATE LOTES_INVENTARIO SET stock_actual = stock_actual + %s WHERE id_lote = %s",
            (cantidad, id_lote),
        )
        self._commit()
        return cursor.rowcount > 0