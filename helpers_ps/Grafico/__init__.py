"""
Graphing utilities for helpers_ps.

This module exposes the public charting API used to create institutional
Matplotlib charts.
"""

from .config import PALETA_COLORES, buffers, set_graph_theme
from .metadata import Graph_meta_data
from .base import Graph_base
from .tags_line import Line_tags
from .tags_bar import Bar_tags
from .tags_pie import Pie_tags
from .tags_box import BoxW_tags
from .charts import GraphMtplt

# Preferred public aliases
GraphMetadata = Graph_meta_data
GraphBase = Graph_base
LineTags = Line_tags
BarTags = Bar_tags
PieTags = Pie_tags
BoxWhiskerTags = BoxW_tags

__all__ = [
    "PALETA_COLORES",
    "buffers",
    "set_graph_theme",

    "Graph_meta_data",
    "Graph_base",
    "Line_tags",
    "Bar_tags",
    "Pie_tags",
    "BoxW_tags",
    "Graph_mtplt",

    "GraphMetadata",
    "GraphBase",
    "LineTags",
    "BarTags",
    "PieTags",
    "BoxWhiskerTags",
    "GraphMtplt",
]