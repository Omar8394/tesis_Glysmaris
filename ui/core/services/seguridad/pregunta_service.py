"""
Servicio para preguntas de seguridad.
"""

from ui.core.services.base.service_result import ServiceResult


class PreguntaService:
    """Lógica de negocio para preguntas de seguridad."""

    def __init__(self, pregunta_repository):
        self._repo = pregunta_repository

    def obtener_pregunta_aleatoria(self) -> ServiceResult:
        """Devuelve una pregunta aleatoria."""
        try:
            pregunta = self._repo.obtener_aleatoria()
            if pregunta:
                return ServiceResult.ok(datos={"question": pregunta})
            return ServiceResult.error("No hay preguntas disponibles.")
        except Exception as e:
            return ServiceResult.error(str(e))

    def listar_preguntas(self) -> ServiceResult:
        """Devuelve todas las preguntas."""
        try:
            preguntas = self._repo.obtener_todas()
            return ServiceResult.ok(datos=preguntas)
        except Exception as e:
            return ServiceResult.error(str(e))