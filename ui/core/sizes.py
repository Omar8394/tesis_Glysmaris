"""
============================================================
Sistema La Dulce Tía

Archivo:
    sizes.py

Responsabilidad:
    Centralizar todos los tamaños utilizados por la interfaz.

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


class AppSize:
    """
    Tamaños oficiales de la interfaz.

    Todos los componentes deberán utilizar estos valores
    para mantener consistencia visual en todo el sistema.
    """

    # =====================================================
    # CAMPOS DE TEXTO
    # =====================================================

    FIELD_SMALL = 180
    FIELD_MEDIUM = 250
    FIELD_LARGE = 350
    FIELD_EXTRA_LARGE = 500

    FIELD_HEIGHT = 42

    # =====================================================
    # BOTONES
    # =====================================================

    BUTTON_SMALL_WIDTH = 110
    BUTTON_MEDIUM_WIDTH = 150
    BUTTON_LARGE_WIDTH = 200

    BUTTON_HEIGHT = 42

    # =====================================================
    # DROPDOWN
    # =====================================================

    DROPDOWN_SMALL = 180
    DROPDOWN_MEDIUM = 250
    DROPDOWN_LARGE = 350

    # =====================================================
    # TARJETAS
    # =====================================================

    CARD_SMALL_WIDTH = 300
    CARD_MEDIUM_WIDTH = 450
    CARD_LARGE_WIDTH = 650

    CARD_MIN_HEIGHT = 120

    # =====================================================
    # PANEL LATERAL
    # =====================================================

    SIDEBAR_WIDTH = 260

    # =====================================================
    # DIÁLOGOS
    # =====================================================

    DIALOG_SMALL_WIDTH = 400
    DIALOG_MEDIUM_WIDTH = 600
    DIALOG_LARGE_WIDTH = 800

    # =====================================================
    # ICONOS
    # =====================================================

    ICON_SMALL = 18
    ICON_MEDIUM = 24
    ICON_LARGE = 32
    ICON_EXTRA_LARGE = 40

    # =====================================================
    # TABLAS
    # =====================================================

    TABLE_ROW_HEIGHT = 44
    TABLE_HEADER_HEIGHT = 46

    # =====================================================
    # AVATARES / IMÁGENES
    # =====================================================

    IMAGE_SMALL = 32
    IMAGE_MEDIUM = 48
    IMAGE_LARGE = 64
    IMAGE_EXTRA_LARGE = 96

    # =====================================================
    # BARRA DE BÚSQUEDA
    # =====================================================

    SEARCH_BAR_WIDTH = 350

    # =====================================================
    # HISTORIAL
    # =====================================================

    HISTORY_PANEL_WIDTH = 350

    # =====================================================
    # RESUMEN
    # =====================================================

    SUMMARY_CARD_WIDTH = 260
    SUMMARY_CARD_HEIGHT = 100

    # =====================================================
    # CALENDARIO
    # =====================================================

    DATE_PICKER_WIDTH = 320

    # =====================================================
    # VENTANA PRINCIPAL
    # =====================================================

    MIN_WINDOW_WIDTH = 1200
    MIN_WINDOW_HEIGHT = 700