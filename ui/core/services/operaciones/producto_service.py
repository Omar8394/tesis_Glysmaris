"""
Servicio de Productos.

Calcula costo y precio final para los 3 tipos de producto:

    - individual: costo = receta + empaques + costos indirectos + mano de obra
    - elaborado:  costo = componentes (ingrediente/producto/subproducto) +
                  empaques + costos indirectos + mano de obra
    - combo:      precio = precio_combo manual con descuento_combo aplicado
                  (no lleva margen; el costo mostrado es informativo, la
                  suma del precio_final de los productos incluidos)

La mano de obra y los costos indirectos ya no se cargan a mano: llegan
calculados desde tiempo_preparacion x tasas por hora (PARAMETROS_NEGOCIO
/ Mi Negocio). Quien arma `datos` (típicamente ProductoWizard) resuelve
esa multiplicación antes de llamar; el service solo:
    - suma "mano_obra" como monto fijo, y
    - usa "costos_indirectos_monto" como override directo del total de
      costos indirectos si viene presente (si no, cae al cálculo viejo
      desde una lista de activos en "costos_indirectos", por compatibilidad).

✅ Normalización de claves (ver `_normalizar_alias`):
   ProductoWizard y ProductoRepository no siempre usan exactamente las
   mismas claves entre sí (p.ej. el wizard guarda la lista de productos
   del combo bajo "productos", el repositorio bajo "productos_combo";
   ProductoRepository.obtener() devuelve "receta_id", pero crear()/
   actualizar() esperan "id_receta"). En vez de exigirle a cada llamador
   (ProductoModule) que arme el dict "perfecto", el service normaliza
   los alias más comunes al entrar por crear()/actualizar().
"""

from __future__ import annotations
from ui.core.services.base.crud_service import CRUDService
from ui.core.services.base.service_result import ServiceResult


