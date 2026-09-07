"""
helpers_ps

Paquete de herramientas para análisis, gráficos, métricas y presentación.
"""

# ============================================================
# Versión del paquete
# ============================================================

try:
    from importlib.metadata import version

    __version__ = version("helpers_ps")
except Exception:
    __version__ = "0.0.0"


from helpers_ps.GlobVars import (
    PALETA_COLORES
)

# ============================================================
# API pública - paquetes alternos
# ============================================================

from . import (
    Calcs,
    Ppt,
    Excel,
    DfStyling
)

# ============================================================
# API pública - Paquete principal
# ============================================================
from .MtpltGraph import (
    GraphMtplt,
    set_graph_theme
)


# ============================================================
# Control explícito de objetos públicos
# ============================================================

__all__ = [
    "__version__",

    # Gráficos
    "GraphMtplt",
    "set_graph_theme",

    #Styling de DF
    "DfStyling",

    #Alternate packages
    "Calcs",
    "Ppt",
    "Excel",
    "PALETA_COLORES"
]