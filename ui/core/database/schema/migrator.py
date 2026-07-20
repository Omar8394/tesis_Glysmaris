"""
============================================================
Sistema La Dulce Tía

Archivo:
    migrator.py

Responsabilidad:
    Aplicar todos los esquemas de base de datos (seguridad y operaciones)
    al iniciar la aplicación.

    Crea las tablas si no existen, sin borrar datos existentes.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import bcrypt

from ui.core.database.factory import DatabaseFactory
from ui.core.database.schema.seguridad.schema import SCHEMA_SEGURIDAD
from ui.core.database.schema.operaciones.schema import SCHEMA_OPERACIONES
from ui.core.database.ensure_database import crear_bases_de_datos_si_no_existen

# ============================================================
# Helpers para migraciones seguras de columnas/llaves foráneas
# ============================================================
# MySQL/MariaDB no soportan "DROP COLUMN IF EXISTS" combinado con
# "ADD COLUMN IF NOT EXISTS" en la misma sentencia, y NINGUNA versión
# soporta "ADD FOREIGN KEY IF NOT EXISTS". Por eso estos cambios se
# aplican desde Python: se pregunta primero si hace falta, y solo
# entonces se ejecuta el ALTER TABLE correspondiente. Esto es seguro
# de correr en cada arranque de la aplicación.

def _columna_existe(cursor, tabla: str, columna: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS total FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (tabla, columna),
    )
    return cursor.fetchone()["total"] > 0


def _fk_existe_en_columna(cursor, tabla: str, columna: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """,
        (tabla, columna),
    )
    return cursor.fetchone()["total"] > 0


def _agregar_columna_si_no_existe(cursor, tabla: str, columna: str, definicion: str) -> None:
    if not _columna_existe(cursor, tabla, columna):
        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")


def _eliminar_columna_si_existe(cursor, tabla: str, columna: str) -> None:
    if _columna_existe(cursor, tabla, columna):
        cursor.execute(f"ALTER TABLE {tabla} DROP COLUMN {columna}")


def _renombrar_columna_si_hace_falta(cursor, tabla: str, columna_vieja: str, columna_nueva: str, definicion: str) -> None:
    """Renombra columna_vieja -> columna_nueva solo si la vieja existe y la nueva todavía no."""
    if _columna_existe(cursor, tabla, columna_vieja) and not _columna_existe(cursor, tabla, columna_nueva):
        cursor.execute(f"ALTER TABLE {tabla} CHANGE COLUMN {columna_vieja} {columna_nueva} {definicion}")


