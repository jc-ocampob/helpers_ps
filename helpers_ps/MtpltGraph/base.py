from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .tags._colors import PALETA_COLORES
from .metadata import GraphMetaData
from .config import buffers
from .mixins.annotations import AnnotationMixin
from .mixins.axes import AxesMixin
from .mixins.chain import ChainMixin
from .mixins.export import ExportMixin
from .mixins.layout import LayoutMixin
from .mixins.legends import LegendMixin
from .mixins.recessions import RecessionMixin
from .mixins.reference_lines import ReferenceLinesMixin

@dataclass
class Graph_base(
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
