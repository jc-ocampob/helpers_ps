from __future__ import annotations

import io
import locale
import warnings
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Any, Callable, Self

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MultipleLocator

from ._colors import PALETA_COLORES

from .metadata import Graph_meta_data
from .config import buffers


@dataclass
class Graph_base(Graph_meta_data):
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
    # =========================
    # Chainable API helpers
    # =========================
    def pipe(
        self: Self,
        func: Callable[..., Self | None],
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        """
        Apply a custom function to the graph object and keep the chain alive.

        This method follows the same idea as pandas .pipe(), allowing reusable
        graph transformations to be inserted into the chart-building workflow.

        Parameters
        ----------
        func:
            Function that receives the current graph object as its first argument.
            The function can either return the graph object or return None.
        *args:
            Positional arguments passed to the function.
        **kwargs:
            Keyword arguments passed to the function.

        Returns
        -------
        Graph_base
            The current graph object, or the object returned by the function.
        """
        result = func(self, *args, **kwargs)
        return self if result is None else result

    def tap(
        self: Self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        """
        Execute a side-effect function and keep the chain alive.

        This is useful for debugging, logging, previewing, or applying matplotlib
        actions that do not need to return the graph object.

        Parameters
        ----------
        func:
            Function that receives the current graph object as its first argument.
        *args:
            Positional arguments passed to the function.
        **kwargs:
            Keyword arguments passed to the function.

        Returns
        -------
        Graph_base
            The current graph object.
        """
        func(self, *args, **kwargs)
        return self

    def axis(self: Self, ax_index: int = 0) -> Self:
        """
        Select the active subplot axis and keep the chain alive.

        This is a public chainable wrapper around _set_axis().

        Parameters
        ----------
        ax_index:
            Zero-based index of the subplot axis to activate.

        Returns
        -------
        Graph_base
            The current graph object.
        """
        self._set_axis(ax_index=ax_index)
        return self

    def get_axis(self, side: str = "left"):
        """
        Return the active left or right Matplotlib axis.

        Parameters
        ----------
        side:
            Axis side to retrieve. Must be either "left" or "right".

        Returns
        -------
        matplotlib.axes.Axes
            The requested Matplotlib axis.
        """
        if side not in {"left", "right"}:
            raise ValueError("side must be 'left' or 'right'.")

        if side == "left":
            return self._ax

        if self._right_ax is None:
            raise RuntimeError("No right axis exists for the active chart.")

        return self._right_ax

    # =========================
    # funciones de ayuda
    # =========================
    def _months_years(self, fechas):
        """
        Extract Spanish month abbreviations and years from a date-like index.

        This helper stores month labels and year values in the instance so they can
        be reused when creating Bloomberg-style x-axis labels.

        Parameters
        ----------
        fechas : sequence of datetime-like values
            Date-like sequence used to extract month abbreviations and years.

        Returns
        -------
        None
            The extracted values are stored internally in `_months` and `_years`.
        """
        mes_es = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        self._months = [mes_es[d.month] for d in fechas]
        self._years = np.array([d.year for d in fechas])

    def _years_xaxis(self, y_offset=-0.08, fontsize=None, color='black'):
        """
        Add year labels below the x-axis for Bloomberg-style date charts.

        This method uses the internally stored `_years` array to place one centered
        year label below each group of monthly x-axis labels.

        Parameters
        ----------
        y_offset : float, default -0.08
            Vertical offset of the year labels relative to the x-axis transform.
        fontsize : float or None, optional
            Font size of the year labels. If None, the method uses the internal
            tick font size when available.
        color : str, default "black"
            Text color of the year labels.

        Returns
        -------
        None
            Year labels are added directly to the active axis.
        """

        years = getattr(self, "_years", None)
        if years is None:
            return

        if fontsize is None:
                fontsize = getattr(self, "_tick_fontsize", 8)

        for yr in np.unique(years):
            idx = np.where(years == yr)[0]
            mid = idx.mean()
            self._ax.text(
                mid, y_offset, str(yr),
                transform=self._ax.get_xaxis_transform(),
                ha='center', va='top',
                fontsize=fontsize,
                color=color
            )

    def _coerce_to_bbg_x(self, x):
        """
        Convert an x-axis input value into the internal Bloomberg-style position.

        Bloomberg-style charts use integer positions instead of the original
        datetime values. This helper converts dates, timestamps, or numeric values
        into the corresponding numeric x-coordinate used by the active axis.

        Parameters
        ----------
        x : int, float, str, pandas.Timestamp, or datetime-like
            Input x-axis value to convert.

        Returns
        -------
        float
            Numeric x-axis position compatible with the Bloomberg-style axis.

        Notes
        -----
        If the internal Bloomberg date index is not available, the function attempts
        to return the input value as a float.
        """

        fechas = self._x_axis_fechas
        if fechas is None or len(fechas) == 0:
            return float(x)

        if isinstance(x, (int, float, np.integer, np.floating)):
            return float(x)

        try:
            dt = pd.to_datetime(x)
        except Exception:
            return float(x)

        arr = fechas.values
        pos = np.searchsorted(arr, np.datetime64(dt), side="left")
        pos = int(np.clip(pos, 0, len(fechas) - 1))
        return float(pos)

    def _normalize_series_config(
        self,
        dataframe: pd.DataFrame,
        tickers: list[str] | str = "all",
        labels: list[str] | str | dict[str, str] | None = None,
        colors: list[str] | str | dict[str, str] | None = None,
        axis_side: str | list[str] | dict[str, str] | None = None,
        default_axis_side: str = "left",
    ) -> list[dict]:
        """
        Normalize tickers, labels, colors, and axis-side configuration into a
        single list of series dictionaries.

        This helper keeps backward compatibility with the current public API while
        avoiding fragile parallel-list handling internally.

        Parameters
        ----------
        dataframe:
            DataFrame used to validate available columns.
        tickers:
            Selected columns to plot. Use "all" to select all columns.
        labels:
            Labels for each ticker. Can be None, str, list, tuple, or dict keyed by ticker.
        colors:
            Colors for each ticker. Can be None, str, list, tuple, or dict keyed by ticker.
        axis_side:
            Axis side for each ticker. Can be None, "left", "right", list, tuple, or dict.
        default_axis_side:
            Default axis side used when no side is provided for a ticker.

        Returns
        -------
        list[dict]
            List of dictionaries with ticker, label, color, and axis_side.
        """

        if dataframe is None or not isinstance(dataframe, pd.DataFrame):
            raise TypeError("`dataframe` must be a pandas DataFrame.")

        available_columns = dataframe.columns.tolist()

        # -------------------------------------------------
        # 1. Normalize tickers
        # -------------------------------------------------
        if isinstance(tickers, str):
            if tickers == "all":
                tickers = available_columns.copy()
            else:
                tickers = [tickers]
        elif isinstance(tickers, (tuple, set)):
            tickers = list(tickers)
        elif not isinstance(tickers, list):
            raise TypeError("`tickers` must be 'all', a string, or a list-like object.")

        tickers = [ticker for ticker in tickers if ticker in available_columns]

        if len(tickers) == 0:
            raise ValueError("No valid tickers were found in the dataframe.")

        # -------------------------------------------------
        # 2. Normalize labels
        # -------------------------------------------------
        if labels is None:
            labels_map = {ticker: ticker for ticker in tickers}

        elif isinstance(labels, str):
            labels_map = {
                ticker: ticker
                for ticker in tickers
            }
            labels_map[tickers[0]] = labels

        elif isinstance(labels, dict):
            labels_map = {
                ticker: labels.get(ticker, ticker)
                for ticker in tickers
            }

        elif isinstance(labels, (list, tuple)):
            labels = list(labels)
            labels_map = {
                ticker: labels[i] if i < len(labels) else ticker
                for i, ticker in enumerate(tickers)
            }

        else:
            raise TypeError(
                "`labels` must be None, a string, a list-like object, or a dictionary."
            )

        # -------------------------------------------------
        # 3. Normalize colors
        # -------------------------------------------------
        if colors is None:
            colors = PALETA_COLORES.copy()

        if isinstance(colors, str):
            colors_map = {ticker: colors for ticker in tickers}

        elif isinstance(colors, dict):
            colors_map = {
                ticker: colors.get(ticker, PALETA_COLORES[i % len(PALETA_COLORES)])
                for i, ticker in enumerate(tickers)
            }

        elif isinstance(colors, (list, tuple)):
            colors = list(colors)
            colors_map = {
                ticker: colors[i] if i < len(colors) else PALETA_COLORES[i % len(PALETA_COLORES)]
                for i, ticker in enumerate(tickers)
            }

        else:
            colors_map = {
                ticker: PALETA_COLORES[i % len(PALETA_COLORES)]
                for i, ticker in enumerate(tickers)
            }

        # -------------------------------------------------
        # 4. Normalize axis side
        # -------------------------------------------------
        if axis_side is None:
            axis_map = {
                ticker: default_axis_side
                for ticker in tickers
            }

        elif isinstance(axis_side, str):
            if axis_side not in {"left", "right"}:
                raise ValueError("`axis_side` must be either 'left' or 'right'.")

            axis_map = {
                ticker: axis_side
                for ticker in tickers
            }

        elif isinstance(axis_side, dict):
            axis_map = {
                ticker: axis_side.get(ticker, default_axis_side)
                for ticker in tickers
            }

        elif isinstance(axis_side, (list, tuple)):
            axis_side = list(axis_side)
            axis_map = {
                ticker: axis_side[i] if i < len(axis_side) else default_axis_side
                for i, ticker in enumerate(tickers)
            }

        else:
            raise TypeError(
                "`axis_side` must be None, a string, a list-like object, or a dictionary."
            )

        invalid_sides = {
            side for side in axis_map.values()
            if side not in {"left", "right"}
        }

        if invalid_sides:
            raise ValueError("`axis_side` values must be only 'left' or 'right'.")

        # -------------------------------------------------
        # 5. Build normalized config
        # -------------------------------------------------
        return [
            {
                "ticker": ticker,
                "label": labels_map[ticker],
                "color": colors_map[ticker],
                "axis_side": axis_map[ticker],
            }
            for ticker in tickers
        ]

    def _get_series_meta(self, ticker: str) -> dict:
        """
        Return normalized metadata for a plotted ticker.

        Parameters
        ----------
        ticker:
            Ticker/column name to search in the current series configuration.

        Returns
        -------
        dict
            Metadata dictionary with ticker, label, color, and axis_side.
        """

        for item in getattr(self, "_series_config", []):
            if item.get("ticker") == ticker:
                return item

        raise KeyError(f"No series metadata found for ticker: {ticker}")

    # =========================
    # Metodos de los ejes
    # =========================
    def prep_x_axis(
        self,
        dataframe: pd.DataFrame = None,
        bbg_format: bool = False,
        tick_step: int = 6,
        fmt: str = None,
        year_y_offset: float = -0.08,
        lim: tuple[float, float] = None,
        fontsize: float = 8,
        return_dataframe: bool = True,
        tick_values: list | tuple | pd.Index | np.ndarray | None = None,
        tick_labels: list[str] | tuple[str, ...] | None = None,
        tick_label_map: dict | None = None,
        rotation: float = 0,
        ha: str = "center",
        label_color: str | None = None,
        show_years: bool = True,
    ) -> pd.DataFrame:
        """
        Prepare the x-axis format, ticks, labels, limits, and internal metadata.

        This method detects whether the DataFrame index is datetime-like, numeric,
        or categorical, and applies the appropriate x-axis formatting. It supports
        automatic tick selection through `tick_step`, explicit tick selection through
        `tick_values`, and custom label replacement through `tick_labels` or
        `tick_label_map`.

        Parameters
        ----------
        dataframe : pandas.DataFrame or None, optional
            DataFrame used to configure the x-axis. If None, the active internal
            DataFrame `_df` is used.
        bbg_format : bool, default False
            Whether to use the Bloomberg-style x-axis format for datetime indexes.
        tick_step : int, default 6
            Step used to determine the frequency of visible x-axis tick labels when
            `tick_values` is not provided.
        fmt : str or None, optional
            Format string used for datetime or numeric tick labels.
        year_y_offset : float, default -0.08
            Vertical offset used for year labels when `bbg_format=True`.
        lim : tuple[float, float] or None, optional
            Optional lower and upper x-axis filter applied to the DataFrame index.
        fontsize : float, default 8
            Font size used for x-axis tick labels.
        return_dataframe : bool, default True
            Kept for API compatibility. The method returns the transformed or
            filtered DataFrame.
        tick_values : list, tuple, pandas.Index, numpy.ndarray, or None, optional
            Explicit x-axis values to display as ticks. Values should match the
            DataFrame index for datetime, numeric, or categorical axes. In
            Bloomberg-style mode, datetime values are mapped to internal positions.
        tick_labels : list[str], tuple[str, ...], or None, optional
            Explicit labels to use for `tick_values`. Must have the same length as
            the resolved tick positions.
        tick_label_map : dict or None, optional
            Mapping used to rename selected tick labels. Keys are matched against
            original index values and stringified labels.
        rotation : float, default 0
            Rotation applied to x-axis tick labels.
        ha : str, default "center"
            Horizontal alignment of x-axis tick labels.
        label_color : str or None, optional
            Optional color applied to x-axis tick labels.
        show_years : bool, default True
            Whether to draw year labels in Bloomberg-style mode.

        Returns
        -------
        pandas.DataFrame
            DataFrame after applying the optional x-axis limits.

        Notes
        -----
        The method updates internal x-axis metadata such as `_x_axis_mode`,
        `_x_axis_fechas`, `_x_vals`, `_months`, `_years`, and `_x_axis_metadata`.
        """

        # -------------------------------------------------
        # 1. Basic validation
        # -------------------------------------------------
        if dataframe is None:
            dataframe = self._df

        if dataframe is None:
            raise ValueError("No dataframe was provided and `self._df` is None.")

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("`dataframe` must be a pandas DataFrame.")

        if dataframe.empty:
            raise ValueError("Cannot prepare x-axis because the dataframe is empty.")

        if tick_step is None:
            tick_step = 1

        if not isinstance(tick_step, int):
            raise TypeError("`tick_step` must be an integer.")

        if tick_step <= 0:
            raise ValueError("`tick_step` must be greater than zero.")

        dataframe = dataframe.copy()

        # -------------------------------------------------
        # 2. Apply limits before detecting index type
        # -------------------------------------------------
        if lim is not None:
            if not isinstance(lim, tuple) or len(lim) != 2:
                raise ValueError("`lim` must be a tuple with two values: (start, end).")

            start_value_x, end_value_x = lim

            if start_value_x is not None:
                dataframe = dataframe.loc[dataframe.index >= start_value_x].copy()

            if end_value_x is not None:
                dataframe = dataframe.loc[dataframe.index <= end_value_x].copy()

            if dataframe.empty:
                raise ValueError("The dataframe is empty after applying `lim`.")

        x_index = dataframe.index

        is_datetime = pd.api.types.is_datetime64_any_dtype(x_index)
        is_numeric = pd.api.types.is_numeric_dtype(x_index)

        fechas = None
        x_vals = None

        tick_label_map = {} if tick_label_map is None else tick_label_map

        # -------------------------------------------------
        # 3. Helpers
        # -------------------------------------------------
        def _as_list(value):
            if value is None:
                return None
            if isinstance(value, pd.Index):
                return value.tolist()
            if isinstance(value, np.ndarray):
                return value.tolist()
            if isinstance(value, (list, tuple)):
                return list(value)
            return [value]

        def _format_tick_label(value, axis_mode: str):
            if axis_mode in {"datetime", "bbg"}:
                try:
                    dt = pd.to_datetime(value)
                    date_format = fmt if fmt is not None else "%b-%y"
                    label = dt.strftime(date_format)
                except Exception:
                    label = str(value)

            elif axis_mode == "numeric":
                num_format = fmt if fmt is not None else ",.0f"
                try:
                    label = f"{value:{num_format}}"
                except Exception:
                    label = str(value)

            else:
                label = str(value)

            if value in tick_label_map:
                return tick_label_map[value]

            if str(value) in tick_label_map:
                return tick_label_map[str(value)]

            if label in tick_label_map:
                return tick_label_map[label]

            return label

        def _validate_tick_labels(resolved_positions, resolved_labels):
            if resolved_labels is None:
                return

            if len(resolved_positions) != len(resolved_labels):
                raise ValueError(
                    "`tick_labels` must have the same length as the resolved tick positions."
                )

        def _style_x_ticks():
            tick_params = {
                "axis": "x",
                "labelsize": fontsize,
            }

            if label_color is not None:
                tick_params["colors"] = label_color

            self._ax.tick_params(**tick_params)

            for label in self._ax.get_xticklabels():
                label.set_rotation(rotation)
                label.set_ha(ha)

                if label_color is not None:
                    label.set_color(label_color)

        # -------------------------------------------------
        # 4. Bloomberg-style datetime axis
        # -------------------------------------------------
        if bbg_format and is_datetime:
            fechas = pd.Index(pd.Series(x_index).dropna().sort_values().unique())

            if len(fechas) == 0:
                raise ValueError("Datetime index only contains NaT values.")

            date_to_position = {
                pd.Timestamp(date): position
                for position, date in enumerate(fechas)
            }

            x_vals = pd.Index(x_index).map(
                lambda value: date_to_position.get(pd.Timestamp(value), np.nan)
            ).to_numpy(dtype=float)

            if np.isnan(x_vals).any():
                raise ValueError(
                    "Some x-axis dates could not be mapped to Bloomberg-style positions."
                )

            self._months_years(fechas)

            if tick_values is not None:
                raw_tick_values = _as_list(tick_values)

                tick_positions = []
                tick_source_values = []

                for value in raw_tick_values:
                    try:
                        dt_value = pd.Timestamp(value)
                    except Exception:
                        dt_value = value

                    if dt_value in date_to_position:
                        tick_positions.append(date_to_position[dt_value])
                        tick_source_values.append(dt_value)
                    elif isinstance(value, (int, float, np.integer, np.floating)):
                        position = int(value)
                        if 0 <= position < len(fechas):
                            tick_positions.append(position)
                            tick_source_values.append(fechas[position])
                    else:
                        raise ValueError(
                            f"`tick_values` contains a value not found in the x-axis: {value}"
                        )

                tick_positions = np.asarray(tick_positions, dtype=float)

            else:
                periods = pd.Series(fechas).dt.to_period("M")
                month_change = periods.ne(periods.shift())
                month_idx = np.where(month_change.to_numpy())[0]

                tick_positions = month_idx[::tick_step]
                tick_source_values = [fechas[i] for i in tick_positions]

            if tick_labels is not None:
                final_labels = list(tick_labels)
            else:
                final_labels = [
                    _format_tick_label(value, "bbg")
                    for value in tick_source_values
                ]

                # Preserve your Bloomberg-style month abbreviation default
                if fmt is None and tick_values is None:
                    final_labels = [self._months[int(i)] for i in tick_positions]

            _validate_tick_labels(tick_positions, final_labels)

            self._ax.set_xticks(tick_positions)
            self._ax.set_xticklabels(final_labels, fontsize=fontsize)

            if show_years:
                self._years_xaxis(
                    y_offset=year_y_offset,
                    fontsize=fontsize,
                )

            _style_x_ticks()

            self._x_axis_mode = "bbg"
            self._x_axis_fechas = fechas

        # -------------------------------------------------
        # 5. Regular datetime axis
        # -------------------------------------------------
        elif is_datetime:
            x_vals = x_index.to_numpy()
            self._x_axis_mode = "datetime"

            if tick_values is not None:
                raw_tick_values = _as_list(tick_values)
                tick_positions = [pd.to_datetime(value) for value in raw_tick_values]

                if tick_labels is not None:
                    final_labels = list(tick_labels)
                else:
                    final_labels = [
                        _format_tick_label(value, "datetime")
                        for value in tick_positions
                    ]

                _validate_tick_labels(tick_positions, final_labels)

                self._ax.set_xticks(tick_positions)
                self._ax.set_xticklabels(final_labels, fontsize=fontsize)

            else:
                x_axis_format = fmt if fmt is not None else "%b-%y"
                locator = mdates.MonthLocator(interval=tick_step)
                formatter = mdates.DateFormatter(x_axis_format)

                self._ax.xaxis.set_major_locator(locator)
                self._ax.xaxis.set_major_formatter(formatter)

            _style_x_ticks()

        # -------------------------------------------------
        # 6. Numeric axis
        # -------------------------------------------------
        elif is_numeric:
            x_vals = x_index.to_numpy()
            self._x_axis_mode = "numeric"

            if tick_values is not None:
                tick_positions = np.asarray(_as_list(tick_values))

                if tick_labels is not None:
                    final_labels = list(tick_labels)
                else:
                    final_labels = [
                        _format_tick_label(value, "numeric")
                        for value in tick_positions
                    ]

            else:
                tick_idx = np.arange(0, len(x_vals), tick_step)
                tick_positions = x_vals[tick_idx]

                if tick_labels is not None:
                    final_labels = list(tick_labels)
                else:
                    final_labels = [
                        _format_tick_label(value, "numeric")
                        for value in tick_positions
                    ]

            _validate_tick_labels(tick_positions, final_labels)

            self._ax.set_xticks(tick_positions)
            self._ax.set_xticklabels(final_labels, fontsize=fontsize)
            _style_x_ticks()

        # -------------------------------------------------
        # 7. Categorical axis
        # -------------------------------------------------
        else:
            categories = x_index.astype(str).to_numpy()
            x_vals = np.arange(len(categories), dtype=float)

            category_to_position = {
                category: position
                for position, category in enumerate(categories)
            }

            self._x_axis_mode = "categorical"
            self._x_axis_fechas = None

            if tick_values is not None:
                raw_tick_values = _as_list(tick_values)

                tick_positions = []
                tick_source_values = []

                for value in raw_tick_values:
                    if isinstance(value, (int, np.integer)):
                        position = int(value)
                        if 0 <= position < len(categories):
                            tick_positions.append(position)
                            tick_source_values.append(categories[position])
                        else:
                            raise ValueError(
                                f"`tick_values` contains an out-of-range position: {value}"
                            )

                    elif str(value) in category_to_position:
                        tick_positions.append(category_to_position[str(value)])
                        tick_source_values.append(str(value))

                    else:
                        raise ValueError(
                            f"`tick_values` contains a category not found in the x-axis: {value}"
                        )

                tick_positions = np.asarray(tick_positions, dtype=float)

            else:
                tick_positions = np.arange(0, len(categories), tick_step, dtype=float)
                tick_source_values = [categories[int(i)] for i in tick_positions]

            if tick_labels is not None:
                final_labels = list(tick_labels)
            else:
                final_labels = [
                    _format_tick_label(value, "categorical")
                    for value in tick_source_values
                ]

            _validate_tick_labels(tick_positions, final_labels)

            self._ax.set_xticks(tick_positions)
            self._ax.set_xticklabels(final_labels, fontsize=fontsize)
            _style_x_ticks()

        # -------------------------------------------------
        # 8. Store metadata
        # -------------------------------------------------
        self._x_vals = x_vals

        self._x_axis_metadata = {
            "mode": self._x_axis_mode,
            "fechas": self._x_axis_fechas,
            "x_vals": self._x_vals,
            "tick_step": tick_step,
            "tick_values": tick_values,
            "tick_labels": tick_labels,
            "tick_label_map": tick_label_map,
            "fmt": fmt,
            "fontsize": fontsize,
            "rotation": rotation,
            "ha": ha,
            "label_color": label_color,
            "bbg_format": bbg_format,
            "lim": lim,
        }

        # -------------------------------------------------
        # 9. Layout adjustment
        # -------------------------------------------------
        if self._x_axis_mode == "bbg":
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.21,
            )
        else:
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.18,
            )

        return dataframe

    def prep_y_axis(
        self,
        lim: tuple[float, float] | None = None,
        fmt: str | None = None,
        fontsize: float = 7,
        tick_step: int | None = None,
        label: str | None = None,
        label_fontsize: float | None = None,
        label_color: str | None = None,
        tick_color: str | None = None,
        spine_color: str | None = None,
        margins_x: float | None = 0.01,
        side: str | None = None,
        ax=None,
    ):
        """
        Prepare and format a y-axis.

        This method formats a target y-axis with limits, tick label formatting,
        tick styling, axis label styling, spine color, and optional tick spacing.

        It can be used for the active axis, the left axis, the right axis, or an
        explicitly provided Matplotlib axis. Grid lines are intentionally handled
        by horizontal_guides() to keep responsibilities separated.

        Parameters
        ----------
        lim:
            Lower and upper y-axis limits.
        fmt:
            Numeric format string used for y-axis labels. If None, ',.0f' is used.
        fontsize:
            Font size used for y-axis tick labels.
        tick_step:
            Fixed interval between y-axis ticks.
        label:
            Optional y-axis label.
        label_fontsize:
            Font size used for the y-axis label. If None, uses fontsize.
        label_color:
            Color used for the y-axis label.
        tick_color:
            Color used for y-axis tick labels and tick marks.
        spine_color:
            Color used for the y-axis spine.
        margins_x:
            X-axis margin passed to the target axis. If None, margins are not changed.
        side:
            Optional side reference. Use 'left' or 'right'. If None, the method
            formats the active axis unless ax is provided.
        ax:
            Explicit Matplotlib axis to format. This takes priority over side.

        Returns
        -------
        Graph_base
            Current graph object.
        """
        # -------------------------------------------------
        # 1. Resolve target axis
        # -------------------------------------------------
        if ax is not None:
            target_ax = ax

        elif side == "right":
            if getattr(self, "_right_ax", None) is None:
                raise RuntimeError("No right axis exists for the active chart.")
            target_ax = self._right_ax

        elif side == "left":
            target_ax = self._ax

        else:
            target_ax = self._ax

        if target_ax is None:
            raise RuntimeError(
                "No axis available. Create a chart before formatting the y-axis."
            )

        # -------------------------------------------------
        # 2. Resolve side
        # -------------------------------------------------
        if side is None:
            if getattr(self, "_right_ax", None) is target_ax:
                resolved_side = "right"
            else:
                resolved_side = "left"
        else:
            resolved_side = side

        if resolved_side not in {"left", "right"}:
            raise ValueError("side must be either 'left', 'right', or None.")

        spine_name = "right" if resolved_side == "right" else "left"

        # -------------------------------------------------
        # 3. Limits and margins
        # -------------------------------------------------
        if lim is not None:
            target_ax.set_ylim(*lim)

        if margins_x is not None:
            target_ax.margins(x=margins_x)

        # -------------------------------------------------
        # 4. Tick formatter
        # -------------------------------------------------
        fmt = fmt if fmt is not None else ",.0f"

        target_ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: f"{x:{fmt}}")
        )

        # -------------------------------------------------
        # 5. Tick params
        # Important:
        # Do not pass colors=None to Matplotlib.
        # -------------------------------------------------
        tick_params = {
            "axis": "y",
            "labelsize": fontsize,
        }

        final_tick_color = tick_color if tick_color is not None else label_color

        if final_tick_color is not None:
            tick_params["colors"] = final_tick_color

        target_ax.tick_params(**tick_params)

        # -------------------------------------------------
        # 6. Tick locator
        # -------------------------------------------------
        if tick_step is not None:
            target_ax.yaxis.set_major_locator(MultipleLocator(tick_step))

        # -------------------------------------------------
        # 7. Axis label
        # Important:
        # Do not force color=None.
        # -------------------------------------------------
        if label is not None:
            label_kwargs = {
                "fontsize": label_fontsize if label_fontsize is not None else fontsize,
            }

            final_label_color = label_color if label_color is not None else final_tick_color

            if final_label_color is not None:
                label_kwargs["color"] = final_label_color

            target_ax.set_ylabel(label, **label_kwargs)

        # -------------------------------------------------
        # 8. Spine color
        # Important:
        # Do not force color=None.
        # -------------------------------------------------
        final_spine_color = spine_color if spine_color is not None else final_tick_color

        if final_spine_color is not None:
            target_ax.spines[spine_name].set_color(final_spine_color)

        return self

    # =========================
    # Metodos de titulos subtitulos y fuente
    # =========================
    def add_titles(
        self,
        title: str | None = None,
        title_font_size: int = 12,
        subtitle: str | None = None,
        subtitle_font_size: int = 9
    ) -> Self:
        """
        Add a main title and subtitle to the active figure.

        This method places figure-level text elements instead of using the default
        axis title, allowing for a consistent institutional layout across different
        chart types.

        Parameters
        ----------
        title : str or None, optional
            Main chart title.
        title_font_size : int, default 12
            Font size of the main title.
        subtitle : str or None, optional
            Subtitle displayed below the main title.
        subtitle_font_size : int, default 9
            Font size of the subtitle.

        Returns
        -------
        None
            Title and subtitle are added directly to the active figure.
        """
        
        # eliminar title del axis
        self._ax.set_title("")

        # título principal (arriba del todo)
        if title:
            self._fig.text(
                0.02, 0.93,
                title,
                ha="left",
                va="top",
                fontsize=title_font_size,
                fontweight="bold"
            )

        # subtítulo
        if subtitle:
            self._fig.text(
                0.02, 0.88,
                subtitle,
                ha="left",
                va="top",
                fontsize=subtitle_font_size,
                color="#333333"
            )

        return self

    def add_source(
        self,
        text: str | list | None = None,
        x: float = 0.02,
        y: float = 0.022,
        fontsize: float = 6,
        color: str = "#606060",
        line_spacing: float = 0.022,
    ) -> Self:
        """
        Add a source note or footer text to the active figure.

        The source can be provided as a single string or as a list of lines. The
        method supports up to four lines and places them in the lower section of the
        figure.

        Parameters
        ----------
        text : str, list, or None, optional
            Source text to display. If None, no source note is added.
        x : float, default 0.02
            Horizontal figure coordinate for the source text.
        y : float, default 0.022
            Vertical figure coordinate for the first source line.
        fontsize : float, default 6
            Font size of the source note.
        color : str, default "#606060"
            Text color of the source note.
        line_spacing : float, default 0.022
            Vertical spacing between source lines.

        Returns
        -------
        None
            Source text is added directly to the active figure.

        Raises
        ------
        ValueError
            If more than four source lines are provided.
        """
        if text is None:
            return self
        
        if isinstance(text, str):
            lines = [text]
        else:
            lines = list(text)

        if len(lines) > 4:
            raise ValueError("Too many lines for source. Max 4.")
        elif len(lines) < 4:
            lines += [""] * (4 - len(lines))

        for i, line in enumerate(lines[::-1]):
            self._fig.text(
                x,
                y + i * line_spacing,
                line,
                ha="left",
                va="bottom",
                fontsize=fontsize,
                color=color
            )

        return self

    def add_legend(
            self,
            show: bool = False,
            loc: str = "upper left",
            bbox_to_anchor: tuple = None,
            ncol: int = 1,
            fontsize: int = 7,
            frameon: bool = True,
            edgecolor: str = "white",
            facecolor: str = "white",
            framealpha: float = 0.6
    ) -> Self:
        """
        Add and style a legend for the active axis.

        This method combines legend handles generated by Matplotlib with optional
        custom legend handles registered through helper methods. Duplicate labels
        are removed while preserving their original order.

        Parameters
        ----------
        show : bool, default False
            Whether to display the legend.
        loc : str, default "upper left"
            Legend location.
        bbox_to_anchor : tuple or None, optional
            Optional bounding box anchor used to position the legend.
        ncol : int, default 3
            Number of legend columns.
        fontsize : int, default 7
            Legend font size.
        frameon : bool, default True
            Whether to display the legend frame.
        edgecolor : str, default "white"
            Legend frame edge color.
        facecolor : str, default "white"
            Legend frame background color.
        framealpha : float, default 0.6
            Legend frame transparency.

        Returns
        -------
        None
            The legend is added directly to the active axis when available.
        """

        if not show:
            return self

        handles, labels = self._ax.get_legend_handles_labels()

        custom_handles = getattr(self, "_custom_legend_handles", None)

        if custom_handles:
            handles = handles + custom_handles
            labels = labels + [h.get_label() for h in custom_handles]

        # -------------------------------------------------
        # Evitar duplicados preservando orden
        # -------------------------------------------------
        final_handles = []
        final_labels = []
        seen = set()

        for h, lab in zip(handles, labels):
            if lab is None or lab == "" or lab.startswith("_"):
                continue

            if lab in seen:
                continue

            final_handles.append(h)
            final_labels.append(lab)
            seen.add(lab)

        if len(final_handles) == 0:
            return self

        self._ax.legend(
            final_handles,
            final_labels,
            loc=loc,
            bbox_to_anchor=bbox_to_anchor,
            ncol=ncol,
            fontsize=fontsize,
            frameon=frameon,
            edgecolor=edgecolor,
            facecolor=facecolor,
            framealpha=framealpha
        )

        return self

    def add_legend_point(
        self,
        label: str,
        color: str,
        marker: str = "o",
        markersize: float = 6,
    ) -> Self:
        
        """
        Register a custom point-style legend item for the active axis.

        Notes
        -----
        This docstring was added during the modular refactor to make the API easier
        to understand for new users and maintainers.
        """
        if not hasattr(self, "_custom_legend_handles"):
            self._custom_legend_handles = []

        existing_labels = {
            h.get_label()
            for h in self._custom_legend_handles
        }

        if label in existing_labels:
            return self

        self._custom_legend_handles.append(
            Line2D(
                [0],
                [0],
                marker=marker,
                linestyle="None",
                color="none",
                markerfacecolor=color,
                markeredgecolor=color,
                markersize=markersize,
                label=label,
            )
        )

        return self

    # =========================
    # Metodos de la figura general
    # =========================
    def show(self: Self) -> Self:
        """
        Display the active Matplotlib figure and keep the chain alive.

        Returns
        -------
        Graph_base
            The current graph object.
        """
        if self._fig:
            self._fig.show()

        return self

    def save(
        self,
        dir: dict = buffers,
        name: str = "graph_1",
        dpi: int = 400,
        reset_buffers: bool = True
    ) -> Self:
        """
        Save the active figure into an in-memory PNG buffer.

        This method exports the current figure as a PNG image into a `BytesIO`
        buffer and stores it in the provided dictionary-like object using `name`
        as the key. It is useful when charts need to be passed to PowerPoint,
        reports, dashboards, or other downstream workflows without writing files
        to disk.

        Parameters
        ----------
        dir : dict, default buffers
            Dictionary-like object where the image buffer will be stored.
        name : str, default "graph_1"
            Key assigned to the saved image buffer.
        dpi : int, default 400
            Resolution used when exporting the figure.
        reset_buffers : bool, default True
            Whether to reset internal figure, axis, layout, and metadata references
            after saving.

        Returns
        -------
        None
            The image buffer is stored in `dir[name]`.

        Notes
        -----
        The Matplotlib figure is closed after being saved.
        """
        buf = io.BytesIO()
        self._fig.savefig(buf, format="png", dpi=dpi)   # use figure-level save
        buf.seek(0)
        dir[name] = buf
        plt.close(self._fig)

        if reset_buffers:
            self._fig = None
            self._axes = None
            self._axes_shape = None
            self._ax_idx = None
            self._ax = None
            self._states = None
            self._state = None

        return self

    def plot(
        self,
        figsize: tuple[float, float] = (6.00, 4.80),
        color: str = "#D5D5D5",
        researchtype: bool = True,
        lw: float = 0.8,
        nrows: int = 1,
        ncols: int = 1,
        sharex: bool = False,
        sharey: bool = False,
        dpi: int | None = None,
        height_ratios: list[float] | None = None,
        width_ratios: list[float] | None = None,
        hspace: float | None = None,
        wspace: float | None = None
    ) -> Self:
        """
        Create the base Matplotlib figure and axes layout.

        This method initializes the figure and axes used by all chart methods. It
        supports standard subplot creation as well as custom GridSpec layouts when
        height ratios, width ratios, spacing, or DPI are provided.

        Parameters
        ----------
        figsize : tuple[float, float], default (6.00, 4.80)
            Figure size in inches.
        color : str, default "#D5D5D5"
            Color of the decorative horizontal divider lines.
        researchtype : bool default True
            Adds decorative figure dividers.
        lw : float, default 0.8
            Line width of the decorative figure dividers.
        nrows : int, default 1
            Number of subplot rows.
        ncols : int, default 1
            Number of subplot columns.
        sharex : bool, default False
            Whether subplots should share the x-axis.
        sharey : bool, default False
            Whether subplots should share the y-axis.
        dpi : int or None, optional
            Figure DPI. If provided, a custom GridSpec layout is used.
        height_ratios : list[float] or None, optional
            Relative height ratios for GridSpec rows.
        width_ratios : list[float] or None, optional
            Relative width ratios for GridSpec columns.
        hspace : float or None, optional
            Vertical spacing between GridSpec rows.
        wspace : float or None, optional
            Horizontal spacing between GridSpec columns.

        Returns
        -------
        None
            The figure and axes are created and stored internally.

        Notes
        -----
        The method also adds institutional-style decorative horizontal lines to the
        figure and applies default subplot spacing when no custom GridSpec settings
        are used.
        """
        # -------------------------------------------------
        # 1. Crear figura + axes
        # -------------------------------------------------
        use_gridspec = any([
            height_ratios is not None,
            width_ratios is not None,
            hspace is not None,
            wspace is not None,
            dpi is not None
        ])

        if not use_gridspec:
            fig, axes = plt.subplots(
                nrows=nrows,
                ncols=ncols,
                figsize=figsize,
                sharex=sharex,
                sharey=sharey
            )
        else:
            fig = plt.figure(figsize=figsize, dpi=dpi)

            gs_kwargs = {
                "nrows": nrows,
                "ncols": ncols
            }

            if height_ratios is not None:
                gs_kwargs["height_ratios"] = height_ratios

            if width_ratios is not None:
                gs_kwargs["width_ratios"] = width_ratios

            if hspace is not None:
                gs_kwargs["hspace"] = hspace

            if wspace is not None:
                gs_kwargs["wspace"] = wspace

            gs = fig.add_gridspec(**gs_kwargs)

            axes = []
            first_ax = None

            for r in range(nrows):
                row_axes = []
                for c in range(ncols):
                    subplot_kwargs = {}

                    if first_ax is not None:
                        if sharex:
                            subplot_kwargs["sharex"] = first_ax
                        if sharey:
                            subplot_kwargs["sharey"] = first_ax

                    ax = fig.add_subplot(gs[r, c], **subplot_kwargs)

                    if first_ax is None:
                        first_ax = ax

                    row_axes.append(ax)

                axes.append(row_axes)

            if nrows == 1 and ncols == 1:
                axes = axes[0][0]
            else:
                axes = np.array(axes, dtype=object)

        # -------------------------------------------------
        # 2. Guardar figura
        # -------------------------------------------------
        self._generate_metadata(
            fig,
            axes,
            nrows,
            ncols
        )

        # -------------------------------------------------
        # 5. Líneas decorativas de figura
        # -------------------------------------------------
        if researchtype:
            self._fig.add_artist(
                Line2D(
                    [0.01, 0.98], [0.95, 0.95],
                    transform=self._fig.transFigure,
                    color=color, lw=lw
                )
            )

            self._fig.add_artist(
                Line2D(
                    [0.01, 0.98], [0.12, 0.12],
                    transform=self._fig.transFigure,
                    color=color, lw=lw
                )
            )

        # -------------------------------------------------
        # 6. Ajustes globales
        # -------------------------------------------------
        # Si no usas gridspec custom, mantén el comportamiento original
        if not use_gridspec:
            self._fig.subplots_adjust(
                left=0.15,
                right=0.93,
                top=0.80,
                bottom=0.30
            )

        return self

    # =========================
    # Metodos de as etiquetas, guias y sombras
    # =========================
    def horizontal_guides(
        self,
        mostrar_cero: bool = True,
        side: str = "left",
        ax=None,
        linestyle: str = "--",
        linewidth: float = 0.5,
        color: str = "gray",
        alpha: float = 0.35,
        zero_color: str | None = None,
        zero_linestyle: str | None = None,
        zero_linewidth: float = 0.8,
        zero_alpha: float | None = None,
        zorder: int = 0,
    ):
        """
        Add horizontal guide lines to one or both y-axes.

        Parameters
        ----------
        mostrar_cero:
            Whether to add a highlighted horizontal line at y=0.
        side:
            Axis side where guides should be applied. Use 'left', 'right', or 'both'.
        ax:
            Explicit Matplotlib axis to apply guides to. If provided, side is ignored
            for axis selection.
        linestyle:
            Grid line style.
        linewidth:
            Grid line width.
        color:
            Grid line color.
        alpha:
            Grid line transparency.
        zero_color:
            Color of the zero line. If None, uses color.
        zero_linestyle:
            Style of the zero line. If None, uses linestyle.
        zero_linewidth:
            Width of the zero line.
        zero_alpha:
            Transparency of the zero line. If None, uses alpha.
        zorder:
            Drawing order of the guide lines.

        Returns
        -------
        Graph_base
            Current graph object.
        """
        if ax is not None:
            axes = [ax]

        elif side == "left":
            axes = [self._ax]

        elif side == "right":
            if getattr(self, "_right_ax", None) is None:
                raise RuntimeError("No right axis exists for the active chart.")
            axes = [self._right_ax]

        elif side == "both":
            axes = [self._ax]

            if getattr(self, "_right_ax", None) is not None:
                axes.append(self._right_ax)

        else:
            raise ValueError("side must be 'left', 'right', or 'both'.")

        for target_ax in axes:
            if target_ax is None:
                continue

            target_ax.yaxis.grid(
                True,
                linestyle=linestyle,
                linewidth=linewidth,
                color=color,
                alpha=alpha,
                zorder=zorder,
            )

            target_ax.set_axisbelow(True)

            if mostrar_cero:
                target_ax.axhline(
                    0,
                    color=zero_color if zero_color is not None else color,
                    linestyle=zero_linestyle if zero_linestyle is not None else linestyle,
                    linewidth=zero_linewidth,
                    alpha=zero_alpha if zero_alpha is not None else alpha,
                    zorder=zorder,
                )

        return self

    def tag(
        self,
        x_value: float | str | pd.Timestamp,
        y_value: float,
        label: str,
        label_h_align: str = "center",
        label_v_align: str = "center",
        ubic_etq: tuple = (0, 17),
        fontsize: int = 7,
        fontweight: str = "normal",
        font_color: str = "black",
        bg_color: str = "#ECEFF1",
        bg_alpha: float = 1.0,
        edge_color: str = "none",
        show_bbox: bool = True,
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
        zorder: int = 6,
    ) -> Self:
        """
        Add a text annotation to a specific chart coordinate.

        This method supports standard datetime, numeric, categorical, and
        Bloomberg-style x-axis modes. It can optionally display the label inside a
        rounded bounding box and apply a text stroke to improve readability.

        Parameters
        ----------
        x_value : float, str, pandas.Timestamp, or datetime-like
            X-axis value where the annotation should be placed.
        y_value : float
            Y-axis value where the annotation should be placed.
        label : str
            Text displayed in the annotation.
        label_h_align : str, default "center"
            Horizontal alignment of the annotation text.
        label_v_align : str, default "center"
            Vertical alignment of the annotation text.
        ubic_etq : tuple, default (0, 17)
            Offset in points from the annotated coordinate.
        fontsize : int, default 7
            Font size of the annotation.
        fontweight : str, default "normal"
            Font weight of the annotation.
        font_color : str, default "black"
            Text color.
        bg_color : str, default "#ECEFF1"
            Background color of the annotation box.
        bg_alpha : float, default 1.0
            Transparency of the annotation box.
        edge_color : str, default "none"
            Edge color of the annotation box.
        show_bbox : bool, default True
            Whether to display a background box behind the annotation.
        text_edge_color : str or None, optional
            Optional stroke color applied to the annotation text.
        text_edge_width : float, default 0.0
            Width of the optional text stroke.
        zorder : int, default 6
            Drawing order of the annotation.

        Returns
        -------
        None
            The annotation is added directly to the active axis.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("Axis not initialized.")


        mode = self._x_axis_mode

        # --- Convert x_value ---
        if mode == "bbg":
            x_plot = self._coerce_to_bbg_x(x_value)
        else:
            x_conv = x_value

            if mode == "datetime":
                try:
                    x_conv = pd.to_datetime(x_value)
                except Exception:
                    pass

            x_plot = self._ax.convert_xunits(x_conv)

            if np.ndim(x_plot) > 0:
                x_plot = np.asarray(x_plot).item()

        # --- Bounding box config ---
        bbox = None
        if show_bbox:
            bbox = dict(
                boxstyle="round,pad=0.4",
                fc=bg_color,
                ec=edge_color,
                alpha=bg_alpha
            )

        # --- Annotate ---
        annotation = self._ax.annotate(
            label,
            xy=(x_plot, y_value),
            xytext=ubic_etq,
            textcoords="offset points",
            ha=label_h_align,
            va=label_v_align,
            fontsize=fontsize,
            fontweight=fontweight,
            color=font_color,
            bbox=bbox,
            zorder=zorder
        )

        # Optional text stroke to improve readability over busy backgrounds.
        if text_edge_color is not None and text_edge_width and text_edge_width > 0:
            annotation.set_path_effects([
                path_effects.withStroke(linewidth=text_edge_width, foreground=text_edge_color)
            ])

        return self
    
    def dot(
        self,
        x_value,
        y_value,
        color="red",
        size=30,
        zorder=5
    ) -> Self:
        """
        Add a highlighted point marker to the active chart.

        This method supports standard datetime, numeric, categorical, and
        Bloomberg-style x-axis modes.

        Parameters
        ----------
        x_value : any
            X-axis value where the marker should be placed.
        y_value : float
            Y-axis value where the marker should be placed.
        color : str, default "red"
            Marker color.
        size : float, default 30
            Marker size.
        zorder : int, default 5
            Drawing order of the marker.

        Returns
        -------
        None
            The marker is added directly to the active axis.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("Axis not initialized.")

        mode = self._x_axis_mode

        # --- Convert x_value ---
        if mode == "bbg":
            x_plot = self._coerce_to_bbg_x(x_value)
        else:
            x_conv = x_value

            if mode == "datetime":
                try:
                    x_conv = pd.to_datetime(x_value)
                except Exception:
                    pass

            x_plot = self._ax.convert_xunits(x_conv)

            if np.ndim(x_plot) > 0:
                x_plot = np.asarray(x_plot).item()

        # --- Plot point ---
        self._ax.scatter(
            x_plot,
            y_value,
            color=color,
            s=size,
            zorder=zorder
        )

        return self

    def shade_x(
        self,
        periods,
        color="#B0B0B0",
        alpha=0.25,
        zorder=0,
        label=None,
        hatch=None,
        ymin=0.0,
        ymax=1.0,
        clip_to_xlim=True,
    ) -> Self:
        """
        Add shaded vertical regions to the active chart.

        This method highlights one or multiple x-axis periods using vertical shaded
        spans. It supports datetime, numeric, categorical, Bloomberg-style, and bar
        chart x-axis modes. For categorical bar charts in `bar_mode="last"`, the
        method can shade entire bar clusters instead of only individual x positions.

        Parameters
        ----------
        periods : tuple, list[tuple], or list[dict]
            Period or periods to shade. A simple period can be provided as
            `(start, end)`. Multiple periods can be provided as a list of tuples.
            Each period can also be a dictionary with keys such as `start`, `end`,
            `color`, `alpha`, `label`, and `hatch`.
        color : str, default "#B0B0B0"
            Default fill color of the shaded region.
        alpha : float, default 0.25
            Default transparency of the shaded region.
        zorder : int, default 0
            Drawing order of the shaded region.
        label : str or None, optional
            Optional legend label for the shaded region.
        hatch : str or None, optional
            Optional hatch pattern for the shaded region.
        ymin : float, default 0.0
            Lower vertical bound of the shaded region in axis-relative coordinates.
        ymax : float, default 1.0
            Upper vertical bound of the shaded region in axis-relative coordinates.
        clip_to_xlim : bool, default True
            Whether to clip shaded regions to the current x-axis limits.

        Returns
        -------
        None
            Shaded regions are added directly to the active axis.

        Raises
        ------
        RuntimeError
            If the active axis has not been initialized.

        Notes
        -----
        When multiple periods are provided and `label` is used, the default label is
        applied only once to avoid duplicate legend entries.
        """

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("No axis found. Call graph_line/graph_bar first.")

        if isinstance(periods, tuple) and len(periods) == 2:
            periods = [periods]

        mode = self._x_axis_mode
        bar_meta = self._bar_mode

        used_label = False
        xlim = self._ax.get_xlim()

        # ==========================================================
        # Helpers locales para bar_mode="last"
        # ==========================================================
        def _collect_rects_for_idx(idx: int) -> list:
            """
            Execute `_collect_rects_for_idx` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            rects = []

            if not hasattr(self, "_bars_data") or not self._bars_data:
                return rects

            for entry in self._bars_data.values():
                bars_obj = entry.get("bars")

                # --- stacked
                if isinstance(bars_obj, dict):
                    for side in ("pos", "neg"):
                        bars_side = bars_obj.get(side)
                        if bars_side is None or idx >= len(bars_side):
                            continue

                        rect = bars_side[idx]
                        if rect is None:
                            continue

                        try:
                            h = rect.get_height()
                        except Exception:
                            h = None

                        if h is None:
                            continue

                        try:
                            if np.isnan(h):
                                continue
                        except Exception:
                            pass

                        rects.append(rect)

                # --- grouped / single
                else:
                    if bars_obj is None or idx >= len(bars_obj):
                        continue

                    rect = bars_obj[idx]
                    if rect is None:
                        continue

                    try:
                        h = rect.get_height()
                    except Exception:
                        h = None

                    if h is None:
                        continue

                    try:
                        if np.isnan(h):
                            continue
                        # si quieres excluir barras vacías:
                        # if abs(h) == 0:
                        #     continue
                    except Exception:
                        pass

                    rects.append(rect)

            return rects

        def _cluster_bounds(idx: int, default_half_width: float = 0.4) -> tuple[float, float]:
            """
            Execute `_cluster_bounds` as part of the chart-building workflow.

            Notes
            -----
            This docstring was added during the modular refactor to make the API easier
            to understand for new users and maintainers.
            """
            rects = _collect_rects_for_idx(idx)

            if not rects:
                center = float(idx)
                return center - default_half_width, center + default_half_width

            left = min(r.get_x() for r in rects)
            right = max(r.get_x() + r.get_width() for r in rects)
            return float(left), float(right)

        # ==========================================================
        # Main
        # ==========================================================
        for p in periods:
            if isinstance(p, dict):
                start = p.get("start")
                end = p.get("end")
                c = p.get("color", color)
                a = p.get("alpha", alpha)
                lab = p.get("label", None)
                hat = p.get("hatch", hatch)
            else:
                start, end = p
                c, a, lab, hat = color, alpha, None, hatch

            if mode == "bbg":
                x0 = self._coerce_to_bbg_x(start)
                x1 = self._coerce_to_bbg_x(end)

            elif bar_meta is not None and bar_meta == "last":
                xticklabels = [t.get_text() for t in self._ax.get_xticklabels()]

                def _to_pos(val):
                    # string => buscar en labels del eje
                    """
                    Execute `_to_pos` as part of the chart-building workflow.

                    Notes
                    -----
                    This docstring was added during the modular refactor to make the API easier
                    to understand for new users and maintainers.
                    """
                    if isinstance(val, str):
                        if val not in xticklabels:
                            raise ValueError(f"{val} not found in x labels")
                        return int(xticklabels.index(val))

                    # enteros => posición categórica
                    if isinstance(val, (int, np.integer)):
                        return int(val)

                    # floats enteros => posición categórica
                    if isinstance(val, (float, np.floating)) and float(val).is_integer():
                        return int(val)

                    # cualquier otro numérico fino => usar directo
                    return float(val)

                p0 = _to_pos(start)
                p1 = _to_pos(end)

                if isinstance(p0, (int, np.integer)) and isinstance(p1, (int, np.integer)):
                    left0, right0 = _cluster_bounds(int(p0))
                    left1, right1 = _cluster_bounds(int(p1))
                    x0 = left0
                    x1 = right1
                else:
                    x0 = float(p0)
                    x1 = float(p1)

            else:
                s = start
                e = end

                if mode == "datetime":
                    try:
                        s = pd.to_datetime(start)
                    except Exception:
                        pass

                    try:
                        e = pd.to_datetime(end)
                    except Exception:
                        pass

                    # widen only for bar charts in time mode
                    if bar_meta is not None and bar_meta == "time":
                        delta = pd.Timedelta(days=15)
                        s = s - delta
                        e = e + delta

                x0 = self._ax.convert_xunits(s)
                x1 = self._ax.convert_xunits(e)

                if np.ndim(x0) > 0:
                    x0 = np.asarray(x0).item()
                if np.ndim(x1) > 0:
                    x1 = np.asarray(x1).item()

            if x1 < x0:
                x0, x1 = x1, x0

            if clip_to_xlim:
                x0 = max(x0, xlim[0])
                x1 = min(x1, xlim[1])
                if x1 <= x0:
                    continue

            final_label = None
            if lab is not None:
                final_label = lab
            elif label is not None and not used_label:
                final_label = label
                used_label = True

            self._ax.axvspan(
                x0,
                x1,
                ymin=ymin,
                ymax=ymax,
                facecolor=c,
                alpha=a,
                zorder=zorder,
                label=final_label,
                hatch=hat
            )

        return self

    # =========================
    # Metodos de lineas
    # =========================
    def vertical_lines(
        self: Self,
        x_values: list[float | str | pd.Timestamp] | float | str | pd.Timestamp | None = None,
        linestyle: str | None = None,
        linewidth: float = 0.5,
        color: str = "gray",
        alpha: float = 1.0,
        ymin: float = 0.0,
        ymax: float = 1.0,
        labels: list[str] | str | None = None,
        zorder: int = 4,
    ) -> Self:
        """
        Add one or more vertical reference lines to the active axis.

        This method supports standard numeric, datetime, categorical, and
        Bloomberg-style x-axis modes. It is intended to be used as a chainable
        public helper after a chart has been created.

        Parameters
        ----------
        x_values:
            X-axis value or values where vertical lines should be drawn.
            If None, no lines are added.
        linestyle:
            Matplotlib line style used for the reference lines.
        linewidth:
            Width of the reference lines.
        color:
            Color of the reference lines.
        alpha:
            Transparency of the reference lines.
        ymin:
            Lower vertical bound of the line in axis-relative coordinates.
        ymax:
            Upper vertical bound of the line in axis-relative coordinates.
        labels:
            Optional label or list of labels for legend integration.
        zorder:
            Drawing order of the reference lines.

        Returns
        -------
        Graph_base
            The current graph object.
        """
        if x_values is None:
            return self

        if not hasattr(self, "_ax") or self._ax is None:
            raise RuntimeError("No active axis found. Create a chart before adding vertical lines.")

        if not isinstance(x_values, (list, tuple, set)):
            x_values = [x_values]
        else:
            x_values = list(x_values)

        if labels is None:
            labels = [None] * len(x_values)
        elif isinstance(labels, str):
            labels = [labels] + [None] * (len(x_values) - 1)
        else:
            labels = list(labels)
            if len(labels) < len(x_values):
                labels = labels + [None] * (len(x_values) - len(labels))

        mode = self._x_axis_mode

        for i, x in enumerate(x_values):
            label = labels[i] if i < len(labels) else None

            if mode == "bbg":
                x_plot = self._coerce_to_bbg_x(x)

            elif mode == "datetime":
                try:
                    x_conv = pd.to_datetime(x)
                except Exception:
                    x_conv = x

                x_plot = self._ax.convert_xunits(x_conv)

                if np.ndim(x_plot) > 0:
                    x_plot = np.asarray(x_plot).item()

            elif mode == "categorical":
                x_plot = x

                if isinstance(x, str):
                    xticklabels = [tick.get_text() for tick in self._ax.get_xticklabels()]

                    if x in xticklabels:
                        x_plot = xticklabels.index(x)

            else:
                x_plot = x

            self._ax.axvline(
                x=x_plot,
                ymin=ymin,
                ymax=ymax,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=alpha,
                label=label,
                zorder=zorder,
            )

        return self

    def horizontal_lines(
        self,
        y_values: list[float] | float | None = None,
        linestyle: str | None = None,
        linewidth: float = 0.5,
        color: str = "gray",
        alpha: float = 1.0,
        side: str = "left",
        ax=None,
        label: str | None = None,
        zorder: int = 4,
    ):
        """
        Add one or more horizontal reference lines to one y-axis.

        Parameters
        ----------
        y_values:
            Y-axis value or values where horizontal lines should be drawn.
            If None, no lines are added.
        linestyle:
            Matplotlib line style used for the reference lines.
        linewidth:
            Width of the reference lines.
        color:
            Color of the reference lines.
        alpha:
            Transparency of the reference lines.
        side:
            Axis side where lines should be added. Use 'left' or 'right'.
        ax:
            Explicit Matplotlib axis to use. If provided, side is ignored for
            axis selection.
        label:
            Optional legend label. Applied only to the first line to avoid duplicates.
        zorder:
            Drawing order of the reference lines.

        Returns
        -------
        Graph_base
            Current graph object.
        """
        if y_values is None:
            return self

        if ax is not None:
            target_ax = ax

        elif side == "right":
            if getattr(self, "_right_ax", None) is None:
                raise RuntimeError("No right axis exists for the active chart.")
            target_ax = self._right_ax

        elif side == "left":
            target_ax = self._ax

        else:
            raise ValueError("side must be either 'left' or 'right'.")

        if target_ax is None:
            raise RuntimeError("No axis available. Create a chart before adding lines.")

        if isinstance(y_values, (int, float)):
            y_values = [y_values]

        for i, y in enumerate(y_values):
            target_ax.axhline(
                y,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=alpha,
                label=label if i == 0 else None,
                zorder=zorder,
            )

        return self

    # =========================
    # Metodos para agregar recesiones a las graficas
    # =========================
    def add_recessions(
            self,
            country: str = "United States",
            data_frame: bool = False,
            controles: dict = None
    ):
        """
        Add recession shading to a date-based chart.

        This method reads recession periods from the package's recession dataset and
        shades the corresponding date ranges on the active chart. It only works with
        date-based x-axis modes, including standard datetime axes and
        Bloomberg-style axes.

        Parameters
        ----------
        country : str, default "United States"
            Country used to filter the recession dataset.
        data_frame : bool, default False
            If True, return the recession dataset instead of plotting the shaded
            regions.
        controles : dict or None, optional
            Styling parameters passed to `shade_x`, such as `color`, `alpha`,
            `label`, or `hatch`.

        Returns
        -------
        pandas.DataFrame or None
            Returns the recession DataFrame when `data_frame=True`; otherwise,
            returns None after adding the shaded regions.

        Raises
        ------
        RuntimeError
            If no active chart exists.
        TypeError
            If the active chart does not use a date-based x-axis.
        NotImplementedError
            If the selected country is not available in the recession dataset.
        """
        csv_path = files("helpers_ps").joinpath("Data/recessions.csv")
        recesiones = pd.read_csv(csv_path, parse_dates=["start_date", "end_date"])
        recesiones = recesiones.set_index("recesion_id")
        if data_frame:
            return recesiones
        
        # plotear en el eje
        if self._ax is None:
            raise RuntimeError("No existe grafico para agregar las recesiones")
        
        if self._x_axis_mode not in ["bbg", "datetime"]:
            raise TypeError("No se pueden aplicar recesiones a un grafico que no tiene como eje fechas")
        
        if country not in recesiones["country"].unique():
            raise NotImplementedError("No hay registro de recesiones para ese pais")
        
        recesiones = recesiones[recesiones["country"] == country].copy()
        
        # agregar recesiones a la grafica
        date_list = [(recesiones.loc[x,"start_date"].strftime("%Y-%m-%d"), recesiones.loc[x,"end_date"].strftime("%Y-%m-%d")) for x in recesiones.index.tolist()]
        controles = controles if controles is not None else dict(color="grey", alpha=0.3)
        self.shade_x(periods=date_list, **controles)

        return None

