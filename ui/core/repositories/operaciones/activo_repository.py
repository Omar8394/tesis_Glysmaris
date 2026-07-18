from __future__ import annotations
from typing import Any, Dict, List, Optional
from ui.core.repositories.base.crud_repository import CRUDRepository
from ui.components.activos.activo_model import Activo

class ActivoRepository(CRUDRepository):
    def __init__(self, conexion):
        super().__init__(conexion)

    def _to_dict(self, activo: Activo) -> Dict:
        return {
            "id_activo": activo.id_activo,
            "nombre": activo.nombre,
            "tipo": activo.tipo,
            "costo_unitario": activo.costo_unitario,
            "stock_actual": activo.stock_actual,
            "unidad": activo.unidad,
            "descripcion": activo.descripcion,
            "estado": activo.estado,
            "proveedor": activo.proveedor,
            "codigo_interno": activo.codigo_interno,
            "observaciones": activo.observaciones,
            "modalidad_costo": activo.modalidad_costo,
            "unidad_costo": activo.unidad_costo,
            "periodo": activo.periodo,
            "vida_util_meses": activo.vida_util_meses,
            "valor_residual": activo.valor_residual,
            "fecha_registro": activo.fecha_registro,
        }

    def _from_dict(self, data: Dict) -> Activo:
        return Activo(**data)

    def crear(self, datos: Dict[str, Any]) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute("""
            INSERT INTO ACTIVOS
                (nombre, tipo, costo_unitario, stock_actual, unidad,
                 descripcion, estado, proveedor, codigo_interno,
                 observaciones, modalidad_costo, unidad_costo, periodo,
                 vida_util_meses, valor_residual)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos["nombre"], datos.get("tipo", ""), datos.get("costo_unitario", 0.0),
            datos.get("stock_actual", 0.0), datos.get("unidad", "unidad"),
            datos.get("descripcion", ""), datos.get("estado", "activo"),
            datos.get("proveedor", ""), datos.get("codigo_interno", ""),
            datos.get("observaciones", ""), datos.get("modalidad_costo", "por_unidad"),
            datos.get("unidad_costo", ""), datos.get("periodo", ""),
            datos.get("vida_util_meses"), datos.get("valor_residual", 0.0)
        ))
        self._commit()
        nuevo_id = cursor.lastrowid
        return self.obtener(nuevo_id)

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> bool:
        cursor = self._cursor()
        cursor.execute("""
            UPDATE ACTIVOS SET
                nombre=%s, tipo=%s, costo_unitario=%s, stock_actual=%s,
                unidad=%s, descripcion=%s, estado=%s, proveedor=%s,
                codigo_interno=%s, observaciones=%s, modalidad_costo=%s,
                unidad_costo=%s, periodo=%s, vida_util_meses=%s, valor_residual=%s
            WHERE id_activo=%s
        """, (
            datos["nombre"], datos.get("tipo", ""), datos.get("costo_unitario", 0.0),
            datos.get("stock_actual", 0.0), datos.get("unidad", "unidad"),
            datos.get("descripcion", ""), datos.get("estado", "activo"),
            datos.get("proveedor", ""), datos.get("codigo_interno", ""),
            datos.get("observaciones", ""), datos.get("modalidad_costo", "por_unidad"),
            datos.get("unidad_costo", ""), datos.get("periodo", ""),
            datos.get("vida_util_meses"), datos.get("valor_residual", 0.0),
            identificador
        ))
        self._commit()
        return cursor.rowcount > 0

    def eliminar(self, identificador: Any) -> bool:
        cursor = self._cursor()
        cursor.execute("DELETE FROM ACTIVOS WHERE id_activo=%s", (identificador,))
        self._commit()
        return cursor.rowcount > 0

    def obtener(self, identificador: Any) -> Optional[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM ACTIVOS WHERE id_activo=%s", (identificador,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def listar(self) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("SELECT * FROM ACTIVOS")
        return [dict(row) for row in cursor.fetchall()]

    def buscar(self, texto: str) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute("""
            SELECT * FROM ACTIVOS
            WHERE nombre LIKE %s OR tipo LIKE %s OR descripcion LIKE %s
        """, (f"%{texto}%", f"%{texto}%", f"%{texto}%"))
        return [dict(row) for row in cursor.fetchall()]

    def obtener_por_tipo(self, tipo: str) -> List[Dict]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM ACTIVOS WHERE tipo=%s AND estado='activo' ORDER BY nombre",
            (tipo,)
        )
        return [dict(row) for row in cursor.fetchall()]