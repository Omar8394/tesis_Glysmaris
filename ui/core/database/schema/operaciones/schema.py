"""
============================================================
Sistema La Dulce Tía

Archivo:
    schema.py

Responsabilidad:
    Definir el esquema de la base de datos de operaciones.

    Contiene las sentencias CREATE TABLE para todas las tablas
    del negocio (ingredientes, productos, recetas, producción,
    ventas, compras, gastos, etc.).

    No contiene lógica de negocio ni datos de prueba.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

SCHEMA_OPERACIONES = [
    # ============================================================
    # 1. INGREDIENTES (Catálogo de insumos y materias primas)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS INGREDIENTES (
        id_ingrediente INT AUTO_INCREMENT PRIMARY KEY,
        nombre_ingrediente VARCHAR(100) UNIQUE NOT NULL,
        unidad_medida VARCHAR(30) NOT NULL,
        categoria VARCHAR(50),
        perecedero BOOLEAN DEFAULT FALSE,
        refrigerado BOOLEAN DEFAULT FALSE,
        descripcion TEXT,
        contenido_unidad VARCHAR(50)
    )
    """,
    # ============================================================
    # 1B. LOTES_INVENTARIO (Movimientos - Datos Dinámicos PEPS)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS LOTES_INVENTARIO (
        id_lote INT AUTO_INCREMENT PRIMARY KEY,
        id_ingrediente INT NOT NULL,
        stock_inicial DECIMAL(10,2) NOT NULL DEFAULT 0,
        stock_actual DECIMAL(10,2) NOT NULL DEFAULT 0,
        costo_unitario DECIMAL(10,4) NOT NULL DEFAULT 0,
        fecha_ingreso DATE NOT NULL,
        fecha_caducidad DATE NOT NULL,
        FOREIGN KEY (id_ingrediente) REFERENCES INGREDIENTES(id_ingrediente) ON DELETE CASCADE
    )
    """,

    # ============================================================
    # 1C. PERDIDAS_INVENTARIO (Historial de mermas/bajas por lote)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS PERDIDAS_INVENTARIO (
        id_perdida INT AUTO_INCREMENT PRIMARY KEY,
        id_lote INT NULL,
        nombre_ingrediente VARCHAR(100),
        unidad_medida VARCHAR(30),
        cantidad DECIMAL(10,2) NOT NULL,
        motivo ENUM(
            'error_registro',
            'perdida_material',
            'caducidad',
            'daño',
            'otro'
        ) NOT NULL,
        descripcion TEXT,
        costo_perdida DECIMAL(10,2),
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_lote) REFERENCES LOTES_INVENTARIO(id_lote) ON DELETE SET NULL
    )
    """,

    # ============================================================
    # 2. RECETAS (independientes de productos)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS RECETAS (
        id_receta INT AUTO_INCREMENT PRIMARY KEY,
        nombre_receta VARCHAR(100) NOT NULL,
        tipo_receta VARCHAR(50) NOT NULL,
        descripcion TEXT,
        costo_ingredientes DECIMAL(10,2) NOT NULL DEFAULT 0,
        rendimiento_cantidad DECIMAL(10,2) NOT NULL DEFAULT 1,
        rendimiento_unidad VARCHAR(30) NOT NULL DEFAULT 'unidad',
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ============================================================
    # 3. RECETA_INGREDIENTES (relación receta-ingrediente)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS RECETA_INGREDIENTES (
        id_receta_ingrediente INT AUTO_INCREMENT PRIMARY KEY,
        id_receta INT NOT NULL,
        id_ingrediente INT NOT NULL,
        cantidad_necesaria DECIMAL(10,4) NOT NULL,
        unidad VARCHAR(200) NOT NULL,
        FOREIGN KEY (id_receta) REFERENCES RECETAS(id_receta) ON DELETE CASCADE,
        FOREIGN KEY (id_ingrediente) REFERENCES INGREDIENTES(id_ingrediente) ON DELETE RESTRICT
    )
    """,
    # ============================================================
    # 4. PRODUCTOS
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCTOS (
        id_producto INT AUTO_INCREMENT PRIMARY KEY,
        nombre_producto VARCHAR(150) NOT NULL,
        tipo_producto VARCHAR(50),
        categoria VARCHAR(50),
        precio_venta DECIMAL(10,2) DEFAULT 0,
        peso DECIMAL(10,2) DEFAULT 1.0,
        unidad_peso VARCHAR(20) DEFAULT 'kg',
        receta_id INT NULL,
        producto_padre_id INT NULL,
        descripcion_producto TEXT,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        activo BOOLEAN DEFAULT TRUE,
        sabor_producto VARCHAR(100),
        relleno_producto VARCHAR(100),
        cobertura_producto VARCHAR(100),
        costo_receta DECIMAL(10,2) DEFAULT 0,
        tiempo_preparacion_minutos DECIMAL(10,2) DEFAULT 0,
        mano_obra DECIMAL(10,2) DEFAULT 0,
        empaques DECIMAL(10,2) DEFAULT 0,
        costos_indirectos DECIMAL(10,2) DEFAULT 0,
        margen_porcentaje DECIMAL(5,2) DEFAULT 40,
        costo_total DECIMAL(10,2) DEFAULT 0,
        precio_final DECIMAL(10,2) DEFAULT 0,
        precio_combo DECIMAL(10,2) DEFAULT 0,
        descuento_combo DECIMAL(5,2) DEFAULT 0,

        FOREIGN KEY (receta_id) REFERENCES RECETAS(id_receta) ON DELETE SET NULL,
        FOREIGN KEY (producto_padre_id) REFERENCES PRODUCTOS(id_producto) ON DELETE SET NULL
    )
    """,
    # ============================================================
    # 5. PODUCTO_PRESENTACIONES
    # ============================================================
   """
        CREATE TABLE IF NOT EXISTS PRODUCTO_PRESENTACIONES (
            id_presentacion INT AUTO_INCREMENT PRIMARY KEY,
            id_producto INT NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            precio DECIMAL(10,2) NOT NULL DEFAULT 0,
            FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE CASCADE
    )""",
    # ============================================================
    # 6. PRODUCTO_COMPONENTES
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCTO_COMPONENTES (
        id_componente INT AUTO_INCREMENT PRIMARY KEY,
        id_producto INT NOT NULL,
        tipo_componente ENUM('ingrediente','producto','subproducto') NOT NULL,
        id_ingrediente INT NULL,
        id_producto_componente INT NULL,
        cantidad_necesaria DECIMAL(10,4) NOT NULL,
        FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE CASCADE,
        FOREIGN KEY (id_ingrediente) REFERENCES INGREDIENTES(id_ingrediente) ON DELETE RESTRICT,
        FOREIGN KEY (id_producto_componente) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT
)
    """,


    """
        CREATE TABLE IF NOT EXISTS PRODUCTO_ACTIVO (
        id_producto INT NOT NULL,
        id_activo INT NOT NULL,
        cantidad_necesaria DECIMAL(10,4) NOT NULL DEFAULT 1,
        PRIMARY KEY (id_producto, id_activo),
        FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE CASCADE,
        FOREIGN KEY (id_activo) REFERENCES ACTIVOS(id_activo) ON DELETE RESTRICT
    )
    """,
    """
        CREATE TABLE IF NOT EXISTS PRODUCTO_COMBO_ITEMS (
        id_producto_combo INT NOT NULL,
        id_producto_incluido INT NOT NULL,
        cantidad DECIMAL(10,2) NOT NULL DEFAULT 1,
        PRIMARY KEY (id_producto_combo, id_producto_incluido),
        FOREIGN KEY (id_producto_combo) REFERENCES PRODUCTOS(id_producto) ON DELETE CASCADE,
        FOREIGN KEY (id_producto_incluido) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT
        )
    """,


    #============================================================
    #7. PRODUCCION_ORDENES (Cabecera de la orden de producción)
    #============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_ORDENES (
        id_orden INT AUTO_INCREMENT PRIMARY KEY,
        numero_orden VARCHAR(20) UNIQUE NOT NULL,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_planificada DATE NOT NULL,
        hora_estimada TIME,
        prioridad ENUM('baja', 'media', 'alta', 'urgente') DEFAULT 'media',
        responsable VARCHAR(100),
        estado ENUM('pendiente', 'en_proceso', 'finalizada', 'cancelada') DEFAULT 'pendiente',
        notas TEXT,
        costo_estimado DECIMAL(10,2) DEFAULT 0,
        costo_real DECIMAL(10,2) DEFAULT 0,
        tiempo_estimado_minutos INT DEFAULT 0,
        tiempo_real_minutos INT DEFAULT 0,
        fecha_inicio DATETIME NULL,
        fecha_fin DATETIME NULL,
        creado_por VARCHAR(100),
        INDEX idx_estado (estado),
        INDEX idx_fecha (fecha_planificada),
        INDEX idx_prioridad (prioridad),
        INDEX idx_numero (numero_orden)
    )
    """,