class ProductoService(CRUDService):

    TIPOS_VALIDOS = ("individual", "elaborado", "combo")

    def __init__(self, producto_repository, recetas_service, activo_service, ingrediente_service=None):
        self._repo = producto_repository
        self._recetas = recetas_service
        self._activos = activo_service
        # ⚠️ Opcional: si no se pasa, el costo de componentes tipo
        # "ingrediente" en productos elaborados no se puede calcular
        # (se contabiliza como 0). Pasarlo en cuanto exista.
        self._ingredientes = ingrediente_service

    # ============================================================
    # MÉTODOS CRUD OBLIGATORIOS (abstractos)
    # ============================================================

    def listar(self, filtro: str = None) -> ServiceResult:
        try:
            datos = self._repo.listar(filtro)
            return ServiceResult.ok(datos=datos)
        except Exception as e:
            return ServiceResult.error(str(e))

    def obtener(self, identificador: int) -> ServiceResult:
        try:
            datos = self._repo.obtener(identificador)
            if not datos:
                return ServiceResult.error("Producto no encontrado.")
            return ServiceResult.ok(datos=datos)
        except Exception as e:
            return ServiceResult.error(str(e))

    def crear(self, datos: dict) -> ServiceResult:
        datos = self._normalizar_alias(datos)

        valido, mensaje = self.validar(datos)
        if not valido:
            return ServiceResult.error(mensaje)

        datos = self._calcular_y_normalizar(datos)

        try:
            nuevo_id = self._repo.crear(datos)
            return ServiceResult.ok(
                mensaje="Producto creado correctamente.",
                datos={"id_producto": nuevo_id, "precio_final": datos["precio_final"]},
            )
        except Exception as e:
            return ServiceResult.error(str(e))

    def actualizar(self, identificador: int, datos: dict) -> ServiceResult:
        datos = self._normalizar_alias(datos)

        valido, mensaje = self.validar(datos)
        if not valido:
            return ServiceResult.error(mensaje)

        datos = self._calcular_y_normalizar(datos)

        try:
            success = self._repo.actualizar(identificador, datos)
            if not success:
                return ServiceResult.error("No se pudo actualizar el producto.")
            return ServiceResult.ok("Producto actualizado.", datos={"precio_final": datos["precio_final"]})
        except Exception as e:
            return ServiceResult.error(str(e))

    def eliminar(self, identificador: int) -> ServiceResult:
        try:
            success = self._repo.eliminar(identificador)
            if not success:
                return ServiceResult.error("No se pudo desactivar el producto.")
            return ServiceResult.ok("Producto desactivado.")
        except Exception as e:
            return ServiceResult.error(str(e))

    def buscar(self, texto: str) -> ServiceResult:
        try:
            datos = self._repo.buscar(texto)
            return ServiceResult.ok(datos=datos)
        except Exception as e:
            return ServiceResult.error(str(e))

    def calcular_preview(self, datos: dict) -> ServiceResult:
        """
        Calcula costo_total y precio_final para datos de un producto que
        todavía se está armando (por ejemplo, en el wizard), SIN guardar
        nada ni exigir que estén todos los campos obligatorios.

        A diferencia de crear()/actualizar(), acá los campos faltantes se
        tratan como 0 / vacíos en vez de rechazar el cálculo. Esto permite
        mostrarle al usuario un precio sugerido a medida que completa el
        producto (por ejemplo, para sugerir el precio de una presentación
        por pedazos antes de guardar).
        """
        try:
            datos_normalizados = self._normalizar_alias(dict(datos))
            datos_normalizados.setdefault("tipo", "individual")
            calculado = self._calcular_y_normalizar(datos_normalizados)
            return ServiceResult.ok(datos={
                "costo_total": calculado.get("costo_total", 0.0),
                "precio_final": calculado.get("precio_final", 0.0),
            })
        except Exception as e:
            return ServiceResult.error(str(e))

    def validar(self, datos: dict) -> tuple[bool, str]:
        """Valida los datos de un producto antes de guardar, según su tipo."""
        tipo = datos.get("tipo")
        if tipo not in self.TIPOS_VALIDOS:
            return False, "El tipo de producto no es válido."

        if not datos.get("nombre", "").strip():
            return False, "El nombre es obligatorio."

        if tipo == "individual" and not datos.get("id_receta"):
            return False, "Debe seleccionar una receta."

        if tipo == "elaborado" and not datos.get("componentes"):
            return False, "Debe agregar al menos un componente."

        if tipo == "combo":
            if not datos.get("productos_combo"):
                return False, "Debe agregar al menos un producto al combo."
            if not datos.get("precio_combo"):
                return False, "Debe indicar el precio del combo."

        return True, ""

    # ============================================================
    # NORMALIZACIÓN DE ALIAS DE CLAVES
    # ============================================================

    def _normalizar_alias(self, datos: dict) -> dict:
        """
        Traduce al vocabulario interno del service/repositorio las claves
        que llegan con otro nombre desde otras capas, sin mutar el dict
        original recibido:

        - ProductoWizard._guardar() guarda la lista de productos del combo
          bajo "productos" (no "productos_combo").
        - ProductoRepository.obtener()/self.obtener() devuelven el id de
          receta como "receta_id" (alias de columna), pero crear()/
          actualizar() esperan "id_receta". Esto pasa, por ejemplo, al
          reutilizar el resultado de obtener() para duplicar un producto.
        """
        datos = dict(datos)

        if datos.get("tipo") == "combo":
            if "productos_combo" not in datos and "productos" in datos:
                datos["productos_combo"] = datos.pop("productos")

        if datos.get("tipo") == "individual":
            if not datos.get("id_receta") and datos.get("receta_id"):
                datos["id_receta"] = datos["receta_id"]

        return datos

    # ============================================================
    # DUPLICAR
    # ============================================================

    def duplicar(self, identificador: int) -> ServiceResult:
        """
        Crea una copia de un producto existente (mismos componentes,
        empaques, costos indirectos, presentaciones o productos de combo
        según el tipo), con el nombre sufijado como "(copia)".

        Se apoya en `obtener()` + `crear()` + `_normalizar_alias` para no
        obligar a quien llama (ProductoModule) a resolver a mano el
        desfase de claves entre lo que devuelve obtener() y lo que
        espera crear().
        """
        resultado = self.obtener(identificador)
        if resultado.fallo:
            return resultado

        original = resultado.datos
        datos = dict(original)
        datos["nombre"] = f"{original.get('nombre', '')} (copia)"
        for campo in ("id_producto", "activo", "nombre_receta"):
            datos.pop(campo, None)

        return self.crear(datos)

    # ============================================================
    # CÁLCULO
    # ============================================================

    def _calcular_y_normalizar(self, datos: dict) -> dict:
        """
        Rellena en `datos` todos los campos calculados que espera el
        repositorio: costo_receta, empaques_total, costos_indirectos_total,
        mano_obra (valor ya resuelto), costo_total y precio_final.
        """
        tipo = datos["tipo"]

        total_empaques = self._sumar_activos(datos.get("empaques", []))

        # ✅ El wizard ya no hace elegir costos indirectos "a mano": los
        # calcula como tiempo_preparacion x tasas por hora (ver Mi
        # Negocio / ParametrosNegocioService) y los manda hechos en
        # "costos_indirectos_monto". Si no viene esa clave, se mantiene
        # compatibilidad con el flujo viejo de lista de activos elegidos
        # a mano (por si algún llamador todavía la usa).
        if "costos_indirectos_monto" in datos:
            total_costos_indirectos = round(float(datos.get("costos_indirectos_monto", 0) or 0), 2)
        else:
            total_costos_indirectos = self._sumar_activos(datos.get("costos_indirectos", []))

        if tipo == "individual":
            costo_base = self._calcular_costo_receta(datos["id_receta"])
        elif tipo == "elaborado":
            costo_base = self._calcular_costo_componentes(datos.get("componentes", []))
        else:  # combo
            costo_base = self._calcular_costo_combo(datos.get("productos_combo", []))

        if tipo in ("individual", "elaborado"):
            subtotal = costo_base + total_empaques + total_costos_indirectos
            # ✅ mano_obra llega ya calculada (tiempo_preparacion x
            # costo_hora_trabajo de PARAMETROS_NEGOCIO). Quien arma
            # `datos` -típicamente ProductoWizard- es responsable de
            # resolver esa multiplicación antes de llamar a crear()/
            # actualizar(); el service solo la suma como monto fijo.
            mano_obra_valor = float(datos.get("mano_obra", 0) or 0)
            margen = float(datos.get("margen_porcentaje", 40) or 40)
            costo_total = subtotal + mano_obra_valor
            precio_final = costo_total * (1 + margen / 100)

            datos["costo_receta"] = round(costo_base, 2)

        else:  # combo: precio manual, no hay margen ni mano de obra propios
            precio_combo = float(datos.get("precio_combo", 0) or 0)
            descuento = float(datos.get("descuento_combo", 0) or 0)
            precio_final = precio_combo * (1 - descuento / 100)
            mano_obra_valor = 0.0
            # Informativo: cuánto "valen" por separado los productos del combo.
            costo_total = costo_base

            datos["costo_receta"] = 0

        datos["empaques_total"] = round(total_empaques, 2)
        datos["costos_indirectos_total"] = round(total_costos_indirectos, 2)
        datos["mano_obra"] = round(mano_obra_valor, 2)
        datos["costo_total"] = round(costo_total, 2)
        datos["precio_final"] = round(precio_final, 2)

        return datos

    def _sumar_activos(self, items: list[dict]) -> float:
        """
        `items` es una lista de {"id_activo": int, "cantidad": float},
        tanto para empaques como para costos indirectos (ambos viven
        en ACTIVOS / "recursos").

        ✅ ProductoRepository._obtener_activos() devuelve cada fila con
        la clave "id" (no "id_activo") cuando se lee un producto ya
        guardado. Si esa misma lista se reutiliza tal cual para guardar
        (p.ej. al editar sin tocar los empaques), acá se acepta "id"
        como alternativa para no romper con un KeyError.
        """
        total = 0.0
        for item in items or []:
            id_activo = item.get("id_activo", item.get("id"))
            # ActivoService.obtener() devuelve un diccionario si existe,
            # o None si no — no un ServiceResult con .exito/.datos.
            activo = self._activos.obtener(id_activo)
            if activo:
                costo_unitario = float(activo.get("costo_unitario", 0))
                cantidad = float(item.get("cantidad", 1) or 1)
                total += costo_unitario * cantidad
        return round(total, 2)

    def _calcular_costo_receta(self, receta_id: int) -> float:
        if not receta_id:
            return 0.0
        resultado = self._recetas.obtener(receta_id)
        if resultado.fallo:
            return 0.0
        ingredientes = resultado.datos.get("ingredientes", [])
        total = sum(
            float(ing.get("cantidad_necesaria", 0)) * float(ing.get("costo_unitario", 0))
            for ing in ingredientes
        )
        return round(total, 2)

    def _calcular_costo_componentes(self, componentes: list[dict]) -> float:
        """
        `componentes` es [{"tipo": "ingrediente"|"producto"|"subproducto",
        "id": int, "cantidad": float}]. Un "subproducto" se calcula igual
        que un "producto": usa su precio_final ya guardado (no se
        recalcula recursivamente, evita ciclos).
        """
        total = 0.0
        for c in componentes or []:
            cantidad = float(c.get("cantidad", 0) or 0)
            tipo_c = c.get("tipo")
            id_c = c.get("id")

            if tipo_c == "ingrediente":
                if not self._ingredientes:
                    continue
                res = self._ingredientes.obtener(id_c)
                if res.exito:
                    total += cantidad * float(res.datos.get("costo_unitario", 0))

            elif tipo_c in ("producto", "subproducto"):
                res = self.obtener(id_c)
                if res.exito:
                    total += cantidad * float(res.datos.get("precio_final", 0))

        return round(total, 2)

    def _calcular_costo_combo(self, productos_combo: list[dict]) -> float:
        total = 0.0
        for item in productos_combo or []:
            cantidad = float(item.get("cantidad", 1) or 1)
            res = self.obtener(item["id_producto"])
            if res.exito:
                total += cantidad * float(res.datos.get("precio_final", 0))
        return round(total, 2)