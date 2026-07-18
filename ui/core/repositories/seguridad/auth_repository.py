from ui.core.repositories.base.repository import Repository

class AuthRepository(Repository):
    """Acceso a datos de autenticación (verificar login, reset password)."""

    def obtener_usuario_por_username(self, username: str) -> dict | None:
        query = "SELECT password, role FROM users WHERE username = %s"
        cursor = self._cursor()
        cursor.execute(query, (username,))
        return cursor.fetchone()

    def obtener_respuesta_seguridad(self, username: str) -> str | None:
        query = "SELECT security_answer FROM users WHERE username = %s"
        cursor = self._cursor()
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        return row["security_answer"] if row else None

    def obtener_pregunta_seguridad(self, username: str) -> str | None:
        """✅ Nuevo: trae la pregunta de seguridad que ESE usuario eligió al
        registrarse (guardada directamente en su fila de 'users'). No hay
        que confundir esto con PreguntaRepository.obtener_aleatoria(), que
        tira cualquier pregunta del catálogo general y no sirve para
        verificar a un usuario puntual."""
        query = "SELECT security_question FROM users WHERE username = %s"
        cursor = self._cursor()
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        return row["security_question"] if row else None

    def actualizar_password(self, username: str, new_hashed_password: str) -> bool:
        query = "UPDATE users SET password = %s WHERE username = %s"
        cursor = self._cursor()
        cursor.execute(query, (new_hashed_password, username))
        self._commit()
        return cursor.rowcount > 0