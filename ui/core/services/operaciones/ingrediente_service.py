"""
============================================================
Sistema La Dulce Tía

Archivo:
    ingrediente_service.py

Responsabilidad:
    Lógica de negocio de los ingredientes.
============================================================
"""

# ui/core/services/operaciones/ingrediente_service.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
from ui.core.services.base.crud_service import CRUDService
from ui.core.services.base.service_result import ServiceResult
from ui.core.repositories.operaciones.ingrediente_repository import IngredienteRepository

class IngredienteService(CRUDService):
    # ✅ Traduce la etiqueta que muestra el diálogo (RadioGroup) al valor
    # real permitido por el ENUM de PERDIDAS_INVENTARIO. Cualquier motivo
    # no listado (incluido "Otro: <texto libre>") cae en 'otro'.
    MOTIVOS_ENUM = {
        "Caducado": "caducidad",
        "Deteriorado": "daño",
        "Error de inventario": "error_registro",
    }

    def __init__(self, repository: IngredienteRepository):
        self._repository = repository

    # ---------- CRUD obligatorios ----------
    def listar(self, filtro: Optional[str] = None) -> ServiceResult:
        try:
            datos = self._repository.listar(filtro)
            return ServiceResult.ok(datos=datos)
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def obtener(self, identificador: int) -> ServiceResult:
        try:
            dato = self._repository.obtener(identificador)
            if not dato:
                return ServiceResult.error("Ingrediente no encontrado.")
            return ServiceResult.ok(datos=dato)
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def obtener_por_nombre(self, nombre: str) -> ServiceResult:
        """✅ Para detectar si ya existe un ingrediente con ese nombre
        (sin importar mayúsculas/minúsculas) antes de crear uno nuevo.
        Devuelve exito=True con datos=None si simplemente no existe."""
        try:
            if not nombre or not nombre.strip():
                return ServiceResult.ok(datos=None)
            dato = self._repository.obtener_por_nombre(nombre)
            return ServiceResult.ok(datos=dato)
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def buscar_nombres(self, texto: str) -> list[str]:
        """✅ Para autocompletado: nombres existentes que coincidan con el
        texto escrito, sin duplicados."""
        try:
            if not texto or not texto.strip():
                return []
            datos = self._repository.listar(texto)
            return sorted({d["nombre_ingrediente"] for d in datos if d.get("nombre_ingrediente")})
        except Exception:
            return []

    def crear(self, datos: Dict[str, Any]) -> ServiceResult:
        try:
            valido, msg = self.validar(datos)
            if not valido:
                return ServiceResult.error(msg)
            
            # Buscamos si el ingrediente base ya existe en el catálogo maestro
            # (Usando el método que ya tienes programado en tu capa de datos)
            resultado_existente = self.obtener_por_nombre(datos["nombre"])
            
            if resultado_existente.exito and resultado_existente.datos:
                # Caso A: El ingrediente ya existe. Conseguimos su ID y creamos un lote nuevo
                id_ingrediente = resultado_existente.datos["id_ingrediente"]
                self._repository.crear_lote(id_ingrediente, datos)
                return ServiceResult.ok(mensaje="Se ha registrado un nuevo lote para el ingrediente existente.")
            else:
                # Caso B: Es un ingrediente 100% nuevo. Primero se registra en la tabla MAESTRA
                id_ingrediente = self._repository.crear(datos)
                # Inmediatamente después, se registra su primer LOTE vinculado a ese ID
                self._repository.crear_lote(id_ingrediente, datos)
                return ServiceResult.ok(mensaje="Ingrediente y lote inicial creados exitosamente.")
                
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def actualizar(self, identificador: int, datos: Dict[str, Any]) -> ServiceResult:
        valido, msg = self.validar(datos)
        if not valido:
            return ServiceResult.error(msg)
        try:
            actualizado = self._repository.actualizar(identificador, datos)
            if not actualizado:
                return ServiceResult.error("No se pudo actualizar.")
            return ServiceResult.ok(mensaje="Ingrediente actualizado.")
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def eliminar(self, identificador: int) -> ServiceResult:
        try:
            eliminado = self._repository.eliminar(identificador)
            if not eliminado:
                return ServiceResult.error("No se pudo eliminar.")
            return ServiceResult.ok(mensaje="Ingrediente eliminado.")
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def obtener_lote(self, id_lote: int) -> ServiceResult:
        """✅ Para editar: trae un lote puntual con los datos del ingrediente
        maestro ya unidos, usando el id_lote real seleccionado en la tabla."""
        try:
            dato = self._repository.obtener_lote(id_lote)
            if not dato:
                return ServiceResult.error("Lote no encontrado.")
            return ServiceResult.ok(datos=dato)
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def actualizar_lote(self, id_lote: int, datos: Dict[str, Any]) -> ServiceResult:
        """✅ Reemplaza al viejo 'actualizar()' para el flujo de edición real
        de la UI: valida igual que al crear (stock/costo/fechas incluidos)
        y actualiza tanto el ingrediente maestro como el lote puntual."""
        valido, msg = self.validar(datos)
        if not valido:
            return ServiceResult.error(msg)
        try:
            actualizado = self._repository.actualizar_lote(id_lote, datos)
            if not actualizado:
                return ServiceResult.error("No se pudo actualizar.")
            return ServiceResult.ok(mensaje="Ingrediente actualizado.")
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def registrar_perdida(self, id_lote: int, cantidad: float, motivo_ui: str) -> ServiceResult:
        """✅ Reemplaza al viejo 'eliminar_lote' (nunca representó lo que la
        UI real necesita). Registra una merma total o parcial de un lote:
        - cantidad es OBLIGATORIA y debe ser > 0 (el diálogo ya lo valida,
          pero el service no confía solo en eso).
        - motivo_ui llega tal cual lo eligió el usuario en el RadioGroup
          (ej. "Caducado", "Error de inventario", "Otro: se mojó la bolsa").
          Acá se mapea al valor de ENUM real; todo lo no reconocido cae
          en 'otro', y el texto completo se guarda en 'descripcion' para
          no perder el detalle (importante para "Otro: ...").
        """
        try:
            if cantidad is None or cantidad <= 0:
                return ServiceResult.error("Debe indicar una cantidad mayor a 0.")
            if not motivo_ui or not motivo_ui.strip():
                return ServiceResult.error("Debe seleccionar un motivo.")

            lote = self._repository.obtener_lote(id_lote)
            if not lote:
                return ServiceResult.error("Lote no encontrado.")

            stock_actual = float(lote["stock_actual"])
            if cantidad > stock_actual:
                return ServiceResult.error(
                    f"No puede eliminar más de {stock_actual:.2f} (stock disponible del lote)."
                )

            motivo_enum = self.MOTIVOS_ENUM.get(motivo_ui, "otro")
            es_perdida_total = cantidad >= stock_actual

            registrado = self._repository.registrar_perdida(
                id_lote=id_lote,
                cantidad=cantidad,
                motivo=motivo_enum,
                descripcion=motivo_ui,
            )
            if not registrado:
                return ServiceResult.error("No se pudo registrar la pérdida.")

            if motivo_enum == "error_registro":
                mensaje = (
                    "Se eliminó el registro erróneo. Si vuelves a cargar este "
                    "ingrediente, se registrará como uno nuevo."
                )
            else:
                mensaje = (
                    "Se eliminó el lote por completo."
                    if es_perdida_total
                    else f"Se registró la pérdida de {cantidad:.2f} unidades del lote."
                )
            return ServiceResult.ok(mensaje=mensaje)
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def buscar(self, texto: str) -> ServiceResult:
        try:
            datos = self._repository.buscar(texto)
            return ServiceResult.ok(datos=datos)
        except Exception as ex:
            return ServiceResult.error(str(ex))

    # ---------- Descuento/devolución de stock (usado por Producción) ----------

    def verificar_disponibilidad(self, id_ingrediente: int, cantidad_necesaria: float) -> ServiceResult:
        """Compara el stock total disponible (suma de lotes vigentes) contra
        la cantidad necesaria. No descuenta nada, solo informa."""
        try:
            disponible = self._repository.obtener_stock(id_ingrediente)
            cantidad_necesaria = float(cantidad_necesaria)
            return ServiceResult.ok(datos={
                "disponible": disponible,
                "necesario": cantidad_necesaria,
                "faltante": max(0.0, cantidad_necesaria - disponible),
                "suficiente": disponible >= cantidad_necesaria,
            })
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def descontar_stock(self, id_ingrediente: int, cantidad: float) -> ServiceResult:
        """Descuenta 'cantidad' en PEPS entre los lotes del ingrediente.
        datos trae la lista de lotes afectados (necesaria para poder
        devolver el stock si la orden de producción se cancela)."""
        try:
            if cantidad <= 0:
                return ServiceResult.ok(datos=[])
            afectados = self._repository.descontar_stock_peps(id_ingrediente, cantidad)
            if afectados is None:
                return ServiceResult.error("Stock insuficiente para descontar.")
            return ServiceResult.ok(datos=afectados)
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def devolver_stock(self, id_lote: int, cantidad: float) -> ServiceResult:
        """Repone 'cantidad' a un lote específico (cancelación de una orden
        de producción que ya había descontado inventario)."""
        try:
            if cantidad <= 0:
                return ServiceResult.ok()
            ok = self._repository.devolver_stock_lote(id_lote, cantidad)
            if not ok:
                return ServiceResult.error("No se pudo devolver el stock (lote no encontrado).")
            return ServiceResult.ok()
        except Exception as ex:
            return ServiceResult.error(str(ex))

    def validar(self, datos: Dict[str, Any]) -> tuple[bool, str]:
        if not datos.get("nombre", "").strip():
            return False, "El nombre es obligatorio."
        if datos.get("stock", 0) < 0:
            return False, "El stock no puede ser negativo."
        if datos.get("costo", 0) < 0:
            return False, "El costo no puede ser negativo."
        # ✅ Antes no se validaba la fecha en absoluto, lo que permitía
        # guardar ingredientes sin fecha de caducidad ni de ingreso.
        if not datos.get("fecha_ingreso"):
            return False, "La fecha de ingreso es obligatoria."
        if not datos.get("caducidad"):
            return False, "La fecha de caducidad es obligatoria."
        if datos.get("fecha_ingreso") and datos.get("caducidad"):
            if datos["caducidad"] < datos["fecha_ingreso"]:
                return False, "La fecha de caducidad no puede ser anterior a la fecha de ingreso."
        # más validaciones si se requieren
        return True, ""

    # ---------- Métodos específicos ----------
    def verificar_stock_para_recetas(self, identificador: int) -> ServiceResult:
        try:
            recetas = self._repository.obtener_recetas(identificador)
            if not recetas:
                return ServiceResult.ok(datos=[])
            stock = self._repository.obtener_stock(identificador)
            faltantes = []
            for receta in recetas:
                if stock < receta["cantidad_necesaria"]:
                    faltantes.append({
                        "id_receta": receta["id_receta"],
                        "nombre": receta["nombre_receta"],
                        "necesario": receta["cantidad_necesaria"],
                        "unidad": receta["unidad"]
                    })
            return ServiceResult.ok(datos=faltantes)
        except Exception as ex:
            return ServiceResult.error(str(ex))