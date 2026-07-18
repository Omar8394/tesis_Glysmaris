"""
============================================================
Sistema La Dulce Tía

Archivo:
    radius.py

Responsabilidad:
    Centralizar los radios de borde utilizados por toda
    la interfaz.

Utilizado por:
    - Botones
    - TextFields
    - Dropdowns
    - Tarjetas
    - Diálogos

No debe:
    - Crear controles.
    - Importar vistas.
    - Contener lógica del negocio.
============================================================
"""


class AppRadius:
    """
    Radios oficiales del sistema.

    Todos los controles deberán utilizar estos valores
    para mantener una apariencia uniforme.
    """

    # =====================================================
    # ESCALA BASE
    # =====================================================

    NONE = 0

    XS = 4
    SM = 6
    MD = 8
    LG = 10
    XL = 12
    XXL = 16
    ROUND = 20

    # =====================================================
    # COMPONENTES
    # =====================================================

    BUTTON = LG

    TEXTFIELD = LG

    DROPDOWN = LG

    CARD = XL

    DIALOG = XL

    SIDEBAR = 0

    CHIP = ROUND

    IMAGE = XL