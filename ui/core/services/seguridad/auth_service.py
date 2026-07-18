import bcrypt
from ui.core.services.base.service_result import ServiceResult


class AuthService:
    def __init__(self, auth_repository):
        self._repo = auth_repository

    def login(self, username: str, password: str) -> ServiceResult:
        
        if not username or not password:
            return ServiceResult.error("Usuario y contraseña son requeridos.")

        
        try:
            user = self._repo.obtener_usuario_por_username(username)
            if not user:
                return ServiceResult.error("Usuario no encontrado.")
            stored_hash = user["password"]
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                return ServiceResult.ok(datos={"role": user["role"]})
            return ServiceResult.error("Contraseña incorrecta.")
        except Exception as e:
            return ServiceResult.error(str(e))

    def obtener_pregunta_seguridad(self, username: str) -> ServiceResult:
        """✅ Nuevo: para el primer paso de 'olvidé mi contraseña'. Antes se
        usaba PreguntaService.obtener_pregunta_aleatoria(), que no tiene
        relación con el usuario puntual — ahora se trae la pregunta real
        que ESE usuario eligió al registrarse."""
        if not username or not username.strip():
            return ServiceResult.error("Ingrese su nombre de usuario.")
        try:
            pregunta = self._repo.obtener_pregunta_seguridad(username)
            if not pregunta:
                return ServiceResult.error("Usuario no encontrado.")
            return ServiceResult.ok(datos={"question": pregunta})
        except Exception as e:
            return ServiceResult.error(str(e))

    def verificar_respuesta_seguridad(self, username: str, answer: str) -> ServiceResult:
        try:
            stored_hash = self._repo.obtener_respuesta_seguridad(username)
            if not stored_hash:
                return ServiceResult.error("Usuario no encontrado.")
            if bcrypt.checkpw(answer.lower().encode("utf-8"), stored_hash.encode("utf-8")):
                return ServiceResult.ok()
            return ServiceResult.error("Respuesta incorrecta.")
        except Exception as e:
            return ServiceResult.error(str(e))

    def resetear_password(self, username: str, answer: str, new_password: str) -> ServiceResult:
        # Validar nueva contraseña (puedes mover esta validación a un helper)
        if len(new_password) < 6:
            return ServiceResult.error("La contraseña debe tener al menos 6 caracteres.")
        if not any(c.isupper() for c in new_password):
            return ServiceResult.error("Debe tener una mayúscula.")
        if not any(c.isdigit() for c in new_password):
            return ServiceResult.error("Debe tener un número.")

        # Verificar respuesta
        verif = self.verificar_respuesta_seguridad(username, answer)
        if verif.fallo:
            return verif

        # Generar nuevo hash
        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        success = self._repo.actualizar_password(username, hashed)
        if success:
            return ServiceResult.ok("Contraseña actualizada correctamente.")
        return ServiceResult.error("No se pudo actualizar la contraseña.")