#============================================================
# 8. PRODUCCION_DETALLE (Productos incluidos en la orden)
#============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_DETALLE (
        id_detalle INT AUTO_INCREMENT PRIMARY KEY,
        id_orden INT NOT NULL,
        id_producto INT NOT NULL,
        id_presentacion INT NULL,                              -- Presentación específica
        cantidad_planificada INT NOT NULL DEFAULT 1,
        cantidad_obtenida INT DEFAULT 0,
        precio_final DECIMAL(10,2) DEFAULT 0,
        modificaciones TEXT,
        costo_calculado DECIMAL(10,2) DEFAULT 0,
        rendimiento_porcentaje DECIMAL(5,2) DEFAULT 0,
        disponible_venta BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (id_orden) REFERENCES PRODUCCION_ORDENES(id_orden) ON DELETE CASCADE,
        FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT,
        FOREIGN KEY (id_presentacion) REFERENCES PRODUCTO_PRESENTACIONES(id_presentacion) ON DELETE SET NULL,
        INDEX idx_orden (id_orden),
        INDEX idx_producto (id_producto)
    )
    """,

    #============================================================
    #9. PRODUCCION_MERMAS
    #============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_MERMAS (
        id_merma INT AUTO_INCREMENT PRIMARY KEY,
        id_orden INT NOT NULL,
        id_detalle INT NULL,                                   -- Detalle al que pertenece (opcional)
        id_producto INT NULL,                                  -- Producto afectado (opcional)
        cantidad DECIMAL(10,2) NOT NULL,
        tipo_merma ENUM('recuperable', 'no_recuperable') NOT NULL,
        motivo ENUM(
            'quemado',
            'rotura',
            'contaminacion',
            'error_preparacion',
            'decoracion',
            'otro'
        ) NOT NULL,
        descripcion TEXT,                                      -- Solo para 'otro' o detalles extra
        costo_asociado DECIMAL(10,2) DEFAULT 0,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_orden) REFERENCES PRODUCCION_ORDENES(id_orden) ON DELETE CASCADE,
        FOREIGN KEY (id_detalle) REFERENCES PRODUCCION_DETALLE(id_detalle) ON DELETE SET NULL,
        FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE SET NULL,
        INDEX idx_orden (id_orden),
        INDEX idx_detalle (id_detalle)
    )
    """,

    #============================================================
    #10. PRODUCCION_SUBPRODUCTOS (Generados a partir de mermas recuperables)
    #============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_SUBPRODUCTOS (
        id_subproducto INT AUTO_INCREMENT PRIMARY KEY,
        id_merma INT NOT NULL,
        id_detalle INT NULL,                                   -- Detalle de origen (opcional)
        id_producto_subproducto INT NOT NULL,                  -- Producto que se genera (ej: "Bizcocho molido")
        cantidad DECIMAL(10,2) NOT NULL,
        unidad VARCHAR(30),
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_merma) REFERENCES PRODUCCION_MERMAS(id_merma) ON DELETE CASCADE,
        FOREIGN KEY (id_detalle) REFERENCES PRODUCCION_DETALLE(id_detalle) ON DELETE SET NULL,
        FOREIGN KEY (id_producto_subproducto) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT,
        INDEX idx_merma (id_merma)
    )
    """,

    #============================================================
    #11. PRODUCCION_INGREDIENTES_RESERVADOS (Reserva y consumo de ingredientes)
    #============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_INGREDIENTES_RESERVADOS (
        id_reserva INT AUTO_INCREMENT PRIMARY KEY,
        id_orden INT NOT NULL,
        id_detalle INT NOT NULL,                               -- Detalle asociado
        id_producto INT NOT NULL,                              -- Producto que consume el ingrediente
        id_ingrediente INT NOT NULL,
        id_lote INT NULL,                                      -- Lote específico del que se descuenta
        cantidad_reservada DECIMAL(10,2) NOT NULL,
        cantidad_consumida DECIMAL(10,2) DEFAULT 0,
        cantidad_devuelta DECIMAL(10,2) DEFAULT 0,
        fecha_reserva DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_orden) REFERENCES PRODUCCION_ORDENES(id_orden) ON DELETE CASCADE,
        FOREIGN KEY (id_detalle) REFERENCES PRODUCCION_DETALLE(id_detalle) ON DELETE CASCADE,
        FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT,
        FOREIGN KEY (id_ingrediente) REFERENCES INGREDIENTES(id_ingrediente) ON DELETE RESTRICT,
        FOREIGN KEY (id_lote) REFERENCES LOTES_INVENTARIO(id_lote) ON DELETE SET NULL,
        INDEX idx_orden (id_orden),
        INDEX idx_detalle (id_detalle),
        INDEX idx_producto (id_producto)
    )
    """,

    #============================================================
    # 2. PRODUCCION_ACTIVOS_RESERVADOS (Reserva de activos/recursos)
    #============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_ACTIVOS_RESERVADOS (
        id_reserva_activo INT AUTO_INCREMENT PRIMARY KEY,
        id_orden INT NOT NULL,
        id_detalle INT NOT NULL,
        id_producto INT NOT NULL,
        id_activo INT NOT NULL,
        cantidad_reservada DECIMAL(10,2) NOT NULL,
        cantidad_consumida DECIMAL(10,2) DEFAULT 0,
        fecha_reserva DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_orden) REFERENCES PRODUCCION_ORDENES(id_orden) ON DELETE CASCADE,
        FOREIGN KEY (id_detalle) REFERENCES PRODUCCION_DETALLE(id_detalle) ON DELETE CASCADE,
        FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT,
        FOREIGN KEY (id_activo) REFERENCES ACTIVOS(id_activo) ON DELETE RESTRICT,
        INDEX idx_orden (id_orden),
        INDEX idx_detalle (id_detalle)
    )
    """,

    #============================================================
    # 13. PRODUCCION_COSTOS (Desglose detallado de costos)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_COSTOS (
        id_costo INT AUTO_INCREMENT PRIMARY KEY,
        id_orden INT NOT NULL,
        id_detalle INT NULL,                                   -- Opcional: si el costo es específico de un detalle
        tipo ENUM('ingrediente', 'activo', 'mano_obra', 'costo_indirecto', 'otro') NOT NULL,
        descripcion VARCHAR(100) NOT NULL,
        valor_estimado DECIMAL(10,2) NOT NULL DEFAULT 0,
        valor_real DECIMAL(10,2) NOT NULL DEFAULT 0,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_orden) REFERENCES PRODUCCION_ORDENES(id_orden) ON DELETE CASCADE,
        FOREIGN KEY (id_detalle) REFERENCES PRODUCCION_DETALLE(id_detalle) ON DELETE CASCADE,
        INDEX idx_orden (id_orden)
    )
    """,

    #============================================================
    #14. PRODUCCION_ANALISIS (Análisis de disponibilidad previo a la orden)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS PRODUCCION_ANALISIS (
        id_analisis INT AUTO_INCREMENT PRIMARY KEY,
        id_orden INT NOT NULL,
        id_producto INT NOT NULL,
        cantidad_solicitada INT NOT NULL,
        cantidad_posible INT NOT NULL,
        resultado ENUM('completo', 'parcial', 'inviable') NOT NULL,
        fecha_analisis DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_orden) REFERENCES PRODUCCION_ORDENES(id_orden) ON DELETE CASCADE,
        FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT,
        INDEX idx_orden (id_orden)
    )
    """,

    #============================================================
    #15. ANALISIS_FALTANTES (Detalle de faltantes del análisis)
    #============================================================
        """
        CREATE TABLE IF NOT EXISTS ANALISIS_FALTANTES (
            id_faltante INT AUTO_INCREMENT PRIMARY KEY,
            id_analisis INT NOT NULL,
            id_ingrediente INT NULL,
            id_activo INT NULL,
            necesario DECIMAL(10,2) NOT NULL,
            disponible DECIMAL(10,2) NOT NULL,
            faltante DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (id_analisis) REFERENCES PRODUCCION_ANALISIS(id_analisis) ON DELETE CASCADE,
            FOREIGN KEY (id_ingrediente) REFERENCES INGREDIENTES(id_ingrediente) ON DELETE SET NULL,
            FOREIGN KEY (id_activo) REFERENCES ACTIVOS(id_activo) ON DELETE SET NULL,
            INDEX idx_analisis (id_analisis)
        )
        """,

    #============================================================
    #16. PRODUCCION_HISTORIAL_ESTADOS (Bitácora de cambios de estado)
    #============================================================
        """
        CREATE TABLE IF NOT EXISTS PRODUCCION_HISTORIAL_ESTADOS (
            id_historial INT AUTO_INCREMENT PRIMARY KEY,
            id_orden INT NOT NULL,
            estado_anterior ENUM('pendiente', 'en_proceso', 'finalizada', 'cancelada') NOT NULL,
            estado_nuevo ENUM('pendiente', 'en_proceso', 'finalizada', 'cancelada') NOT NULL,
            fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario VARCHAR(100),
            observaciones TEXT,
            FOREIGN KEY (id_orden) REFERENCES PRODUCCION_ORDENES(id_orden) ON DELETE CASCADE,
            INDEX idx_orden (id_orden)
        )
        """,

    # NOTA: los ajustes a PRODUCTOS y PRODUCTO_PRESENTACIONES (eliminar
    # columnas redundantes, agregar mano_obra_valor/tipo, agregar
    # diametro/peso/id_receta/costo/estado, y la FK de id_receta) ya NO
    # viven aquí como ALTER TABLE en texto plano, porque "DROP COLUMN
    # IF EXISTS" combinado y "ADD FOREIGN KEY IF NOT EXISTS" no son
    # sintaxis válida en MySQL/MariaDB y rompían la migración.
    # Esa lógica ahora está en migrator.py, como código Python que
    # verifica en INFORMATION_SCHEMA si cada columna/llave ya existe
    # antes de tocarla. Ver _aplicar_migraciones_manuales().

    # ============================================================
    # 9. VENTAS
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS VENTAS (
        id_venta INT AUTO_INCREMENT PRIMARY KEY,
        fecha_venta DATETIME DEFAULT CURRENT_TIMESTAMP,
        cliente VARCHAR(100),
        cedula VARCHAR(20),
        metodo_pago ENUM('efectivo', 'pagomovil', 'credito') NOT NULL,
        referencia VARCHAR(50),
        total DECIMAL(10,2) NOT NULL
    )
    """,
    # ============================================================
    # 10. DETALLE_VENTA
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS DETALLE_VENTA (
        id_detalle_venta INT AUTO_INCREMENT PRIMARY KEY,
        id_venta INT NOT NULL,
        id_detalle_produccion INT NOT NULL,
        cantidad INT NOT NULL,
        precio_unitario DECIMAL(10,2) NOT NULL,
        subtotal DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (id_venta) REFERENCES VENTAS(id_venta) ON DELETE CASCADE,
        FOREIGN KEY (id_detalle_produccion) REFERENCES DETALLE_PRODUCCION(id_detalle) ON DELETE RESTRICT
    )
    """,
    # ============================================================
    # 11. COMPRAS
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS COMPRAS (
        id_compra INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        categoria ENUM('Insumos', 'Herramientas', 'Servicios', 'Otros') NOT NULL,
        cantidad DECIMAL(10,2) NOT NULL,
        unidad VARCHAR(30),
        precio DECIMAL(10,2),
        total DECIMAL(10,2) NOT NULL,
        marca VARCHAR(50),
        metodo_pago ENUM('efectivo', 'divisa', 'pagomovil', 'credito') NOT NULL,
        monto_pendiente DECIMAL(10,2),
        fecha_compra DATE NOT NULL,
        fecha_vencimiento DATE,
        fecha_proximo_cobro DATE,
        proveedor VARCHAR(100),
        observaciones TEXT,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_nombre (nombre),
        INDEX idx_marca (marca)
    )
    """,
    # ============================================================
    # 12. ACTIVOS (Empaques, Utensilios, Herramientas, Costos Indirectos)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS ACTIVOS (
        id_activo INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        tipo ENUM(
            'empaque',
            'utensilio',
            'herramienta',
            'costo_indirecto',
            'servicio',
            'transporte',
            'mobiliario',
            'otro'
        ) NOT NULL,
        costo_unitario DECIMAL(10,2) NOT NULL DEFAULT 0,
        stock_actual DECIMAL(10,2) DEFAULT 0,
        unidad VARCHAR(30),
        descripcion TEXT,
        estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
        proveedor VARCHAR(100),
        codigo_interno VARCHAR(50),
        observaciones TEXT,
        modalidad_costo ENUM(
            'por_unidad',
            'mensual',
            'por_hora',
            'por_uso',
            'porcentaje'
        ) NOT NULL DEFAULT 'por_unidad',
        unidad_costo VARCHAR(30),
        periodo VARCHAR(30),
        vida_util_meses INT NULL,
        valor_residual DECIMAL(10,2) DEFAULT 0,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_tipo (tipo),
        INDEX idx_nombre (nombre)
    )
    """,

    # ============================================================
    # 17. PARAMETROS_NEGOCIO (Mano de obra y base de prorrateo)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS PARAMETROS_NEGOCIO (
        id_parametro INT AUTO_INCREMENT PRIMARY KEY,
        costo_hora_trabajo DECIMAL(10,2) NOT NULL DEFAULT 0,
        horas_trabajo_mes DECIMAL(10,2) NOT NULL DEFAULT 0,
        fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,

]