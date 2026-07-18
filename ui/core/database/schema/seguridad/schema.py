"""
============================================================
Sistema La Dulce Tía

Archivo:
    schema.py

Responsabilidad:
    Definir el esquema de la base de datos de seguridad.

    Contiene las sentencias CREATE TABLE para:
        - users (usuarios del sistema)
        - security_questions (preguntas de seguridad)

    También inserta las preguntas por defecto si no existen.

    Nota: La creación del usuario administrador se realiza
    en migrator.py mediante un script de inicialización
    que utiliza bcrypt para hashear la contraseña.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

# ============================================================
# LISTA DE SENTENCIAS SQL
# ============================================================

SCHEMA_SEGURIDAD = [
    # ============================================================
    # TABLA USERS
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'visitante') NOT NULL,
        security_question VARCHAR(255) NOT NULL,
        security_answer VARCHAR(255) NOT NULL
    )
    """,
    # ============================================================
    # TABLA PREGUNTAS DE SEGURIDAD
    # ============================================================
    """
    CREATE TABLE IF NOT EXISTS security_questions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        question_text VARCHAR(191) UNIQUE NOT NULL
    )
    """,
    # ============================================================
    # INSERTAR PREGUNTAS POR DEFECTO (SI NO EXISTEN)
    # ============================================================
    """
    INSERT INTO security_questions (question_text)
    SELECT * FROM (SELECT '¿Cuál es el nombre de tu primera mascota?') AS tmp
    WHERE NOT EXISTS (
        SELECT 1 FROM security_questions WHERE question_text = '¿Cuál es el nombre de tu primera mascota?'
    )
    """,
    """
    INSERT INTO security_questions (question_text)
    SELECT * FROM (SELECT '¿Cuál es tu comida favorita?') AS tmp
    WHERE NOT EXISTS (
        SELECT 1 FROM security_questions WHERE question_text = '¿Cuál es tu comida favorita?'
    )
    """,
    """
    INSERT INTO security_questions (question_text)
    SELECT * FROM (SELECT '¿Nombre de tu mejor amigo de la infancia?') AS tmp
    WHERE NOT EXISTS (
        SELECT 1 FROM security_questions WHERE question_text = '¿Nombre de tu mejor amigo de la infancia?'
    )
    """,
    """
    INSERT INTO security_questions (question_text)
    SELECT * FROM (SELECT '¿Cuál es tu película favorita?') AS tmp
    WHERE NOT EXISTS (
        SELECT 1 FROM security_questions WHERE question_text = '¿Cuál es tu película favorita?'
    )
    """,
    """
    INSERT INTO security_questions (question_text)
    SELECT * FROM (SELECT '¿Ciudad donde naciste?') AS tmp
    WHERE NOT EXISTS (
        SELECT 1 FROM security_questions WHERE question_text = '¿Ciudad donde naciste?'
    )
    """,
]