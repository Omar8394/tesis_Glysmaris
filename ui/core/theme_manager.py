from __future__ import annotations

from typing import Dict

from .themes.base_theme import AppTheme

from .themes.blue import APP_THEME_BLUE
from .themes.chocolate import APP_THEME_CHOCOLATE
from .themes.green import APP_THEME_GREEN
from .themes.pink import APP_THEME_PINK
from .themes.dark import APP_THEME_DARK
from .themes.dulce_tia import APP_THEME_LA_DULCE_TIA


class ThemeManager:
    """
    Administrador central de temas de la aplicación.

    Toda la interfaz debe obtener los colores desde aquí.

    Ejemplo:

        from ui.core.theme_manager import ThemeManager

        color = ThemeManager.theme.primary
    """

    _themes: Dict[str, AppTheme] = {
        "dulce_tia": APP_THEME_LA_DULCE_TIA,
        "blue": APP_THEME_BLUE,
        "chocolate": APP_THEME_CHOCOLATE,
        "green": APP_THEME_GREEN,
        "pink": APP_THEME_PINK,
        "dark": APP_THEME_DARK,
    }

    _current_theme: str = "dulce_tia"

    @classmethod
    def set_theme(cls, theme_name: str) -> None:
        """
        Cambia el tema activo.
        """

        if theme_name not in cls._themes:
            raise ValueError(f"Tema '{theme_name}' no existe.")

        cls._current_theme = theme_name

    @classmethod
    def get_theme(cls) -> AppTheme:
        """
        Devuelve el tema actualmente activo.
        """

        return cls._themes[cls._current_theme]

    @classmethod
    @property
    def theme(cls) -> AppTheme:
        """
        Acceso rápido al tema activo.

        Ejemplo:

            ThemeManager.theme.primary
        """

        return cls.get_theme()

    @classmethod
    def available_themes(cls) -> list[str]:
        """
        Devuelve la lista de temas disponibles.
        """

        return list(cls._themes.keys())

    @classmethod
    def current_theme_name(cls) -> str:
        """
        Devuelve el nombre del tema actual.
        """

        return cls._current_theme