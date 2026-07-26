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


# ============================================================
# API pública - paquetes alternos
# ============================================================

from helpers_ps import (
    FinCalculations,
    #BBGHelper,
    Powerpoint
)

# ============================================================
# API pública - Paquete principal
# ============================================================
from helpers_ps.MtpltGraph import (
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

    #Alternate packages
    "FinCalculations",
    "BBGHelper"
    "Powerpoint"
]