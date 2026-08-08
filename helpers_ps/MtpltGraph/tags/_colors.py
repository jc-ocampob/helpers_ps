"""
Single source of truth for the institutional color palette.

Every other module in this package should import ``PALETA_COLORES`` from
here instead of repeating the ``try/except`` fallback against
``helpers_ps.GlobVars.var_globs``. This keeps the fallback palette in one
place so it can't drift between modules.
"""

from __future__ import annotations

try:
    from helpers_ps.GlobVars.var_globs import PALETA_COLORES
except Exception:
    PALETA_COLORES = [
        "#2F71E5", "#00A6A6", "#F28E2B", "#E15759", "#76B7B2",
        "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F"
    ]

__all__ = ["PALETA_COLORES"]
