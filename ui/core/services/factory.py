# core/services/factory.py
"""
Fábrica de servicios del sistema.
Centraliza la creación de todas las capas de negocio.
"""

from ui.core.database.factory import DatabaseFactory
from ui.core.repositories.operaciones.ingrediente_repository import IngredienteRepository
from ui.core.repositories.seguridad.usuario_repository import UsuarioRepository
from ui.core.repositories.seguridad.auth_repository import AuthRepository
from ui.core.repositories.seguridad.pregunta_repository import PreguntaRepository
from ui.core.services.operaciones.ingrediente_service import IngredienteService
from ui.core.services.seguridad.auth_service import AuthService
from ui.core.services.seguridad.usuario_service import UsuarioService
from ui.core.services.seguridad.pregunta_service import PreguntaService
from ui.core.repositories.operaciones.recetas_repository import RecetasRepository 
from ui.core.services.operaciones.recetas_service import RecetasService
from ui.core.repositories.operaciones.productos_repository import ProductoRepository
from ui.core.services.operaciones.producto_service import ProductoService
from ui.core.repositories.operaciones.activo_repository import ActivoRepository
from ui.core.services.operaciones.activo_service import ActivoService
from ui.core.repositories.operaciones.mi_negocio_repository import ParametrosNegocioRepository
from ui.core.services.operaciones.mi_negocio_service import ParametrosNegocioService
from ui.core.services.operaciones.produccion_service import ProduccionService
from ui.core.repositories.operaciones.produccion_repository import ProduccionRepository
from ui.core.repositories.operaciones.estadisticas_repository import EstadisticasRepository
from ui.core.services.operaciones.estadisticas_service import EstadisticasService

class ServiceFactory:
    """Crea y cachea servicios."""

    _instances = {}

    @classmethod
    def get_ingrediente_service(cls):
        if "ingrediente" not in cls._instances:
            db = DatabaseFactory.get_operaciones()
            repo = IngredienteRepository(db)
            cls._instances["ingrediente"] = IngredienteService(repo)
        return cls._instances["ingrediente"]
    
    @classmethod
    def get_recetas_service(cls):
        if "recetas" not in cls._instances:
            db = DatabaseFactory.get_operaciones()
            repo = RecetasRepository(db)
            cls._instances["recetas"] = RecetasService(repo)
        return cls._instances["recetas"]
    
    @classmethod
    def get_producto_service(cls):
        if "producto" not in cls._instances:
            db = DatabaseFactory.get_operaciones()
            repo = ProductoRepository(db)
            recetas_service = cls.get_recetas_service()
            activo_service = cls.get_activo_service()
            ingrediente_service = cls.get_ingrediente_service()
            cls._instances["producto"] = ProductoService(
                repo, recetas_service, activo_service, ingrediente_service
            )
        return cls._instances["producto"]

    @classmethod
    def get_activo_service(cls):
        if "activo" not in cls._instances:
            db = DatabaseFactory.get_operaciones()
            repo = ActivoRepository(db)
            cls._instances["activo"] = ActivoService(repo)
        return cls._instances["activo"]

    @classmethod
    def get_produccion_service(cls):
        if "produccion" not in cls._instances:
            from ui.core.database.factory import DatabaseFactory

            db = DatabaseFactory.get_operaciones()
            repo = ProduccionRepository(db)
            service = ProduccionService(repo)

            # Inyectar servicios auxiliares (sin lote_service)
            service.set_servicios_auxiliares(
                ingrediente_service=cls.get_ingrediente_service(),
                activo_service=cls.get_activo_service(),
                producto_service=cls.get_producto_service(),
                recetas_service=cls.get_recetas_service(),
            )

            cls._instances["produccion"] = service
        return cls._instances["produccion"]


    @classmethod
    def get_estadisticas_service(cls) -> EstadisticasService:
        if "estadisticas" not in cls._instances:
            db = DatabaseFactory.get_operaciones()
            repo = EstadisticasRepository(db)
            cls._instances["estadisticas"] = EstadisticasService(repo)
        return cls._instances["estadisticas"]

    @classmethod
    def get_parametros_negocio_service(cls) -> ParametrosNegocioService:
        if "parametros_negocio" not in cls._instances:
            db = DatabaseFactory.get_operaciones()
            repo = ParametrosNegocioRepository(db)
            activo_service = cls.get_activo_service()
            cls._instances["parametros_negocio"] = ParametrosNegocioService(repo, activo_service)
        return cls._instances["parametros_negocio"]

    @classmethod
    def get_auth_service(cls) -> AuthService:
        if "auth" not in cls._instances:
            db = DatabaseFactory.get_seguridad()
            repo = AuthRepository(db)
            cls._instances["auth"] = AuthService(repo)
        return cls._instances["auth"]

    @classmethod
    def get_usuario_service(cls) -> UsuarioService:
        if "usuario" not in cls._instances:
            db = DatabaseFactory.get_seguridad()
            repo = UsuarioRepository(db)
            cls._instances["usuario"] = UsuarioService(repo)
        return cls._instances["usuario"]

    @classmethod
    def get_pregunta_service(cls) -> PreguntaService:
        if "pregunta" not in cls._instances:
            db = DatabaseFactory.get_seguridad()
            repo = PreguntaRepository(db)
            cls._instances["pregunta"] = PreguntaService(repo)
        return cls._instances["pregunta"]