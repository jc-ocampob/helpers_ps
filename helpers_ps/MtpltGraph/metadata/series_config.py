from __future__ import annotations

from typing import Any

import pandas as pd

from ..tags._colors import PALETA_COLORES


def normalize_series_config(
    dataframe: pd.DataFrame,
    tickers: list[str] | tuple[str, ...] | set[str] | str = "all",
    labels: list[str] | tuple[str, ...] | str | dict[str, str] | None = None,
    colors: list[str] | tuple[str, ...] | str | dict[str, str] | None = None,
    axis_side: str | list[str] | tuple[str, ...] | dict[str, str] | None = None,
    default_axis_side: str = "left",
) -> list[dict[str, Any]]:
    """
    Normalize tickers, labels, colors, and axis-side configuration into one list.

    This avoids fragile parallel-list handling inside graph_line and graph_bar.
    """

    if dataframe is None or not isinstance(dataframe, pd.DataFrame):
        raise TypeError("`dataframe` must be a pandas DataFrame.")

    available_columns = dataframe.columns.tolist()

    # -------------------------------------------------
    # 1. Normalize tickers
    # -------------------------------------------------
    if isinstance(tickers, str):
        if tickers == "all":
            normalized_tickers = available_columns.copy()
        else:
            normalized_tickers = [tickers]

    elif isinstance(tickers, (list, tuple, set)):
        normalized_tickers = list(tickers)

    else:
        raise TypeError(
            "`tickers` must be 'all', a string, or a list-like object."
        )

    normalized_tickers = [
        ticker
        for ticker in normalized_tickers
        if ticker in available_columns
    ]

    if not normalized_tickers:
        raise ValueError("No valid tickers were found in the dataframe.")

    # -------------------------------------------------
    # 2. Normalize labels
    # -------------------------------------------------
    if labels is None:
        labels_map = {
            ticker: ticker
            for ticker in normalized_tickers
        }

    elif isinstance(labels, str):
        labels_map = {
            ticker: ticker
            for ticker in normalized_tickers
        }
        labels_map[normalized_tickers[0]] = labels

    elif isinstance(labels, dict):
        labels_map = {
            ticker: labels.get(ticker, ticker)
            for ticker in normalized_tickers
        }

    elif isinstance(labels, (list, tuple)):
        labels_list = list(labels)
        labels_map = {
            ticker: labels_list[i] if i < len(labels_list) else ticker
            for i, ticker in enumerate(normalized_tickers)
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
        colors_map = {
            ticker: colors
            for ticker in normalized_tickers
        }

    elif isinstance(colors, dict):
        colors_map = {
            ticker: colors.get(
                ticker,
                PALETA_COLORES[i % len(PALETA_COLORES)],
            )
            for i, ticker in enumerate(normalized_tickers)
        }

    elif isinstance(colors, (list, tuple)):
        colors_list = list(colors)
        colors_map = {
            ticker: (
                colors_list[i]
                if i < len(colors_list)
                else PALETA_COLORES[i % len(PALETA_COLORES)]
            )
            for i, ticker in enumerate(normalized_tickers)
        }

    else:
        colors_map = {
            ticker: PALETA_COLORES[i % len(PALETA_COLORES)]
            for i, ticker in enumerate(normalized_tickers)
        }

    # -------------------------------------------------
    # 4. Normalize axis side
    # -------------------------------------------------
    if axis_side is None:
        axis_map = {
            ticker: default_axis_side
            for ticker in normalized_tickers
        }

    elif isinstance(axis_side, str):
        if axis_side not in {"left", "right"}:
            raise ValueError("`axis_side` must be either 'left' or 'right'.")

        axis_map = {
            ticker: axis_side
            for ticker in normalized_tickers
        }

    elif isinstance(axis_side, dict):
        axis_map = {
            ticker: axis_side.get(ticker, default_axis_side)
            for ticker in normalized_tickers
        }

    elif isinstance(axis_side, (list, tuple)):
        axis_side_list = list(axis_side)
        axis_map = {
            ticker: (
                axis_side_list[i]
                if i < len(axis_side_list)
                else default_axis_side
            )
            for i, ticker in enumerate(normalized_tickers)
        }

    else:
        raise TypeError(
            "`axis_side` must be None, a string, a list-like object, or a dictionary."
        )

    invalid_sides = {
        side
        for side in axis_map.values()
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
        for ticker in normalized_tickers
    ]


def get_series_meta(
    series_config: list[dict[str, Any]],
    ticker: str,
) -> dict[str, Any]:
    """
    Return normalized metadata for one ticker.
    """

    for item in series_config:
        if item.get("ticker") == ticker:
            return item

    raise KeyError(f"No series metadata found for ticker: {ticker}")