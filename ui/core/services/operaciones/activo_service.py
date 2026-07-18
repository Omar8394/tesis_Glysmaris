from __future__ import annotations
from typing import Any, Dict, List, Optional
from ui.core.services.base.crud_service import CRUDService
from ui.core.services.base.service_result import ServiceResult
from ui.core.repositories.operaciones.activo_repository import ActivoRepository

class ActivoService(CRUDService):
    MODALIDADES_VALIDAS = ["por_unidad", "mensual", "por_hora", "por_uso", "porcentaje"]
    TIPOS_VALIDOS = ["empaque", "utensilio", "herramienta", "servicio", "transporte", "mobiliario", "otro"]
    ESTADOS_VALIDOS = ["activo", "inactivo"]
    # Tipos a los que sí les aplica calcular depreciación (requieren vida útil)
    TIPOS_DEPRECIABLES = ["utensilio", "herramienta", "mobiliario"]
    # Herramienta y mobiliario pueden ser propios (se deprecian) o
    # alquilados (no se deprecian, se pagan como costo recurrente).
    TIPOS_CON_MODO_ADQUISICION = ["herramienta", "mobiliario"]
    MODOS_ADQUISICION_VALIDOS = ["comprado", "alquilado"]

    def __init__(self, repositorio: ActivoRepository):
        self.repo = repositorio

    def validar(self, datos: Dict[str, Any]) -> ServiceResult:
        errores = {}

        nombre = datos.get("nombre", "").strip()
        if not nombre:
            errores["nombre"] = "El nombre es obligatorio."

        tipo = datos.get("tipo", "").strip()
        if not tipo:
            errores["tipo"] = "El tipo (categoría) es obligatorio."
        elif tipo not in self.TIPOS_VALIDOS:
            errores["tipo"] = f"Tipo no válido. Opciones: {', '.join(self.TIPOS_VALIDOS)}"

        modalidad = datos.get("modalidad_costo", "")
        if modalidad not in self.MODALIDADES_VALIDAS:
            errores["modalidad_costo"] = "Modalidad de costo no válida."

        costo = 0.0
        try:
            costo = float(datos.get("costo_unitario", 0))
            if costo < 0:
                errores["costo_unitario"] = "El costo no puede ser negativo."
        except (TypeError, ValueError):
            errores["costo_unitario"] = "El costo debe ser un número."

        try:
            stock = float(datos.get("stock_actual", 0))
            if stock < 0:
                errores["stock_actual"] = "La cantidad en inventario no puede ser negativa."
        except (TypeError, ValueError):
            errores["stock_actual"] = "La cantidad en inventario debe ser un número."

        estado = datos.get("estado", "activo")
        if estado not in self.ESTADOS_VALIDOS:
            errores["estado"] = "Estado no válido."

        # Modo de adquisición: solo aplica (y es obligatorio) para
        # herramienta/mobiliario, ya que pueden ser propios o alquilados.
        modo_adquisicion = datos.get("modo_adquisicion")
        if tipo in self.TIPOS_CON_MODO_ADQUISICION:
            if modo_adquisicion not in self.MODOS_ADQUISICION_VALIDOS:
                errores["modo_adquisicion"] = "Debes indicar si es comprado o alquilado."

        alquilado = (
            tipo in self.TIPOS_CON_MODO_ADQUISICION
            and modo_adquisicion == "alquilado"
        )

        vida_util = datos.get("vida_util_meses")
        # Un activo alquilado no es propio, así que no se deprecia: no se
        # exige vida útil aunque el tipo normalmente la requiera.
        requiere_vida_util = tipo in self.TIPOS_DEPRECIABLES and not alquilado
        if requiere_vida_util:
            if vida_util in (None, ""):
                errores["vida_util_meses"] = "La vida útil (en meses) es obligatoria para herramientas, utensilios y mobiliario comprados."
            else:
                try:
                    vida_util_val = int(vida_util)
                    if vida_util_val <= 0:
                        errores["vida_util_meses"] = "La vida útil debe ser mayor a cero."
                except (TypeError, ValueError):
                    errores["vida_util_meses"] = "La vida útil debe ser un número entero de meses."
        elif vida_util not in (None, ""):
            try:
                if int(vida_util) <= 0:
                    errores["vida_util_meses"] = "La vida útil debe ser mayor a cero."
            except (TypeError, ValueError):
                errores["vida_util_meses"] = "La vida útil debe ser un número entero de meses."

        try:
            valor_residual = float(datos.get("valor_residual", 0) or 0)
            if valor_residual < 0:
                errores["valor_residual"] = "El valor residual no puede ser negativo."
            elif valor_residual > costo:
                errores["valor_residual"] = "El valor residual no puede ser mayor al costo unitario."
        except (TypeError, ValueError):
            errores["valor_residual"] = "El valor residual debe ser un número."

        if errores:
            return ServiceResult.error("Errores de validación", errores)
        return ServiceResult.ok()

    def crear(self, datos: Dict[str, Any]) -> ServiceResult:
        validacion = self.validar(datos)
        if validacion.fallo:
            return validacion
        datos.setdefault("estado", "activo")
        datos.setdefault("unidad", "unidad")
        datos.setdefault("stock_actual", 0.0)
        activo = self.repo.crear(datos)
        return ServiceResult.ok("Recurso creado correctamente.", activo)

    def actualizar(self, identificador: Any, datos: Dict[str, Any]) -> ServiceResult:
        if not self.repo.existe(identificador):
            return ServiceResult.error("El recurso no existe.")
        validacion = self.validar(datos)
        if validacion.fallo:
            return validacion
        if self.repo.actualizar(identificador, datos):
            return ServiceResult.ok("Recurso actualizado.")
        return ServiceResult.error("Error al actualizar.")

    def eliminar(self, identificador: Any) -> ServiceResult:
        if not self.repo.existe(identificador):
            return ServiceResult.error("El recurso no existe.")
        if self.repo.eliminar(identificador):
            return ServiceResult.ok("Recurso eliminado.")
        return ServiceResult.error("Error al eliminar.")

    def obtener(self, identificador: Any) -> Optional[Dict]:
        return self.repo.obtener(identificador)

    def listar(self) -> List[Dict]:
        return self.repo.listar()

    def buscar(self, texto: str) -> List[Dict]:
        return self.repo.buscar(texto)

    def obtener_por_tipo(self, tipo: str) -> List[Dict]:
        """
        Devuelve los activos activos (habilitados) de un tipo específico.
        Usado por autocompletados como el buscador de empaques o costos
        indirectos dentro del wizard de productos.
        """
        if tipo not in self.TIPOS_VALIDOS:
            return []
        return self.repo.obtener_por_tipo(tipo)

    def cambiar_estado(self, identificador: Any, nuevo_estado: str) -> ServiceResult:
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            return ServiceResult.error("Estado no válido.")
        activo = self.obtener(identificador)
        if not activo:
            return ServiceResult.error("Recurso no encontrado.")
        activo["estado"] = nuevo_estado
        return self.actualizar(identificador, activo)

    def calcular_depreciacion_mensual(self, identificador: Any) -> float:
        """
        Devuelve la depreciación mensual de un activo (herramienta, utensilio
        o mobiliario) según su vida útil. Si el activo no tiene vida útil
        registrada (por ejemplo, un servicio como gas o agua, o una
        herramienta/mobiliario alquilado), devuelve 0.0 porque ese costo se
        maneja aparte como costo mensual directo.
        """
        activo = self.obtener(identificador)
        if not activo:
            return 0.0

        vida_util = activo.get("vida_util_meses")
        if not vida_util or int(vida_util) <= 0:
            return 0.0

        costo_unitario = float(activo.get("costo_unitario", 0) or 0)
        valor_residual = float(activo.get("valor_residual", 0) or 0)
        return (costo_unitario - valor_residual) / int(vida_util)

    def duplicar(self, identificador: Any) -> ServiceResult:
        original = self.obtener(identificador)
        if not original:
            return ServiceResult.error("Recurso no encontrado.")
        copia = original.copy()
        copia.pop("id_activo", None)
        copia["nombre"] = f"{copia['nombre']} (copia)"
        return self.crear(copia)