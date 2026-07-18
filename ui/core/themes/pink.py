# app_theme_pink.py
from .base_theme import AppTheme

APP_THEME_PINK = AppTheme(
    # Colores principales (rosa)
    primary="#EC4899",          # Pink 500
    primary_hover="#DB2777",    # Pink 600

    # Fondo y superficies (tonos oscuros neutros)
    background="#0D1117",
    surface="#161B22",
    card="#1C2128",

    # Bordes
    border="#30363D",

    # Texto
    text="#FFFFFF",
    text_secondary="#A1A1AA",

    # Estados
    success="#16A34A",
    warning="#FACC15",
    error="#DC2626",
    info="#8B5CF6",             # Violeta para contraste (o un rosa claro)

    # Texto de botones
    button_text="#FFFFFF",

    # Barra lateral
    sidebar="#161B22",
    sidebar_selected="#EC4899", # Mismo que primary

    # Tablas
    table_header="#1F2937",
    table_row_hover="#22272E",
)