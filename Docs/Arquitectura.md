# ThemeManager

## Responsabilidad

Centralizar la gestión de temas visuales del sistema.

## Objetivos

- Mantener un único tema activo.
- Evitar colores hardcodeados en las vistas.
- Permitir cambiar el tema sin modificar el resto del sistema.
- Preparar la aplicación para guardar la preferencia de tema por usuario.

## Uso

Todas las vistas deberán obtener los colores mediante:

```python
from ui.core.theme_manager import ThemeManager

ThemeManager.theme.primary
ThemeManager.theme.background
ThemeManager.theme.card