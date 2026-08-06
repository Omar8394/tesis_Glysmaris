from ui.core.repositories.base.crud_repository import CRUDRepository


class UsuarioRepository(CRUDRepository):
    """CRUD de usuarios."""

    # Mapeo entre las claves que usan los servicios (question/answer)
    # y las columnas reales de la tabla `users` (security_question/
    # security_answer). Se centraliza acá para no repetirlo en crear()
    # y actualizar().
    _MAPA_COLUMNAS = {
        "password": "password",
        "role": "role",
        "question": "security_question",
        "answer": "security_answer",
    }

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
        """
        Actualiza campos de un usuario existente.

        `datos` acepta cualquier combinación de las claves:
        password, role, question, answer (mismos nombres que usa
        UsuarioService, no los nombres de columna reales). Solo se
        arman los SET de las claves presentes y con valor no nulo,
        así se puede actualizar el rol sin tocar la contraseña, etc.
        """
        campos = []
        valores = []
        for clave, columna in self._MAPA_COLUMNAS.items():
            if datos.get(clave) is not None:
                campos.append(f"{columna} = %s")
                valores.append(datos[clave])

        if not campos:
            return False

        valores.append(username)
        query = f"UPDATE users SET {', '.join(campos)} WHERE username = %s"
        cursor = self._cursor()
        cursor.execute(query, tuple(valores))
        self._commit()
        # Nota: no usamos cursor.rowcount > 0 como indicador de éxito
        # porque MySQL devuelve 0 filas afectadas cuando el UPDATE no
        # cambia ningún valor (ej. reasignar el mismo rol), aunque el
        # usuario exista y la query haya sido válida. La existencia del
        # usuario ya se valida en UsuarioService antes de llamar acá.
        return True

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