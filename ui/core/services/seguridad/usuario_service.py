"""
Servicio para gestión de usuarios (CRUD).
Contiene validaciones de negocio para crear, listar, actualizar y eliminar usuarios.
"""

import bcrypt
from ui.core.services.base.service_result import ServiceResult


class UsuarioService:
    """Lógica de negocio para usuarios."""

    ROLES_VALIDOS = ("admin", "visitante")

    def __init__(self, usuario_repository):
        self._repo = usuario_repository

    def crear_usuario(self, username: str, password: str, role: str, question: str, answer: str) -> ServiceResult:
        """
        Crea un nuevo usuario.
        Valida que el username sea único, la contraseña sea fuerte y los campos no estén vacíos.
        """
        # Validaciones
        if not username or len(username) < 3:
            return ServiceResult.error("El nombre de usuario debe tener al menos 3 caracteres.")
        if len(password) < 6:
            return ServiceResult.error("La contraseña debe tener al menos 6 caracteres.")
        if not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            return ServiceResult.error("La contraseña debe tener al menos una mayúscula y un número.")
        if not question or not answer:
            return ServiceResult.error("Pregunta y respuesta de seguridad son requeridas.")
        if role not in self.ROLES_VALIDOS:
            return ServiceResult.error("Rol inválido.")

        # Verificar duplicado
        existente = self._repo.obtener(username)
        if existente:
            return ServiceResult.error("El nombre de usuario ya está en uso.")

        # Hashear
        hashed_pass = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        hashed_answer = bcrypt.hashpw(answer.lower().encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        datos = {
            "username": username,
            "password": hashed_pass,
            "role": role,
            "question": question,
            "answer": hashed_answer
        }
        try:
            self._repo.crear(datos)
            return ServiceResult.ok("Usuario creado exitosamente.")
        except Exception as e:
            return ServiceResult.error(str(e))

    def actualizar_usuario(
        self,
        username: str,
        role: str,
        question: str,
        answer: str = "",
        password: str = "",
    ) -> ServiceResult:
        """
        Actualiza rol, pregunta de seguridad y, opcionalmente, respuesta y
        contraseña de un usuario existente.

        `answer` y `password` son opcionales: si vienen vacíos, no se
        tocan (se mantiene el hash guardado). Si vienen, se validan y
        se rehashean igual que en creación.
        """
        if not username:
            return ServiceResult.error("Usuario no especificado.")
        if role not in self.ROLES_VALIDOS:
            return ServiceResult.error("Rol inválido.")
        if not question:
            return ServiceResult.error("La pregunta de seguridad es requerida.")

        existente = self._repo.obtener(username)
        if not existente:
            return ServiceResult.error("Usuario no encontrado.")

        # Protección: no permitir sacarle el rol admin al usuario 'admin'.
        if username == "admin" and role != "admin":
            return ServiceResult.error("No se puede cambiar el rol del administrador.")

        datos = {"role": role, "question": question}

        if answer:
            datos["answer"] = bcrypt.hashpw(answer.lower().encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        if password:
            if len(password) < 6:
                return ServiceResult.error("La contraseña debe tener al menos 6 caracteres.")
            if not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
                return ServiceResult.error("La contraseña debe tener al menos una mayúscula y un número.")
            datos["password"] = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        try:
            self._repo.actualizar(username, datos)
            return ServiceResult.ok("Usuario actualizado correctamente.")
        except Exception as e:
            return ServiceResult.error(str(e))

    def listar_usuarios(self) -> ServiceResult:
        """Lista todos los usuarios."""
        try:
            users = self._repo.listar()
            return ServiceResult.ok(datos=users)
        except Exception as e:
            return ServiceResult.error(str(e))

    def eliminar_usuario(self, username: str) -> ServiceResult:
        """Elimina un usuario. No permite eliminar al admin."""
        if username == "admin":
            return ServiceResult.error("No se puede eliminar al usuario administrador.")
        try:
            success = self._repo.eliminar(username)
            if success:
                return ServiceResult.ok("Usuario eliminado.")
            return ServiceResult.error("No se pudo eliminar.")
        except Exception as e:
            return ServiceResult.error(str(e))