"""
Graphing utilities for helpers_ps.

This module exposes the public charting API used to create institutional
Matplotlib charts.
"""

from .config import set_graph_theme
from .renderer import render_from_dict
from .GraphMtplt import GraphMtplt
from . import models


__all__ = [
    # General theme setting
    "set_graph_theme",

    # Main Class
    "GraphMtplt",

    # Batch rendering from dict
    "render_from_dict",

    # Models helpers
    "models"
]