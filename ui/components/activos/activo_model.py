from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Activo:
    id_activo: Optional[int] = None
    nombre: str = ""
    tipo: str = ""                     # se usará como categoría (empaque, utensilio, etc.)
    costo_unitario: float = 0.0
    stock_actual: float = 0.0
    unidad: str = "unidad"
    descripcion: str = ""
    estado: str = "activo"             # activo / inactivo
    proveedor: str = ""
    codigo_interno: str = ""
    observaciones: str = ""
    modalidad_costo: str = "por_unidad"
    unidad_costo: str = ""
    periodo: str = ""
    vida_util_meses: Optional[int] = None
    valor_residual: float = 0.0
    fecha_registro: Optional[datetime] = field(default_factory=datetime.now)