"""
Repositorio para operaciones de preguntas de seguridad.
"""

from ui.core.repositories.base.repository import Repository


class PreguntaRepository(Repository):
    """Acceso a preguntas de seguridad."""

    def obtener_todas(self) -> list[dict]:
        query = "SELECT question_text FROM security_questions"
        cursor = self._cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def obtener_aleatoria(self) -> str | None:
        query = "SELECT question_text FROM security_questions ORDER BY RAND() LIMIT 1"
        cursor = self._cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        return row["question_text"] if row else None