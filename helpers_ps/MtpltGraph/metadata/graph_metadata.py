from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from ..models.layout import (
    FigureConfig,
    FigureSource,
    FigureSubtitle,
    FigureTitle,
)
from .axis_state import AxisState
from .series_config import get_series_meta, normalize_series_config
from .state_attrs import STATE_ATTRS


@dataclass
class GraphMetaData:
    """
    Store and manage figure, axis, dataframe, and per-subplot metadata.

    Figure-level state remains on this object.
    Axis-level state lives in AxisState objects.

    Backward compatibility:
    Existing code can continue using flat attributes like self._df,
    self._x_vals, self._bars_data, self._pie_data, and self._right_ax.
    Those attributes are redirected to the active AxisState.
    """

    dataframe: pd.DataFrame | list[pd.DataFrame] | None = None

    # Figure-level metadata
    _fig: Any = field(default=None, init=False, repr=False)
    _figConfig: FigureConfig | None = field(default=None, init=False, repr=False)

    # Figure layout metadata
    _title: FigureTitle | None = field(default=None, init=False, repr=False)
    _subtitle: FigureSubtitle | None = field(default=None, init=False, repr=False)
    _source: FigureSource | None = field(default=None, init=False, repr=False)

    # Axes management
    _axes: list[Any] | None = field(default=None, init=False, repr=False)
    _axes_shape: tuple[int, int] | None = field(default=None, init=False, repr=False)
    _ax_idx: int | None = field(default=None, init=False, repr=False)
    _ax: Any = field(default=None, init=False, repr=False)
    _states: list[AxisState] | None = field(default=None, init=False, repr=False)
    _state: AxisState | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """
        Normalize constructor inputs after dataclass initialization.
        """
        if isinstance(self.dataframe, pd.DataFrame):
            self.dataframe = [self.dataframe]

    # -----------------------------------------------------------------
    # Transparent delegation of flat attributes to self._state
    # -----------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        field_name = STATE_ATTRS.get(name)

        if field_name is None:
            raise AttributeError(name)

        state = self.__dict__.get("_state")

        if state is None:
            raise AttributeError(
                f"{name!r} is not available yet. "
                "Call plot() / _generate_metadata() first."
            )

        return getattr(state, field_name)

    def __setattr__(self, name: str, value: Any) -> None:
        field_name = STATE_ATTRS.get(name)

        if field_name is None:
            object.__setattr__(self, name, value)
            return

        state = self.__dict__.get("_state")

        if state is None:
            raise AttributeError(
                f"Cannot assign {name!r} yet because there is no active axis. "
                "Call plot() / _generate_metadata() first."
            )

        setattr(state, field_name, value)

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------
    def _ensure_dataframe_collection(self) -> list[pd.DataFrame]:
        """
        Return dataframe as a list of DataFrames.
        """
        if self.dataframe is None:
            raise ValueError("No dataframe was provided.")

        if isinstance(self.dataframe, pd.DataFrame):
            self.dataframe = [self.dataframe]

        if not isinstance(self.dataframe, list):
            raise TypeError(
                "`dataframe` must be a pandas DataFrame, a list of DataFrames, or None."
            )

        if not all(isinstance(item, pd.DataFrame) for item in self.dataframe):
            raise TypeError("Every item in `dataframe` must be a pandas DataFrame.")

        return self.dataframe

    def _ensure_active_state(self) -> AxisState:
        """
        Return the active AxisState, creating a pending one if needed.

        This is useful because graph_line/graph_bar usually select the DataFrame
        before plot() creates the Matplotlib axes.
        """
        if self._state is None:
            self._state = AxisState()

        return self._state

    # -----------------------------------------------------------------
    # Axis selection
    # -----------------------------------------------------------------
    def _set_axis(self, ax_index: int = 0) -> None:
        """
        Select the active Matplotlib axis and its matching AxisState.
        """
        if self._states is None or self._axes is None:
            raise RuntimeError("Axes not initialized. Call plot() first.")

        if ax_index < 0 or ax_index >= len(self._axes):
            raise IndexError("Axis index out of range.")

        if self._ax_idx == ax_index:
            return None

        if self._ax_idx is not None and self._ax is not None:
            self._axes[self._ax_idx] = self._ax

        self._ax_idx = ax_index
        self._ax = self._axes[ax_index]
        self._state = self._states[ax_index]

        return None

    # -----------------------------------------------------------------
    # DataFrame selection
    # -----------------------------------------------------------------
    def _select_df(self, df_idx: int = 0) -> pd.DataFrame:
        """
        Select and store the active dataframe from the dataframe collection.
        """
        dataframes = self._ensure_dataframe_collection()

        if df_idx < 0 or df_idx >= len(dataframes):
            raise IndexError("DataFrame index out of range.")

        state = self._ensure_active_state()
        state.dataframe_idx = df_idx
        state.dataframe = dataframes[df_idx]

        return state.dataframe

    # -----------------------------------------------------------------
    # Metadata generation after plot creation
    # -----------------------------------------------------------------
    def _generate_metadata(
        self,
        fig,
        axes,
        nrows: int,
        ncols: int,
    ) -> None:
        """
        Initialize figure, axes, and one AxisState per axis after plot creation.

        If _select_df() created a pending AxisState before plot() ran,
        that pending state is adopted as axis 0 state.
        """
        pending_state = None

        if self._states is None and self._state is not None:
            pending_state = self._state

        self._fig = fig

        if isinstance(axes, np.ndarray):
            self._axes = axes.flatten().tolist()
        else:
            self._axes = [axes]

        self._ax_idx = 0
        self._ax = self._axes[0]
        self._axes_shape = (nrows, ncols)

        self._states = [
            pending_state if i == 0 and pending_state is not None else AxisState()
            for i in range(len(self._axes))
        ]

        self._state = self._states[0]

        return None

    # -----------------------------------------------------------------
    # Series metadata wrappers
    # -----------------------------------------------------------------
    def _normalize_series_config(
        self,
        dataframe: pd.DataFrame,
        tickers: list[str] | tuple[str, ...] | set[str] | str = "all",
        labels: list[str] | tuple[str, ...] | str | dict[str, str] | None = None,
        colors: list[str] | tuple[str, ...] | str | dict[str, str] | None = None,
        axis_side: str | list[str] | tuple[str, ...] | dict[str, str] | None = None,
        default_axis_side: str = "left",
    ) -> list[dict[str, Any]]:
        """
        Normalize series config and keep the method available on self.
        """
        return normalize_series_config(
            dataframe=dataframe,
            tickers=tickers,
            labels=labels,
            colors=colors,
            axis_side=axis_side,
            default_axis_side=default_axis_side,
        )

    def _get_series_meta(self, ticker: str) -> dict[str, Any]:
        """
        Return normalized metadata for a plotted ticker from the active state.
        """
        return get_series_meta(
            series_config=self._series_config,
            ticker=ticker,
        )

    # -----------------------------------------------------------------
    # Optional reset helper
    # -----------------------------------------------------------------
    def _reset_figure_metadata(self) -> None:
        """
        Reset figure and axis metadata after save/close operations.
        """
        self._fig = None
        self._figConfig = None

        self._title = None
        self._subtitle = None
        self._source = None

        self._axes = None
        self._axes_shape = None
        self._ax_idx = None
        self._ax = None
        self._states = None
        self._state = None