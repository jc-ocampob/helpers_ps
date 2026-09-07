from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from typing import Any, Self

import numpy as np
import pandas as pd

from ..models import (
    BarSeriesConfig,
    BarSeriesDict,
    BarSeriesLike,
    XAxisConfig,
    XAxisLike,
    coerce_configs,
    config_to_dict,
)

from ..tags._colors import PALETA_COLORES


class BarChartMixin:
    """
    Provides bar-chart construction logic for GraphMtplt.
    """

    def _normalize_bar_series(
        self,
        dataframe: pd.DataFrame,
        series: Sequence[BarSeriesLike] | None = None,
    ) -> list[BarSeriesDict]:
        """
        Normalize and validate bar-series configurations.

        If series is None, all DataFrame columns are included using
        their default configuration.
        """
        if series is None:
            series = [
                BarSeriesConfig(
                    ticker=str(column),
                )
                for column in dataframe.columns
            ]

        if not series:
            raise ValueError(
                "'series' cannot be empty. "
                "Use None to plot all DataFrame columns."
            )

        normalized: list[BarSeriesConfig] = []

        for position, item in enumerate(series):
            if isinstance(item, BarSeriesConfig):
                config = item

            elif isinstance(item, dict):
                try:
                    config = BarSeriesConfig(**item)

                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "Invalid bar series configuration at "
                        f"position {position}: {item}."
                    ) from exc

            else:
                raise TypeError(
                    "Each item in 'series' must be a dictionary "
                    "or a BarSeriesConfig instance."
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
            if config.label is None:
                config.label = config.ticker

            if config.color is None:
                config.color = PALETA_COLORES[
                    position % len(PALETA_COLORES)
                ]

        return [
            BarSeriesDict(**asdict(config))
            for config in normalized
        ]

    def _prepare_bar_x_values(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[np.ndarray, float]:
        """
        Return numeric bar positions and the base distance between
        consecutive observations.
        """
        if self._x_axis_mode in {"bbg", "categorical"}:
            x_values = np.asarray(
                self._x_vals,
                dtype=float,
            )

        elif pd.api.types.is_datetime64_any_dtype(
            dataframe.index
        ):
            x_values = np.asarray(
                self._ax.convert_xunits(
                    pd.to_datetime(dataframe.index)
                ),
                dtype=float,
            )

        elif pd.api.types.is_numeric_dtype(
            dataframe.index
        ):
            x_values = np.asarray(
                dataframe.index,
                dtype=float,
            )

        else:
            x_values = np.arange(
                len(dataframe.index),
                dtype=float,
            )

        finite_values = x_values[
            np.isfinite(x_values)
        ]

        unique_values = np.sort(
            np.unique(finite_values)
        )

        differences = np.diff(unique_values)

        positive_differences = differences[
            differences > 0
        ]

        base_step = (
            float(np.median(positive_differences))
            if len(positive_differences)
            else 1.0
        )

        return x_values, base_step

    def _get_bar_values(
        self,
        dataframe: pd.DataFrame,
        ticker: str,
    ) -> np.ndarray:
        """
        Return a bar series aligned with the active X-axis.
        """
        if self._x_axis_mode == "bbg":
            return (
                dataframe[ticker]
                .reindex(self._x_axis_fechas)
                .to_numpy(dtype=float)
            )

        return dataframe[ticker].to_numpy(
            dtype=float
        )

    def _split_bar_values(
        self,
        values: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Split values into positive and negative arrays.

        Missing values are converted to zero so they do not affect
        accumulated stack positions.
        """
        values = np.asarray(
            values,
            dtype=float,
        )

        positive = np.where(
            np.isnan(values),
            0.0,
            np.maximum(values, 0.0),
        )

        negative = np.where(
            np.isnan(values),
            0.0,
            np.minimum(values, 0.0),
        )

        return positive, negative

    def _plot_bar_series(
        self,
        dataframe: pd.DataFrame,
        series_config: list[BarSeriesDict],
        left_ax,
        right_ax,
        grouped: bool,
        stacked: bool,
        bar_width: float,
        alpha: float,
    ) -> dict[str, dict[str, Any]]:
        """
        Plot bar series on their configured axes.
        """
        x_values, base_step = (
            self._prepare_bar_x_values(
                dataframe=dataframe,
            )
        )

        series_count = len(series_config)

        bars_data: dict[
            str,
            dict[str, Any],
        ] = {}

        def get_axis(item: BarSeriesDict):
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

            return plot_ax

        if stacked:
            stack_axis = get_axis(
                series_config[0]
            )

            bottom_positive = np.zeros(
                len(x_values),
                dtype=float,
            )

            bottom_negative = np.zeros(
                len(x_values),
                dtype=float,
            )

            width = min(
                bar_width * base_step,
                0.85 * base_step,
            )

            for item in series_config:
                ticker = item["ticker"]

                values = self._get_bar_values(
                    dataframe=dataframe,
                    ticker=ticker,
                )

                positive, negative = (
                    self._split_bar_values(values)
                )

                positive_bars = stack_axis.bar(
                    x_values,
                    positive,
                    width=width,
                    bottom=bottom_positive,
                    color=item["color"],
                    alpha=alpha,
                    label=item["label"],
                    zorder=3,
                )

                negative_bars = stack_axis.bar(
                    x_values,
                    negative,
                    width=width,
                    bottom=bottom_negative,
                    color=item["color"],
                    alpha=alpha,
                    label="_nolegend_",
                    zorder=3,
                )

                bottom_positive += positive
                bottom_negative += negative

                bars_data[ticker] = {
                    "bars": {
                        "pos": positive_bars,
                        "neg": negative_bars,
                    },
                    "ticker": ticker,
                    "label": item["label"],
                    "color": item["color"],
                    "axis_side": item["axis_side"],
                    "x_values": x_values.copy(),
                    "values": values.copy(),
                }

            return bars_data

        if grouped and series_count > 1:
            group_width = min(
                bar_width * base_step,
                0.80 * base_step,
            )

            individual_width = (
                group_width / series_count
            )

            for position, item in enumerate(
                series_config
            ):
                ticker = item["ticker"]
                plot_ax = get_axis(item)

                values = self._get_bar_values(
                    dataframe=dataframe,
                    ticker=ticker,
                )

                offset = (
                    position
                    - (series_count - 1) / 2
                ) * individual_width

                plotted_x = x_values + offset

                bars = plot_ax.bar(
                    plotted_x,
                    values,
                    width=individual_width,
                    color=item["color"],
                    alpha=alpha,
                    label=item["label"],
                    zorder=3,
                )

                bars_data[ticker] = {
                    "bars": bars,
                    "ticker": ticker,
                    "label": item["label"],
                    "color": item["color"],
                    "axis_side": item["axis_side"],
                    "x_values": plotted_x.copy(),
                    "base_x_values": x_values.copy(),
                    "values": values.copy(),
                }

            return bars_data

        item = series_config[0]
        ticker = item["ticker"]
        plot_ax = get_axis(item)

        values = self._get_bar_values(
            dataframe=dataframe,
            ticker=ticker,
        )

        width = min(
            bar_width * base_step,
            0.85 * base_step,
        )

        bars = plot_ax.bar(
            x_values,
            values,
            width=width,
            color=item["color"],
            alpha=alpha,
            label=item["label"],
            zorder=3,
        )

        bars_data[ticker] = {
            "bars": bars,
            "ticker": ticker,
            "label": item["label"],
            "color": item["color"],
            "axis_side": item["axis_side"],
            "x_values": x_values.copy(),
            "values": values.copy(),
        }

        return bars_data

    def graph_bar(
        self,
        series: Sequence[BarSeriesLike] | None = None,
        df_index: int = 0,
        grouped: bool | None = None,
        stacked: bool = False,
        bar_width: float = 0.8,
        alpha: float = 0.95,
        x_axis: XAxisLike | None = None,
    ) -> Self:
        """
        Add bar series to the active figure.

        If series is None, all DataFrame columns are plotted using:

        - Column name as label.
        - Automatic palette colors.
        - Left axis.
        - Grouped bars when multiple columns exist.
        - No tags.
        """
        if not isinstance(bar_width, (int, float)):
            raise TypeError(
                "'bar_width' must be numeric."
            )

        if not 0 < bar_width <= 1:
            raise ValueError(
                "'bar_width' must be greater than zero "
                "and less than or equal to one."
            )

        if not isinstance(alpha, (int, float)):
            raise TypeError(
                "'alpha' must be numeric."
            )

        if not 0 <= alpha <= 1:
            raise ValueError(
                "'alpha' must be between zero and one."
            )

        if not isinstance(stacked, bool):
            raise TypeError(
                "'stacked' must be a boolean."
            )

        if (
            grouped is not None
            and not isinstance(grouped, bool)
        ):
            raise TypeError(
                "'grouped' must be a boolean or None."
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

        series_config = self._normalize_bar_series(
            dataframe=dataframe,
            series=series,
        )

        series_count = len(series_config)

        if grouped is None:
            grouped = (
                series_count > 1
                and not stacked
            )

        if stacked and grouped:
            raise ValueError(
                "'stacked' and 'grouped' cannot both be True."
            )

        if (
            not stacked
            and not grouped
            and series_count > 1
        ):
            raise ValueError(
                "Multiple bar series require grouped=True "
                "or stacked=True."
            )

        axis_map = {
            item["ticker"]: item["axis_side"]
            for item in series_config
        }

        if (
            stacked
            and len(set(axis_map.values())) > 1
        ):
            raise ValueError(
                "Stacked bars cannot use mixed left and "
                "right axes."
            )

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

        state.bar_grouped = grouped
        state.bar_stacked = stacked

        if not hasattr(self, "_ax") or self._ax is None:
            self.plot()

        left_ax, right_ax = self._resolve_line_axes(
            axis_map=axis_map,
        )

        dataframe = self.prep_x_axis(
            dataframe=dataframe,
            **x_axis_config,
        )

        if self._x_axis_mode == "categorical":
            categorical_x = np.arange(
                len(dataframe.index),
                dtype=float,
            )

            self._x_vals = categorical_x

            left_ax.set_xticks(
                categorical_x
            )

            left_ax.set_xticklabels(
                [
                    str(value)
                    for value in dataframe.index
                ]
            )

        bars_data = self._plot_bar_series(
            dataframe=dataframe,
            series_config=series_config,
            left_ax=left_ax,
            right_ax=right_ax,
            grouped=grouped,
            stacked=stacked,
            bar_width=float(bar_width),
            alpha=float(alpha),
        )

        state.bars_data = bars_data

        state.bars_x_reference = (
            list(self._x_axis_fechas)
            if self._x_axis_mode == "bbg"
            else list(dataframe.index)
        )

        self._apply_bar_tags(
            series_config=series_config,
            bars_data=bars_data,
            x_reference=state.bars_x_reference,
            left_ax=left_ax,
            right_ax=right_ax,
        )

        self._ax = left_ax

        return self