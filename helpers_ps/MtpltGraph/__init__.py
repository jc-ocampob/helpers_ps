"""
Graphing utilities for helpers_ps.

This module exposes the public charting API used to create institutional
Matplotlib charts.
"""

from .config import set_graph_theme
from .renderer import render_from_dict
from .GraphMtplt import GraphMtplt
from .models import (
    XAxisConfig,
    YAxisConfig,
    SeriesSpec,
    FigureSource,
    TagStyle,
    DotStyle,
    FigureTitle,
)


__all__ = [
    "set_graph_theme",
    "GraphMtplt",
    "render_from_dict"
]