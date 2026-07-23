"""
============================================================
Sistema La Dulce Tía

Archivo:
    schema_clientes_cxc.py

Responsabilidad:
    Sentencias CREATE TABLE para el módulo de Clientes y
    Cuentas por Cobrar (deudas generadas por ventas a crédito).

    Este archivo es un SNIPPET para incorporar dentro de la lista
    SCHEMA_OPERACIONES de schema.py (agregar estos bloques, en este
    orden: CLIENTES debe ir ANTES que VENTAS porque VENTAS.id_cliente
    la referencia; CUENTAS_POR_COBRAR y ABONOS_CUENTA deben ir
    DESPUÉS de VENTAS y VENTA_PAGOS).

    La columna VENTAS.id_cliente NO se agrega aquí como ALTER TABLE
    en texto plano (ver la nota que ya tienes en schema.py sobre
    "DROP COLUMN IF EXISTS" / "ADD FOREIGN KEY IF NOT EXISTS" no
    siendo válido en MySQL/MariaDB). Esa migración va en
    migrator.py, verificando antes en INFORMATION_SCHEMA:

        ALTER TABLE VENTAS ADD COLUMN id_cliente INT NULL
            AFTER cliente_telefono;
        ALTER TABLE VENTAS ADD FOREIGN KEY (id_cliente)
            REFERENCES CLIENTES(id_cliente) ON DELETE SET NULL;

Autor:
    Proyecto La Dulce Tía
============================================================
"""

SCHEMA_CLIENTES_CXC = [
    # ============================================================
    # A. CLIENTES
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS CLIENTES (
        id_cliente INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        cedula VARCHAR(20) UNIQUE,
        telefono VARCHAR(20),
        direccion VARCHAR(200),
        observaciones TEXT,
        activo BOOLEAN DEFAULT TRUE,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_nombre (nombre),
        INDEX idx_cedula (cedula)
    )
    """,

    # ============================================================
    # B. CUENTAS_POR_COBRAR (deudas generadas por ventas a crédito)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS CUENTAS_POR_COBRAR (
        id_cuenta INT AUTO_INCREMENT PRIMARY KEY,
        id_venta INT NOT NULL,
        id_cliente INT NULL,
        monto_total DECIMAL(10,2) NOT NULL,
        monto_abonado DECIMAL(10,2) NOT NULL DEFAULT 0,
        monto_pendiente DECIMAL(10,2) NOT NULL,
        estado ENUM('pendiente','parcial','pagada','anulada') NOT NULL DEFAULT 'pendiente',
        fecha_venta DATETIME NOT NULL,
        fecha_vencimiento DATE NULL,
        observaciones TEXT,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_venta) REFERENCES VENTAS(id_venta) ON DELETE CASCADE,
        FOREIGN KEY (id_cliente) REFERENCES CLIENTES(id_cliente) ON DELETE SET NULL,
        INDEX idx_estado (estado),
        INDEX idx_cliente (id_cliente),
        INDEX idx_venta (id_venta)
    )
    """,

    # ============================================================
    # C. ABONOS_CUENTA (pagos parciales que saldan una deuda)
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS ABONOS_CUENTA (
        id_abono INT AUTO_INCREMENT PRIMARY KEY,
        id_cuenta INT NOT NULL,
        monto DECIMAL(10,2) NOT NULL,
        metodo_pago ENUM('efectivo','debito','transferencia','pago_movil') NOT NULL,
        referencia VARCHAR(50),
        observaciones TEXT,
        usuario_registro VARCHAR(100),
        fecha_abono DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cuenta) REFERENCES CUENTAS_POR_COBRAR(id_cuenta) ON DELETE CASCADE,
        INDEX idx_cuenta (id_cuenta)
    )
    """,
]
