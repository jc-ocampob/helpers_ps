from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from typing import Any, Self

import pandas as pd

from ..models import (
    LineSeriesConfig,
    LineSeriesDict,
    LineSeriesLike,
    XAxisConfig,
    XAxisLike,
    coerce_configs,
    config_to_dict,
)
from ..tags._colors import PALETA_COLORES


class LineChartMixin:
    """
    Provides line chart construction logic for GraphMtplt.
    """

    def _normalize_line_series(
        self,
        dataframe: pd.DataFrame,
        series: Sequence[LineSeriesLike] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Normalize and validate line-series configurations.

        If series is None, all DataFrame columns are included using
        their default configuration.
        """
        if series is None:
            series = [
                LineSeriesConfig(ticker=str(column))
                for column in dataframe.columns
            ]

        if not series:
            raise ValueError(
                "'series' cannot be empty. "
                "Use None to plot all DataFrame columns."
            )

        normalized: list[LineSeriesConfig] = []

        for position, item in enumerate(series):
            if isinstance(item, LineSeriesConfig):
                config = item

            elif isinstance(item, dict):
                try:
                    config = LineSeriesConfig(**item)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "Invalid line series configuration at "
                        f"position {position}: {item}."
                    ) from exc

            else:
                raise TypeError(
                    "Each item in 'series' must be a dictionary "
                    "or a LineSeriesConfig instance."
                )

            if config.ticker not in dataframe.columns:
                raise KeyError(
                    f"Ticker '{config.ticker}' was not found "
                    "in the selected DataFrame."
                )

            normalized.append(config)

        tickers = [
            config.ticker
            for config in normalized
        ]

        if len(tickers) != len(set(tickers)):
            raise ValueError(
                "Duplicated tickers are not allowed in 'series'."
            )

        if not PALETA_COLORES:
            raise ValueError(
                "PALETA_COLORES cannot be empty."
            )

        for position, config in enumerate(normalized):
            if config.color is None:
                config.color = PALETA_COLORES[
                    position % len(PALETA_COLORES)
                ]

        return [
            LineSeriesDict(**asdict(config))
            for config in normalized
        ]

    def _plot_line_series(
        self,
        dataframe: pd.DataFrame,
        series_config: list[LineSeriesDict],
        left_ax,
        right_ax,
        default_lw: float,
    ) -> None:
        """
        Plot line series on their configured axes.
        """
        for item in series_config:
            ticker = item["ticker"]
            selected_side = item["axis_side"]

            plot_ax = (
                right_ax
                if selected_side == "right"
                else left_ax
            )

            if plot_ax is None:
                raise RuntimeError(
                    f"Axis '{selected_side}' was not "
                    "initialized correctly."
                )

            series_lw = (
                item["lw"]
                if item["lw"] is not None
                else default_lw
            )

            plot_kwargs = {
                "color": item["color"],
                "lw": series_lw,
                "linestyle": item["linestyle"],
                "label": item["label"],
            }

            if self._x_axis_mode == "bbg":
                serie = dataframe[ticker].reindex(
                    self._x_axis_fechas
                )

                plot_ax.plot(
                    self._x_vals,
                    serie.to_numpy(),
                    **plot_kwargs,
                )

                continue

            x_plot = (
                self._x_vals
                if self._x_axis_mode == "categorical"
                else dataframe.index
            )

            plot_ax.plot(
                x_plot,
                dataframe[ticker],
                **plot_kwargs,
            )

    def graph_line(
        self,
        series: Sequence[ LineSeriesLike] | None = None,
        df_index: int = 0,
        lw: float = 1.6,
        x_axis: XAxisLike | None = None,
    ) -> Self:
        """
        Add line series to the active figure.

        If series is None, all DataFrame columns are plotted using:

        - Column name as label.
        - Automatic palette colors.
        - Left axis.
        - Continuous line style.
        - Default line width.
        """
        if not isinstance(lw, (int, float)):
            raise TypeError(
                "'lw' must be numeric."
            )

        if lw <= 0:
            raise ValueError(
                "'lw' must be greater than zero."
            )

        dataframe = self._select_df(
            df_idx=df_index,
        )

        configs = coerce_configs(
            x_axis=(x_axis, XAxisConfig),
        )

        x_axis_config = config_to_dict(
            configs["x_axis"]
        )

        series_config = self._normalize_line_series(
            dataframe=dataframe,
            series=series,
        )

        axis_map = {
            item["ticker"]: item["axis_side"]
            for item in series_config
        }

        state = self._ensure_active_state()

        state.series_config = series_config
        state.axis_map = axis_map
        state.ticker_label_color = [
            (
                item["ticker"],
                item["label"],
                item["color"],
            )
            for item in series_config
        ]

        if not hasattr(self, "_ax") or self._ax is None:
            self.plot()

        left_ax, right_ax = self._resolve_line_axes(
            axis_map=axis_map,
        )

        dataframe = self.prep_x_axis(
            dataframe=dataframe,
            **x_axis_config,
        )

        self._plot_line_series(
            dataframe=dataframe,
            series_config=series_config,
            left_ax=left_ax,
            right_ax=right_ax,
            default_lw=float(lw),
        )

        self._apply_line_tags(
            dataframe=dataframe,
            series_config=series_config,
            left_ax=left_ax,
            right_ax=right_ax,
        )

        self._ax = left_ax

        return self