def create_table_operaciones():
    conn = connect_db_operaciones()
    cursor = conn.cursor()

    # --- TABLA 1: INGREDIENTES ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS INGREDIENTES (
            id_ingrediente INT ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nombre_ingrediente VARCHAR(100) UNIQUE NOT NULL,
            stock_actual REAL NOT NULL,
            unidad_medida VARCHAR(50) NOT NULL,
            costo_unitario DECIMAL(10, 2) NOT NULL, 
            fecha_caducidad DATE NOT NULL
        )
    ''')

    # --- TABLA 2: PRODUCTOS (Terminados) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PRODUCTOS (
            id_producto INT ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nombre_producto VARCHAR(100) UNIQUE NOT NULL,
            stock_producto INT NOT NULL,
            precio_venta DECIMAL(10, 2) NOT NULL,
            tiempo_produccion DECIMAL(10,2) DEFAULT 0.00,
            costo_indirecto DECIMAL(10, 2) NOT NULL,
            margen_ganancia REAL NOT NULL
        )
    ''')

    # --- TABLA 3: RECETAS (Clave Compuesta) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RECETAS (
            id_producto INT ZEROFILL NOT NULL,
            id_ingrediente INT ZEROFILL NOT NULL,
            cantidad_requerida REAL NOT NULL,

            PRIMARY KEY (id_producto, id_ingrediente),

            FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE CASCADE,
            FOREIGN KEY (id_ingrediente) REFERENCES INGREDIENTES(id_ingrediente) ON DELETE RESTRICT
        )
    ''')

    # --- TABLA 4, 5, 6 (Producción, Ventas, Pagos) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PRODUCCION (
            id_produccion INT ZEROFILL NOT NULL AUTO_INCREMENT PRIMARY KEY,
            id_producto INT ZEROFILL NOT NULL,
            cantidad_producida INT NOT NULL,
            fecha_produccion DATETIME NOT NULL,
            FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto) ON DELETE RESTRICT
        )
    ''')

    # cursor.execute('''
    #    CREATE TABLE IF NOT EXISTS VENTAS (
    #       id_venta INT AUTO_INCREMENT PRIMARY KEY,
    #       id_producto INT NOT NULL,
    #      cantidad_vendida INT NOT NULL,
    #      precio_unitario_final DECIMAL(10, 2) NOT NULL,
    #      fecha_venta DATETIME NOT NULL,
    #     FOREIGN KEY (id_producto) REFERENCES PRODUCTOS(id_producto)
    # )
    # ''')

    # cursor.execute('''
    #   CREATE TABLE IF NOT EXISTS PAGOS (
    #     id_pago INT AUTO_INCREMENT PRIMARY KEY,
    #      id_venta INT NOT NULL,
    #    metodo_pago VARCHAR(50) NOT NULL,
    #   monto_pago DECIMAL(10, 2) NOT NULL,
    #  FOREIGN KEY (id_venta) REFERENCES VENTAS(id_venta)
    #     )
    # ''')

    # Insertar datos de prueba para poder calcular costos
    cursor.execute('SELECT COUNT(*) FROM PRODUCTOS')
    if cursor.fetchone()[0] == 0:
        query = """
                INSERT INTO PRODUCTOS
                (nombre_producto, stock_producto, precio_venta, tiempo_produccion, costo_indirecto, margen_ganancia)
                VALUES (%s, %s, %s, %s, %s, %s) \
                """
        cursor.execute(query, ('Tarta de Manzana', 10, 0.0, 0.25, 1.50, 0.40))

    conn.commit()
    conn.close()