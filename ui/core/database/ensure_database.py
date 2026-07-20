"""
============================================================
Sistema La Dulce Tía

Archivo:
    ensure_databases.py

Responsabilidad:
    Asegurar que las bases de datos de configuración existan.
    Crea las bases de datos si no existen, usando los nombres
    definidos en config.py.

    Este script debe ejecutarse ANTES de cualquier intento de
    conexión a las bases de datos (por ejemplo, antes de migrar
    las tablas), ya que DatabaseFactory fallará si la base de
    datos no existe.

Uso:
    - Ejecutar directamente: python -m ui.core.database.ensure_databases
    - Importar y llamar a crear_bases_de_datos_si_no_existen()

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import pymysql
import sys
from ui.core.database.config import DB_HOST, DB_USER, DB_PASSWORD, DB_SEGURIDAD, DB_OPERACIONES


def crear_bases_de_datos_si_no_existen() -> None:
    """
    Conecta a MySQL (sin seleccionar base de datos) y crea las bases
    de datos definidas en config.py si no existen.
    """
    print(f"[DEBUG] Intentando conectar a MySQL en {DB_HOST} con usuario {DB_USER}...")
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    except pymysql.Error as e:
        print(f"❌ Error de conexión a MySQL: {e}")
        raise RuntimeError(f"Error al conectar a MySQL: {e}") from e

    try:
        with conn.cursor() as cursor:
            # Verificar si existen las bases de datos
            cursor.execute("SHOW DATABASES")
            existing_dbs = [row['Database'] for row in cursor.fetchall()]
            print(f"[DEBUG] Bases de datos existentes: {existing_dbs}")

            # Crear base de datos de seguridad si no existe
            if DB_SEGURIDAD not in existing_dbs:
                print(f"[INFO] Creando base de datos '{DB_SEGURIDAD}'...")
                cursor.execute(f"CREATE DATABASE `{DB_SEGURIDAD}`")
            else:
                print(f"[INFO] Base de datos '{DB_SEGURIDAD}' ya existe.")

            # Crear base de datos de operaciones si no existe
            if DB_OPERACIONES not in existing_dbs:
                print(f"[INFO] Creando base de datos '{DB_OPERACIONES}'...")
                cursor.execute(f"CREATE DATABASE `{DB_OPERACIONES}`")
            else:
                print(f"[INFO] Base de datos '{DB_OPERACIONES}' ya existe.")

            print(f"✅ Bases de datos aseguradas: {DB_SEGURIDAD}, {DB_OPERACIONES}")
    except pymysql.Error as e:
        print(f"❌ Error al crear bases de datos: {e}")
        raise RuntimeError(f"Error al crear bases de datos: {e}") from e
    finally:
        conn.close()


if __name__ == "__main__":
    # Ejecutar directamente para crear las bases de datos si no existen
    try:
        crear_bases_de_datos_si_no_existen()
        print("\n✅ Script ejecutado con éxito.")
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        sys.exit(1)