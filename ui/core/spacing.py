"""
============================================================
Sistema La Dulce Tía

Archivo:
    spacing.py

Responsabilidad:
    Centralizar todos los espaciados utilizados por la interfaz.

Utilizado por:
    - Componentes
    - Vistas
    - Diálogos
    - Tarjetas
    - Formularios

No debe:
    - Crear controles.
    - Importar vistas.
    - Contener lógica del negocio.
============================================================
"""


class AppSpacing:
    """
    Escala oficial de espaciados del sistema.

    Todas las separaciones, márgenes y paddings deberán
    utilizar exclusivamente estos valores.
    """

    # =====================================================
    # ESCALA BASE
    # =====================================================

    NONE = 0

    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32
    HUGE = 40

    # =====================================================
    # PADDING
    # =====================================================

    PAGE_PADDING = XL
    CARD_PADDING = LG
    DIALOG_PADDING = XL
    PANEL_PADDING = XL
    FORM_PADDING = LG

    # =====================================================
    # SPACING
    # =====================================================

    SECTION_SPACING = XXL
    CONTROL_SPACING = LG
    ITEM_SPACING = MD
    BUTTON_SPACING = SM

    # =====================================================
    # MÁRGENES
    # =====================================================

    PAGE_MARGIN = LG
    CARD_MARGIN = MD

    # =====================================================
    # TABLAS
    # =====================================================

    TABLE_CELL_PADDING = SM
    TABLE_ROW_SPACING = XS

    # =====================================================
    # SIDEBAR
    # =====================================================

    SIDEBAR_PADDING = LG