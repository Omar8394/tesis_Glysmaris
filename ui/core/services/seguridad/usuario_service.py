"""
Servicio para gestión de usuarios (CRUD).
Contiene validaciones de negocio para crear, listar y eliminar usuarios.
"""

import bcrypt
from ui.core.services.base.service_result import ServiceResult


class UsuarioService:
    """Lógica de negocio para usuarios."""

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