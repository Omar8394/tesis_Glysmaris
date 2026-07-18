from ui.core.repositories.base.crud_repository import CRUDRepository

class UsuarioRepository(CRUDRepository):
    """CRUD de usuarios."""

    def crear(self, datos: dict) -> int:
        query = """
            INSERT INTO users (username, password, role, security_question, security_answer)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor = self._cursor()
        cursor.execute(query, (
            datos["username"],
            datos["password"],
            datos["role"],
            datos["question"],
            datos["answer"]
        ))
        self._commit()
        return cursor.lastrowid

    def listar(self) -> list[dict]:
        query = "SELECT username, role FROM users"
        cursor = self._cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def obtener(self, username: str) -> dict | None:
        query = "SELECT * FROM users WHERE username = %s"
        cursor = self._cursor()
        cursor.execute(query, (username,))
        return cursor.fetchone()

    def actualizar(self, username: str, datos: dict) -> bool:
        # Implementar si es necesario
        pass

    def eliminar(self, username: str) -> bool:
        query = "DELETE FROM users WHERE username = %s"
        cursor = self._cursor()
        cursor.execute(query, (username,))
        self._commit()
        return cursor.rowcount > 0

    def buscar(self, texto: str) -> list[dict]:
        query = "SELECT username, role FROM users WHERE username LIKE %s"
        cursor = self._cursor()
        cursor.execute(query, (f"%{texto}%",))
        return cursor.fetchall()