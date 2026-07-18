"""
============================================================
Sistema La Dulce Tía

Archivo:
    typography.py

Responsabilidad:
    Centralizar toda la tipografía utilizada por la interfaz.

Utilizado por:
    - Componentes
    - Vistas
    - Diálogos
    - Tablas
    - Formularios

No debe:
    - Crear controles.
    - Importar vistas.
    - Contener lógica del negocio.
============================================================
"""

import flet as ft


class AppTypography:
    """
    Configuración oficial de tipografía del sistema.
    """

    # =====================================================
    # FUENTE
    # =====================================================

    FONT_FAMILY = "Segoe UI"

    # =====================================================
    # TAMAÑOS
    # =====================================================

    DISPLAY = 30

    PAGE_TITLE = 24

    SECTION_TITLE = 18

    CARD_TITLE = 16

    SUBTITLE = 15

    BODY = 14

    SMALL = 13

    CAPTION = 12

    TINY = 11

    # =====================================================
    # PESOS
    # =====================================================

    LIGHT = ft.FontWeight.W_300

    NORMAL = ft.FontWeight.W_400

    MEDIUM = ft.FontWeight.W_500

    SEMIBOLD = ft.FontWeight.W_600

    BOLD = ft.FontWeight.BOLD

    EXTRA_BOLD = ft.FontWeight.W_800

    # =====================================================
    # ALTURAS
    # =====================================================

    LINE_HEIGHT = 1.3

    TITLE_LINE_HEIGHT = 1.2

    # =====================================================
    # USOS MÁS FRECUENTES
    # =====================================================

    BUTTON_SIZE = BODY

    INPUT_SIZE = BODY

    TABLE_SIZE = SMALL

    DIALOG_TITLE = SECTION_TITLE

    DIALOG_TEXT = BODY