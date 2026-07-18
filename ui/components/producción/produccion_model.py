from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional

@dataclass
class OrdenProduccion:
    id_orden: Optional[int] = None
    numero_orden: str = ""
    fecha_creacion: Optional[datetime] = field(default_factory=datetime.now)
    fecha_planificada: date = None
    hora_estimada: Optional[time] = None
    prioridad: str = "media"  # baja, media, alta, urgente
    responsable: str = ""
    estado: str = "pendiente"  # pendiente, en_proceso, finalizada, cancelada
    notas: str = ""
    costo_estimado: float = 0.0
    costo_real: float = 0.0
    tiempo_estimado_minutos: int = 0
    tiempo_real_minutos: int = 0
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    creado_por: str = ""

@dataclass
class DetalleProduccion:
    id_detalle: Optional[int] = None
    id_orden: int = 0
    id_producto: int = 0
    id_presentacion: Optional[int] = None
    cantidad_planificada: int = 1
    cantidad_obtenida: int = 0
    precio_final: float = 0.0
    modificaciones: str = ""
    costo_calculado: float = 0.0
    rendimiento_porcentaje: float = 0.0
    disponible_venta: bool = True

@dataclass
class MermaProduccion:
    id_merma: Optional[int] = None
    id_orden: int = 0
    id_detalle: Optional[int] = None
    id_producto: Optional[int] = None
    cantidad: float = 0.0
    tipo_merma: str = "no_recuperable"  # recuperable, no_recuperable
    motivo: str = "otro"  # quemado, rotura, contaminacion, error_preparacion, decoracion, otro
    descripcion: str = ""
    costo_asociado: float = 0.0
    fecha_registro: Optional[datetime] = field(default_factory=datetime.now)

@dataclass
class SubproductoProduccion:
    id_subproducto: Optional[int] = None
    id_merma: int = 0
    id_detalle: Optional[int] = None
    id_producto_subproducto: int = 0
    cantidad: float = 0.0
    unidad: str = ""
    fecha_registro: Optional[datetime] = field(default_factory=datetime.now)

@dataclass
class ReservaIngrediente:
    id_reserva: Optional[int] = None
    id_orden: int = 0
    id_detalle: int = 0
    id_producto: int = 0
    id_ingrediente: int = 0
    id_lote: Optional[int] = None
    cantidad_reservada: float = 0.0
    cantidad_consumida: float = 0.0
    cantidad_devuelta: float = 0.0
    fecha_reserva: Optional[datetime] = field(default_factory=datetime.now)

@dataclass
class ReservaActivo:
    id_reserva_activo: Optional[int] = None
    id_orden: int = 0
    id_detalle: int = 0
    id_producto: int = 0
    id_activo: int = 0
    cantidad_reservada: float = 0.0
    cantidad_consumida: float = 0.0
    fecha_reserva: Optional[datetime] = field(default_factory=datetime.now)

@dataclass
class CostoProduccion:
    id_costo: Optional[int] = None
    id_orden: int = 0
    id_detalle: Optional[int] = None
    tipo: str = "ingrediente"  # ingrediente, activo, mano_obra, costo_indirecto, otro
    descripcion: str = ""
    valor_estimado: float = 0.0
    valor_real: float = 0.0
    fecha_registro: Optional[datetime] = field(default_factory=datetime.now)

@dataclass
class AnalisisProduccion:
    id_analisis: Optional[int] = None
    id_orden: int = 0
    id_producto: int = 0
    cantidad_solicitada: int = 0
    cantidad_posible: int = 0
    resultado: str = "completo"  # completo, parcial, inviable
    fecha_analisis: Optional[datetime] = field(default_factory=datetime.now)

@dataclass
class AnalisisFaltante:
    id_faltante: Optional[int] = None
    id_analisis: int = 0
    id_ingrediente: Optional[int] = None
    id_activo: Optional[int] = None
    necesario: float = 0.0
    disponible: float = 0.0
    faltante: float = 0.0

@dataclass
class HistorialEstado:
    id_historial: Optional[int] = None
    id_orden: int = 0
    estado_anterior: str = ""
    estado_nuevo: str = ""
    fecha_cambio: Optional[datetime] = field(default_factory=datetime.now)
    usuario: str = ""
    observaciones: str = ""