from __future__ import annotations
from dataclasses import dataclass
from .metadata import GraphMetaData
from .mixins import (
    AnnotationMixin,
    AxesMixin,
    ChainMixin,
    ExportMixin,
    LayoutMixin,
    LegendMixin,
    RecessionMixin,
    ReferenceLinesMixin
)

@dataclass
class GraphBase(
    GraphMetaData,
    AnnotationMixin,
    AxesMixin,
    ChainMixin,
    ExportMixin,
    LayoutMixin,
    LegendMixin,
    RecessionMixin,
    ReferenceLinesMixin

):
    """
    Base class that provides shared Matplotlib utilities for chart construction.

    This class centralizes the common functionality used by higher-level chart
    builders, including axis preparation, title and subtitle handling, source
    notes, legends, horizontal guides, value annotations, shaded regions,
    recession overlays, figure creation, and figure export.

    It is intended to be inherited by chart-specific classes so that line, bar,
    pie, boxplot, and other chart types can reuse a consistent plotting style
    and metadata management workflow.

    Notes
    -----
    This class assumes that figure and axis metadata are managed through
    `Graph_meta_data`, particularly via `_generate_metadata`.
    """


