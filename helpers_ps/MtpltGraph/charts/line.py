from __future__ import annotations

from typing import Self

import pandas as pd

from ..models import (
    XAxisConfig,
    YAxisConfig,
    LegendConfig,
    FigureTitle,
    FigureSubtitle,
    FigureSource,
    coerce_configs,
)
from ..tags._colors import PALETA_COLORES


class LineChartMixin:
    """
    Provides line chart construction logic for GraphMtplt.
    """

    def _plot_line_series(
        self,
        dataframe: pd.DataFrame,
        series_config: list[dict],
        left_ax,
        right_ax,
        lw: float,
    ) -> None:
        for item in series_config:
            ticker = item["ticker"]
            label = item["label"]
            color = item["color"]
            selected_side = item["axis_side"]

            serie_df = dataframe[[ticker]].copy()

            if serie_df.empty:
                continue

            plot_ax = right_ax if selected_side == "right" else left_ax

            if plot_ax is None:
                raise RuntimeError("Right axis was not initialized correctly.")

            if self._x_axis_mode == "bbg":
                serie = serie_df.reindex(self._x_axis_fechas)[ticker]

                plot_ax.plot(
                    self._x_vals,
                    serie.to_numpy(),
                    color=color,
                    lw=lw,
                    label=label,
                )
            else:
                x_plot = (
                    self._x_vals
                    if self._x_axis_mode == "categorical"
                    else serie_df.index
                )

                plot_ax.plot(
                    x_plot,
                    serie_df[ticker],
                    color=color,
                    lw=lw,
                    label=label,
                )

    def graph_line(
        self,
        figsize: tuple[float, float] = (6.00, 5.00),
        title: dict | FigureTitle | None = None,
        subtitle: dict | FigureSubtitle | None = None,
        source: dict | FigureSource | None = None,
        df_index: int = 0,
        tickers: list[str] | str = "all",
        labels: list[str] | str | dict[str, str] | None = None,
        colors: list[str] | str | dict[str, str] = PALETA_COLORES,
        lw: float = 1.6,
        tag_dot: dict | None = None,
        y_axis: dict | YAxisConfig | None = None,
        axis_side: str | list[str] | dict[str, str] | None = None,
        y_axis_right: dict | YAxisConfig | None = None,
        x_axis: dict | XAxisConfig | None = None,
        legend: dict | LegendConfig | None = None,
        hlines: dict | None = None,
        show_hguide: bool = False,
    ) -> Self:
        db = self._select_df(df_idx=df_index)

        series_config = self._normalize_series_config(
            dataframe=db,
            tickers=tickers,
            labels=labels,
            colors=colors,
            axis_side=axis_side,
        )

        axis_map = {
            item["ticker"]: item["axis_side"]
            for item in series_config
        }

        state = self._ensure_active_state()
        state.series_config = series_config
        state.axis_map = axis_map
        state.ticker_label_color = [
            (item["ticker"], item["label"], item["color"])
            for item in series_config
        ]

        configs = coerce_configs(
            x_axis=(x_axis, XAxisConfig),
            y_axis=(y_axis, YAxisConfig),
            y_axis_right=(y_axis_right, YAxisConfig),
            title=(title, FigureTitle),
            subtitle=(subtitle, FigureSubtitle),
            legend=(legend, LegendConfig),
            source=(source, FigureSource),
        )

        x_axis = configs["x_axis"]
        y_axis = configs["y_axis"]
        y_axis_right = configs["y_axis_right"]
        title = configs["title"]
        subtitle = configs["subtitle"]
        legend = configs["legend"]
        source = configs["source"]

        hlines = hlines if hlines is not None else {}

        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        left_ax, right_ax = self._resolve_line_axes(axis_map)

        self.add_title(**title)
        self.add_subtitle(**subtitle)
        self.add_source(**source)

        db = self.prep_x_axis(dataframe=db, **x_axis)

        self._plot_line_series(
            dataframe=db,
            series_config=series_config,
            left_ax=left_ax,
            right_ax=right_ax,
            lw=lw,
        )

        self._apply_line_tags_by_axis(
            tag_dot=tag_dot,
            axis_map=axis_map,
            left_ax=left_ax,
            right_ax=right_ax,
        )

        self.config_yaxis(
            ax=left_ax,
            side="left",
            **y_axis,
        )

        if right_ax is not None:
            self.config_yaxis(
                ax=right_ax,
                side="right",
                **y_axis_right,
            )

        self._ax = left_ax

        if hlines:
            hlines.setdefault("side", "left")
            self.horizontal_lines(**hlines)

        if show_hguide:
            self.horizontal_guides(
                side="both" if right_ax is not None else "left",
                mostrar_cero=False,
            )

        self.add_combined_legend(
            ax=left_ax,
            include_right_axis=right_ax is not None,
            **legend,
        )

        self._ax = left_ax

        return self