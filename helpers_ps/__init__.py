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
# API pública - Gráficos
# ============================================================

from helpers_ps.Grafico.graf import (
    Graph_mtplt,
)

from helpers_ps.Config.var_globs import (
    PALETA_COLORES
)

# ============================================================
# API pública - Cálculo / métricas
# ============================================================

from helpers_ps.Calculo.metricas import (
    Metrics,
    ytd,
    mtd,
    qtd,
    drawdown,
    downside_std,
    beta,
    upside_capture,
    downside_capture,
    capture_ratio,
    var,
    tracking_error,
    information_ratio,
    excess_return,
    consistency,
    rsi,
    sma,
    ema,
    ranges,
    relative,
    momentum,
    momentum_sma,
    rank_percentile,
)

Graph = Graph_mtplt

# ============================================================
# Control explícito de objetos públicos
# ============================================================

__all__ = [
    "__version__",

    # Gráficos
    "Graph",

    # Métricas
    "Metrics",
    "ytd",
    "mtd",
    "qtd",
    "drawdown",
    "downside_std",
    "beta",
    "upside_capture",
    "downside_capture",
    "capture_ratio",
    "var",
    "tracking_error",
    "information_ratio",
    "excess_return",
    "consistency",
    "rsi",
    "sma",
    "ema",
    "ranges",
    "relative",
    "momentum",
    "momentum_sma",
    "rank_percentile",
]