def _aplicar_migraciones_manuales(cursor) -> None:
    """
    Ajustes a tablas ya existentes que no se expresan bien como
    CREATE TABLE IF NOT EXISTS (quitar/agregar columnas, agregar
    foreign keys). Cada cambio revisa primero si hace falta, así
    que correr esto en cada arranque es seguro y no falla sin
    importar cuántas veces ya se haya aplicado.
    """
    # --- PRODUCTOS: alinear columnas con lo que ProductoRepository ---
    # realmente usa (visto en productos_repository.py):
    #
    # ⚠️ Una versión anterior de esta función eliminaba "empaques" y
    # "costos_indirectos" para reemplazarlas por mano_obra_valor/tipo.
    # Eso estaba basado en un plan viejo: ProductoRepository en
    # realidad SÍ guarda los totales de empaques/costos indirectos en
    # esas dos columnas, y usa "mano_obra" + "mano_obra_es_porcentaje"
    # (que ya existían desde el schema original, sin necesitar
    # mano_obra_valor/tipo). Se revierte ese cambio acá: si esas
    # columnas ya se habían eliminado en tu base real, se vuelven a
    # crear sin perder nada más.
    _agregar_columna_si_no_existe(cursor, "PRODUCTOS", "empaques", "DECIMAL(10,2) DEFAULT 0")
    _agregar_columna_si_no_existe(cursor, "PRODUCTOS", "costos_indirectos", "DECIMAL(10,2) DEFAULT 0")

    # ProductoRepository consulta/guarda la columna como "categoria",
    # pero la tabla original la creó como "categoria_producto".
    _renombrar_columna_si_hace_falta(
        cursor, "PRODUCTOS", "categoria_producto", "categoria", "VARCHAR(50)"
    )

    # --- PRODUCTO_PRESENTACIONES: nuevos campos ---
    _agregar_columna_si_no_existe(cursor, "PRODUCTO_PRESENTACIONES", "diametro", "DECIMAL(10,2) NULL")
    _agregar_columna_si_no_existe(cursor, "PRODUCTO_PRESENTACIONES", "peso", "DECIMAL(10,2) NULL")
    _agregar_columna_si_no_existe(cursor, "PRODUCTO_PRESENTACIONES", "id_receta", "INT NULL")
    _agregar_columna_si_no_existe(cursor, "PRODUCTO_PRESENTACIONES", "costo", "DECIMAL(10,2) DEFAULT 0")
    _agregar_columna_si_no_existe(cursor, "PRODUCTO_PRESENTACIONES", "precio", "DECIMAL(10,2) DEFAULT 0")
    _agregar_columna_si_no_existe(
        cursor, "PRODUCTO_PRESENTACIONES", "estado",
        "ENUM('activo', 'inactivo') DEFAULT 'activo'"
    )

    if not _fk_existe_en_columna(cursor, "PRODUCTO_PRESENTACIONES", "id_receta"):
        cursor.execute(
            """
            ALTER TABLE PRODUCTO_PRESENTACIONES
            ADD FOREIGN KEY (id_receta) REFERENCES RECETAS(id_receta) ON DELETE SET NULL
            """
        )


def migrar_todas_las_tablas() -> None:
    """
    Ejecuta todos los scripts de creación de tablas en ambas bases de datos.

    Utiliza DatabaseFactory para obtener las conexiones y ejecuta
    las sentencias SQL definidas en los schemas correspondientes."""

    crear_bases_de_datos_si_no_existen()
    
    # ============================================================
    # 1. BASE DE DATOS DE SEGURIDAD
    # ============================================================
    db_seg = DatabaseFactory.get_seguridad()
    try:
        with db_seg.cursor() as cursor:
            for sql in SCHEMA_SEGURIDAD:
                cursor.execute(sql)
        db_seg.commit()
    except Exception as e:
        db_seg.rollback()
        raise RuntimeError(f"Error al crear tablas de seguridad: {e}") from e

    # ============================================================
    # 2. BASE DE DATOS DE OPERACIONES
    # ============================================================
    db_op = DatabaseFactory.get_operaciones()
    try:
        with db_op.cursor() as cursor:
            for sql in SCHEMA_OPERACIONES:
                cursor.execute(sql)
            _aplicar_migraciones_manuales(cursor)
        db_op.commit()
    except Exception as e:
        db_op.rollback()
        raise RuntimeError(f"Error al crear tablas de operaciones: {e}") from e

 # ============================================================
    # 3. CREAR ADMINISTRADOR POR DEFECTO (SI NO EXISTE)
    # ============================================================
    _crear_admin_si_no_existe()


def _crear_admin_si_no_existe() -> None:
    """
    Crea el usuario administrador por defecto (admin / Admin123)
    si no existe en la base de datos.
    """
    db = DatabaseFactory.get_seguridad()
    cursor = db.cursor()

    # Verificar si ya existe el admin
    cursor.execute("SELECT COUNT(*) AS total FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    if result["total"] > 0:
        return  # Ya existe, no hacemos nada

    # Hashear contraseña y respuesta de seguridad
    hashed_password = bcrypt.hashpw("Admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    hashed_answer = bcrypt.hashpw("anaco".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Insertar admin
    cursor.execute(
        """
        INSERT INTO users
        (username, password, role, security_question, security_answer)
        VALUES (%s, %s, %s, %s, %s)
        """,
        ("admin", hashed_password, "admin", "¿Ciudad donde naciste?", hashed_answer)
    )
    db.commit()