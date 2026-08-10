from __future__ import annotations

import pandas as pd

from .base import GraphBase
from .tags import (
    LineTags,
    BoxWTags,
    BarTags,
    PieTags
)
from .charts import (
    LineChartMixin,
    BarChartMixin,
    PieChartMixin,
    BoxWChartMixin
)


class GraphMtplt(

    # Tag management
    GraphBase,
    LineTags,
    BarTags,
    PieTags,
    BoxWTags,

    # Chart graphing
    LineChartMixin,
    BarChartMixin,
    PieChartMixin,
    BoxWChartMixin
):
    """
    High-level Matplotlib chart builder for institutional reporting.

    This class combines the base plotting utilities with chart-specific mixins
    for line, bar, pie, and box-and-whisker charts. It is designed to provide a
    consistent API for creating presentation-ready graphs using one or multiple
    pandas DataFrames.

    The class manages internal figure, axis, dataframe, x-axis, bar, and legend
    metadata so that chart methods can share common formatting, annotation, and
    layout logic.

    Parameters
    ----------
    dataframe : pandas.DataFrame, list[pandas.DataFrame], or None, optional
        Dataset used by the chart methods. A single DataFrame is internally
        converted into a list to keep a consistent dataframe selection interface.

    Attributes
    ----------
    dataframe : list[pandas.DataFrame] or None
        DataFrame collection available for plotting.
    _fig : matplotlib.figure.Figure or None
        Current Matplotlib figure.
    _ax : matplotlib.axes.Axes or None
        Active Matplotlib axis.
    _axes : matplotlib.axes.Axes or array-like or None
        Axis collection when using subplots.
    _df : pandas.DataFrame or None
        Active DataFrame selected for the current chart.
    _ticker_label_color : list[tuple]
        Internal mapping of ticker, display label, and color used by legends
        and annotations.
    """

    def __init__(self, dataframe: pd.DataFrame | list[pd.DataFrame] | None = None):
        """
        Initialize the chart builder with one or multiple DataFrames.

        Parameters
        ----------
        dataframe : pandas.DataFrame, list[pandas.DataFrame], or None, optional
            DataFrame or list of DataFrames used as input data for the chart methods.
            If a single DataFrame is provided, it is converted into a one-element
            list to standardize dataframe selection by index.

        Notes
        -----
        This initializer also resets all internal plotting metadata, including the
        active figure, axes, selected dataframe, x-axis configuration, bar metadata,
        and custom legend handles.
        """
        self.dataframe = [dataframe] if isinstance(dataframe, pd.DataFrame) else dataframe


