# app_theme_green.py
from .base_theme import AppTheme

APP_THEME_GREEN = AppTheme(
    # Colores principales (verde esmeralda)
    primary="#10B981",          # Emerald 500
    primary_hover="#059669",    # Emerald 600

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
    success="#16A34A",          # Verde éxito (se mantiene)
    warning="#FACC15",
    error="#DC2626",
    info="#0EA5E9",             # Azul cielo (opcional, se puede cambiar a un verde-azulado)

    # Texto de botones
    button_text="#FFFFFF",

    # Barra lateral
    sidebar="#161B22",
    sidebar_selected="#10B981", # Mismo que primary

    # Tablas
    table_header="#1F2937",
    table_row_hover="#22272E",
)