from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class AxisState:
    """
    Store all metadata that belongs to one Matplotlib axis/subplot.

    This object is intentionally independent from the figure-level metadata.
    Every subplot gets its own AxisState instance.
    """

    # DataFrame selected for this axis
    dataframe_idx: int | None = None
    dataframe: pd.DataFrame | None = None

    # X-axis metadata
    x_axis_mode: str | None = None
    x_axis_fechas: Any = None
    x_axis_metadata: dict[str, Any] = field(default_factory=dict)
    x_vals: Any = None
    months: Any = None
    years: Any = None

    # Bar metadata
    bar_mode: str | None = None
    bar_stacked: bool | None = False
    bar_grouped: bool | None = None
    bar_rects: Any = None
    bars_data: dict[str, Any] = field(default_factory=dict)
    bars_x_reference: list[Any] = field(default_factory=list)

    # Pie metadata
    pie_data: dict[str, Any] = field(default_factory=dict)

    # Series metadata
    ticker_label_color: list[tuple[str, str, str]] = field(default_factory=list)
    series_config: list[dict[str, Any]] = field(default_factory=list)

    # Legend metadata
    custom_legend_handles: list[Any] = field(default_factory=list)

    # Secondary y-axis metadata
    right_ax: Any = None
    axis_map: dict[str, str] = field(default_factory=dict)
    right_axis_enabled: bool = False
    right_axis_config: dict[str, Any] = field(default_factory=dict)
    y_axis_right: dict[str, Any] = field(default_factory=dict)

    def reset_chart_runtime(self) -> None:
        """
        Reset chart-specific runtime metadata while preserving dataframe selection.

        Useful if later you want to reuse an axis but clear bars, pie data,
        legend handles, or right-axis references.
        """
        self.x_axis_mode = None
        self.x_axis_fechas = None
        self.x_axis_metadata = {}
        self.x_vals = None
        self.months = None
        self.years = None

        self.bar_mode = None
        self.bar_stacked = None
        self.bar_grouped = None
        self.bar_rects = None
        self.bars_data = {}
        self.bars_x_reference = []

        self.pie_data = {}

        self.ticker_label_color = []
        self.series_config = []

        self.custom_legend_handles = []

        self.right_ax = None
        self.axis_map = {}
        self.right_axis_enabled = False
        self.right_axis_config = {}
        self.y_axis_right = {}