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

    def crear_recuperable(self, nombre: str, unidad: str = "", costo_unitario: float = 0.0) -> ServiceResult:
        """Da de alta el producto-catálogo mínimo de un recuperable de
        merma (ej. "trozos de torta"): no nace de una receta ni de otros
        componentes, es la materia sobrante en sí misma -- por eso NO pasa
        por crear()/validar(), que exigen receta ("individual") o al
        menos un componente ("elaborado"). Se guarda directo como
        "elaborado" con componentes=[] (el repositorio ya tolera una
        lista de componentes vacía sin error) y precio de referencia
        opcional a partir de lo que costó la merma.

        Una vez creado, ya queda disponible para elegirse como
        "Producto"/"Subproducto" al armar otro producto elaborado en
        ProductoWizard (busca sobre el mismo catálogo de PRODUCTOS), y
        para editarle después empaques, margen o precio como a cualquier
        otro producto.
        """
        nombre = (nombre or "").strip()
        if not nombre:
            return ServiceResult.error("El nombre del recuperable es obligatorio.")

        # ✅ Antes `unidad` solo se usaba para armar el texto de
        # descripción y se perdía: no quedaba guardada en ningún campo
        # consultable. Sin eso, un producto elaborado que usara este
        # recuperable como componente no tenía con qué chequear
        # coherencia de unidades (ver unidad_base más abajo y
        # ProductoService._unidad_base_producto).
        unidad = (unidad or "unidad").strip() or "unidad"
        datos = {
            "tipo": "elaborado",
            "nombre": nombre,
            "categoria": "Recuperados",
            "descripcion": f"Generado a partir de una merma recuperable ({unidad}).".strip(),
            "componentes": [],
            "empaques": [],
            "costos_indirectos": [],
            "margen_porcentaje": 0,
            "mano_obra": 0,
            "costos_indirectos_monto": 0,
            "unidad_base": unidad,
        }
        if costo_unitario:
            # No hay receta de la que calcular un costo, así que el
            # costo aproximado de la merma se usa directo como precio de
            # referencia (en vez de arrancar en $0 hasta que alguien lo
            # edite a mano).
            datos["precio_venta"] = round(float(costo_unitario), 2)

        datos = self._calcular_y_normalizar(datos)
        try:
            nuevo_id = self._repo.crear(datos)
            return ServiceResult.ok(
                f"Producto recuperable '{nombre}' creado.",
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
                return ServiceResult.error("No se pudo eliminar el producto.")
            return ServiceResult.ok("Producto eliminado.")
        except Exception as e:
            self._repo._rollback()
            return ServiceResult.error(str(e))

    def alternar_activo(self, identificador: int) -> ServiceResult:
        """
        Activa o desactiva un producto (reversible), a diferencia de
        eliminar(): la tarjeta ofrece "Desactivar"/"Activar" como una
        acción distinta de "Eliminar" -- antes ambas llamaban a
        eliminar() y no había forma de reactivar un producto desde la
        UI.
        """
        try:
            nuevo_estado = self._repo.alternar_activo(identificador)
            if nuevo_estado is None:
                return ServiceResult.error("No se pudo cambiar el estado del producto.")
            mensaje = "Producto activado." if nuevo_estado else "Producto desactivado."
            return ServiceResult.ok(mensaje, datos={"activo": nuevo_estado})
        except Exception as e:
            self._repo._rollback()
            return ServiceResult.error(str(e))

    def buscar(self, texto: str) -> ServiceResult:
        try:
            datos = self._repo.buscar(texto)
            return ServiceResult.ok(datos=datos)
        except Exception as e:
            return ServiceResult.error(str(e))

    def calcular_preview(self, datos: dict) -> ServiceResult:
        """
        Calcula costo y precio SUGERIDO en vivo, sin tocar la base de
        datos. Se usa desde ProductoWizard para mostrar el precio
        sugerido mientras el usuario carga los datos.

        ⚠️ Antes esto devolvía `ServiceResult.ok(datos={...})` -- un
        set de un solo elemento (el objeto Ellipsis), no el resultado
        del cálculo. Eso hacía que el wizard SIEMPRE recibiera un
        precio sugerido de 0, sin importar los datos cargados.
        """
        try:
            datos_normalizados = self._normalizar_alias(dict(datos))
            datos_normalizados.setdefault("tipo", "individual")
            calculado = self._calcular_y_normalizar(datos_normalizados)
            return ServiceResult.ok(datos=calculado)
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

        if tipo == "elaborado":
            if not datos.get("componentes"):
                return False, "Debe agregar al menos un componente."
            for c in datos.get("componentes", []):
                valido_unidad, mensaje_unidad = self._validar_unidad_componente(c)
                if not valido_unidad:
                    return False, mensaje_unidad

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
            precio_sugerido = costo_total * (1 + margen / 100)

            datos["costo_receta"] = round(costo_base, 2)

        else:  # combo: precio manual, no hay margen ni mano de obra propios
            precio_combo = float(datos.get("precio_combo", 0) or 0)
            descuento = float(datos.get("descuento_combo", 0) or 0)
            precio_sugerido = precio_combo * (1 - descuento / 100)
            mano_obra_valor = 0.0
            # Informativo: cuánto "valen" por separado los productos del combo.
            costo_total = costo_base

            datos["costo_receta"] = 0

        # ✅ El precio sugerido SIEMPRE se calcula y se guarda aparte,
        # como referencia. El precio de venta real (precio_final) es
        # el que decide el usuario: si mandó "precio_venta" (el campo
        # editable del wizard), se respeta tal cual; si no lo mandó,
        # recién ahí se usa el sugerido como valor por defecto.
        #
        # Antes acá se pisaba `datos["precio_final"]` siempre con el
        # valor calculado, sin mirar si el usuario había escrito un
        # precio propio -- por eso el precio final que terminaba en
        # la base de datos nunca coincidía con lo que el usuario
        # tipeaba en el wizard.
        precio_venta = datos.get("precio_venta")
        if precio_venta not in (None, ""):
            try:
                precio_final = round(float(precio_venta), 2)
            except (TypeError, ValueError):
                precio_final = round(precio_sugerido, 2)
        else:
            precio_final = round(precio_sugerido, 2)

        datos["empaques_total"] = round(total_empaques, 2)
        datos["costos_indirectos_total"] = round(total_costos_indirectos, 2)
        datos["mano_obra"] = round(mano_obra_valor, 2)
        datos["costo_total"] = round(costo_total, 2)
        datos["precio_sugerido"] = round(precio_sugerido, 2)
        datos["precio_final"] = precio_final

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

    # ============================================================
    # UNIDADES DE COMPONENTES (coherencia de magnitud + conversión)
    # ============================================================
    # No se permite usar, p.ej., "ml" para un componente que se guarda
    # en gramos: mezclar masa con volumen depende de la densidad de
    # cada ingrediente/producto y es fuente de errores de costeo. La
    # conversión real (y el diccionario de unidades reconocidas) ya
    # vive en RecetasService -- se reutiliza acá en vez de duplicarla,
    # así "0.5 kg" en un componente y "500 g" en una receta convierten
    # exactamente igual.

    def _unidad_base_ingrediente(self, id_ingrediente) -> Optional[str]:
        if not self._ingredientes or not id_ingrediente:
            return None
        res = self._ingredientes.obtener(id_ingrediente)
        if res.exito:
            return res.datos.get("unidad_medida")
        return None

    def _unidad_base_producto(self, datos_producto: dict) -> str:
        """
        Unidad "nativa" de un producto para poder usarse como
        referencia de coherencia: la de su receta (rendimiento_unidad)
        si es individual, o unidad_base si es elaborado/recuperable
        (no tiene receta propia). 'unidad' como último respaldo, para
        productos guardados antes de que existiera esta columna.
        """
        return (
            datos_producto.get("rendimiento_unidad")
            or datos_producto.get("unidad_base")
            or "unidad"
        )

    def _unidad_objetivo_componente(self, tipo_c: str, id_c) -> Optional[str]:
        """Unidad nativa del componente (ingrediente o producto), o
        None si no se pudo determinar (componente inexistente, o sin
        servicio de ingredientes conectado)."""
        if tipo_c == "ingrediente":
            return self._unidad_base_ingrediente(id_c)
        if tipo_c in ("producto", "subproducto"):
            res = self.obtener(id_c)
            if res.exito:
                return self._unidad_base_producto(res.datos)
        return None

    def _validar_unidad_componente(self, c: dict) -> tuple[bool, str]:
        unidad_c = (c.get("unidad") or "").strip()
        if not unidad_c:
            # Sin unidad especificada: no se puede chequear coherencia,
            # pero no se bloquea el guardado (compatibilidad con datos
            # cargados antes de que el wizard pidiera esta unidad).
            return True, ""

        unidad_objetivo = self._unidad_objetivo_componente(c.get("tipo"), c.get("id"))
        if not unidad_objetivo:
            return True, ""

        try:
            self._recetas.convertir_unidad(1, unidad_c, unidad_objetivo)
        except AttributeError:
            # self._recetas no expone convertir_unidad (mock de test u
            # otra implementación) -- no bloquear por eso.
            return True, ""
        except ValueError as e:
            nombre = c.get("nombre") or "componente"
            return False, f"Unidad no válida en '{nombre}': {e}"

        return True, ""

    def _convertir_cantidad_componente(self, cantidad: float, unidad_origen: Optional[str], unidad_destino: Optional[str]) -> float:
        """
        Convierte `cantidad` a la unidad nativa del componente antes de
        aplicar el costo por unidad. Si falta alguna unidad, son
        iguales, o la conversión no es posible (magnitud distinta, o
        unidad no reconocida), devuelve la cantidad tal cual: la
        incoherencia real ya se bloquea antes en validar(); acá no se
        quiere romper calcular_preview() (que llama a
        _calcular_y_normalizar() sin pasar por validar()).
        """
        if not unidad_origen or not unidad_destino or unidad_origen == unidad_destino:
            return cantidad
        try:
            return self._recetas.convertir_unidad(cantidad, unidad_origen, unidad_destino)
        except (ValueError, AttributeError):
            return cantidad

    def _calcular_costo_componentes(self, componentes: list[dict]) -> float:
        """
        `componentes` es [{"tipo": "ingrediente"|"producto"|"subproducto",
        "id": int, "cantidad": float, "unidad": str|None}].

        ⚠️ REGLA CLAVE (ver documento de requerimientos de Producto
        Elaborado): cuando el componente es un producto (individual o
        elaborado), solo se toma su costo de MATERIA PRIMA -- nunca su
        precio_final. El precio_final ya incluye margen de ganancia,
        mano de obra, empaques y servicios propios de ESE producto, y
        esos conceptos no se heredan: la nueva elaboración calcula los
        suyos por separado más abajo (empaque, mano de obra, costos
        indirectos, margen). Antes este método usaba precio_final para
        "producto" y "subproducto" por igual, lo que inflaba el costo
        de cualquier elaborado que usara otro producto como componente
        con el margen/mano de obra/empaque ya cobrados en ese producto.

        Por tipo de componente:
          - "ingrediente": costo_unitario del lote x cantidad_usada
            (convertida a la unidad_medida del ingrediente).
          - "producto" (individual o elaborado, sin distinguirse en el
            schema): costo_receta / rendimiento_cantidad x cantidad_usada.
            costo_receta es, para ambos casos, el costo de materia prima
            ya guardado (para individual: suma de ingredientes de su
            receta; para elaborado: suma de sus propios componentes,
            calculada al guardarse ESE producto -- por eso acá no hace
            falta recalcular, evita ciclos). Si el producto no tiene
            rendimiento definido (los elaborados no tienen receta_id
            propio, así que no hay rendimiento_cantidad de RECETAS que
            aplicar), se usa costo_receta directamente como costo
            unitario, tal como indica el documento para ese caso ("se
            usa directamente el costo total de su receta"). La cantidad
            se convierte a la unidad nativa del producto (rendimiento_
            unidad o unidad_base) antes de multiplicar.
          - "subproducto" (merma recuperable dada de alta como producto
            vía crear_recuperable()): ya tiene un precio_final que ES su
            costo por unidad (costo_asociado / cantidad_recuperada, sin
            margen ni mano de obra agregados). Se usa precio_final x
            cantidad_usada directamente (convertida a su unidad_base),
            sin dividir por rendimiento.
        """
        total = 0.0
        for c in componentes or []:
            cantidad = float(c.get("cantidad", 0) or 0)
            unidad_c = c.get("unidad")
            tipo_c = c.get("tipo")
            id_c = c.get("id")

            if tipo_c == "ingrediente":
                if not self._ingredientes:
                    continue
                res = self._ingredientes.obtener(id_c)
                if res.exito:
                    unidad_ingrediente = res.datos.get("unidad_medida")
                    cantidad_convertida = self._convertir_cantidad_componente(cantidad, unidad_c, unidad_ingrediente)
                    total += cantidad_convertida * float(res.datos.get("costo_unitario", 0))

            elif tipo_c == "producto":
                res = self.obtener(id_c)
                if res.exito:
                    costo_receta = float(res.datos.get("costo_receta", 0) or 0)
                    rendimiento = float(res.datos.get("rendimiento_cantidad", 0) or 0)
                    costo_unitario = (costo_receta / rendimiento) if rendimiento > 0 else costo_receta
                    unidad_objetivo = self._unidad_base_producto(res.datos)
                    cantidad_convertida = self._convertir_cantidad_componente(cantidad, unidad_c, unidad_objetivo)
                    total += cantidad_convertida * costo_unitario

            elif tipo_c == "subproducto":
                res = self.obtener(id_c)
                if res.exito:
                    unidad_objetivo = self._unidad_base_producto(res.datos)
                    cantidad_convertida = self._convertir_cantidad_componente(cantidad, unidad_c, unidad_objetivo)
                    total += cantidad_convertida * float(res.datos.get("precio_final", 0))

        return round(total, 2)

    def _calcular_costo_combo(self, productos_combo: list[dict]) -> float:
        total = 0.0
        for item in productos_combo or []:
            cantidad = float(item.get("cantidad", 1) or 1)
            res = self.obtener(item["id_producto"])
            if res.exito:
                total += cantidad * float(res.datos.get("precio_final", 0))
        return round(total, 2)