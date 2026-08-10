from __future__ import annotations

from typing import Self, Literal

import pandas as pd
import numpy as np

from ..models import (
    XAxisConfig,
    YAxisConfig,
    LegendConfig,
    FigureTitle,
    FigureSubtitle,
    FigureSource,
    coerce_configs,
    config_to_dict
)
from ..tags._colors import PALETA_COLORES

import matplotlib.dates as mdates


class BarChartMixin:

    def _prepare_bar_context(
        self,
        *,
        df_index: int,
        tickers,
        labels,
        colors,
        axis_side,
        stacked: bool,
        grouped: bool,
        bar_mode: str,
        x_axis,
        y_axis,
        y_axis_right,
        right_axis,
        title,
        subtitle,
        source,
        legend,
        hlines,
        bar_labels,
    ):
        db = self._select_df(df_idx=df_index)

        series_config = self._normalize_series_config(
            dataframe=db,
            tickers=tickers,
            labels=labels,
            colors=colors,
            axis_side=axis_side,
        )

        tickers = [item["ticker"] for item in series_config]
        labels = [item["label"] for item in series_config]
        colors = [item["color"] for item in series_config]

        axis_map = {
            item["ticker"]: item["axis_side"]
            for item in series_config
        }

        if stacked and len(set(axis_map.values())) > 1:
            raise ValueError(
                "Mixed left/right axis sides are not supported for stacked bars. "
                "Use one axis side for the full stack, or use grouped=True."
            )

        db = db[tickers].copy()

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

        x_axis = config_to_dict(configs["x_axis"])
        y_axis = config_to_dict(configs["y_axis"])
        y_axis_right = config_to_dict(configs["y_axis_right"])
        title = config_to_dict(configs["title"])
        subtitle = config_to_dict(configs["subtitle"])
        legend = config_to_dict(configs["legend"])
        source = config_to_dict(configs["source"])

        right_axis = right_axis if right_axis is not None else {}
        hlines = hlines if hlines is not None else {}
        bar_labels = bar_labels if bar_labels is not None else {}

        if bar_mode == "auto":
            if len(tickers) == 1:
                bar_mode = "time"
            else:
                bar_mode = "time" if (grouped or stacked) else "last"

        state.bar_mode = bar_mode
        state.right_axis_config = right_axis.copy()
        state.y_axis_right = y_axis_right.copy()

        return {
            "db": db,
            "state": state,
            "series_config": series_config,
            "tickers": tickers,
            "labels": labels,
            "colors": colors,
            "axis_map": axis_map,
            "stacked": stacked,
            "grouped": grouped,
            "bar_mode": bar_mode,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "y_axis_right": y_axis_right,
            "right_axis": right_axis,
            "title": title,
            "subtitle": subtitle,
            "source": source,
            "legend": legend,
            "hlines": hlines,
            "bar_labels": bar_labels,
        }


    def _resolve_bar_axes(self, context: dict):
        state = context["state"]
        axis_map = context["axis_map"]

        left_ax = self._ax
        right_ax = getattr(self, "_right_ax", None)

        needs_right_axis = any(
            side == "right"
            for side in axis_map.values()
        )

        if needs_right_axis:
            if right_ax is None:
                right_ax = left_ax.twinx()

            state.right_ax = right_ax
            state.right_axis_enabled = True
        else:
            state.right_axis_enabled = right_ax is not None

        def get_plot_axis(ticker: str):
            selected_side = axis_map.get(ticker, "left")

            if selected_side == "right":
                if right_ax is None:
                    raise RuntimeError("Right axis was not initialized correctly.")
                return right_ax

            return left_ax

        context["left_ax"] = left_ax
        context["right_ax"] = right_ax
        context["get_plot_axis"] = get_plot_axis

        return context


    def _ensure_bar_figure(self, context: dict, figsize: tuple[float, float]):
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        return self._resolve_bar_axes(context)


    def _apply_bar_layout(self, context: dict):
        title = context["title"]
        subtitle = context["subtitle"]
        source = context["source"]

        self.add_title(**title)
        self.add_subtitle(**subtitle)
        self.add_source(**source)

        return context


    def _plot_time_bars(self, context: dict) -> dict:
        db = context["db"]
        state = context["state"]
        tickers = context["tickers"]
        labels = context["labels"]
        colors = context["colors"]
        grouped = context["grouped"]
        stacked = context["stacked"]
        bar_width = context["bar_width"]
        alpha = context["alpha"]
        x_axis = context["x_axis"]
        left_ax = context["left_ax"]
        get_plot_axis = context["get_plot_axis"]

        bars_data = {}

        db = self.prep_x_axis(dataframe=db, **x_axis)
        context["db"] = db

        if self._x_axis_mode == "bbg":
            state.bars_x_reference = list(self._x_axis_fechas)
        else:
            state.bars_x_reference = list(db.index)

        m = len(tickers)

        if m == 1:
            t = tickers[0]
            plot_ax = get_plot_axis(t)
            s = db[[t]].copy()

            if self._x_axis_mode == "bbg":
                serie = s.reindex(self._x_axis_fechas)[t]
                bars = plot_ax.bar(
                    self._x_vals,
                    serie.to_numpy(),
                    width=min(bar_width, 0.85),
                    color=colors[0],
                    alpha=alpha,
                    label=labels[0],
                    zorder=3,
                )
            else:
                bars = plot_ax.bar(
                    s.index,
                    s[t],
                    width=min(bar_width, 0.85),
                    color=colors[0],
                    alpha=alpha,
                    label=labels[0],
                    zorder=3,
                )

            bars_data[t] = {"bars": bars}
            return bars_data

        if grouped and not stacked:
            return self._plot_time_grouped_bars(context)

        return self._plot_time_stacked_bars(context)
    

    def _plot_time_grouped_bars(self, context: dict) -> dict:
        db = context["db"]
        tickers = context["tickers"]
        labels = context["labels"]
        colors = context["colors"]
        bar_width = context["bar_width"]
        alpha = context["alpha"]
        left_ax = context["left_ax"]
        x_axis = context["x_axis"]
        get_plot_axis = context["get_plot_axis"]

        bars_data = {}
        m = len(tickers)

        if self._x_axis_mode == "bbg":
            base_x = self._x_vals.astype(float)
            width = min(bar_width / m, 0.8 / m)

            for i, t in enumerate(tickers):
                plot_ax = get_plot_axis(t)
                serie = db[[t]].copy().reindex(self._x_axis_fechas)[t]
                offset = (i - (m - 1) / 2) * width

                bars = plot_ax.bar(
                    base_x + offset,
                    serie.to_numpy(),
                    width=width,
                    color=colors[i],
                    alpha=alpha,
                    label=labels[i],
                    zorder=3,
                )

                bars_data[t] = {"bars": bars}

            return bars_data

        x_index = db.index
        is_datetime = pd.api.types.is_datetime64_any_dtype(x_index)
        is_numeric = pd.api.types.is_numeric_dtype(x_index)

        if is_datetime:
            x_num = mdates.date2num(pd.to_datetime(x_index).to_pydatetime())
            diffs = np.diff(np.sort(np.unique(x_num)))
            base_step = np.median(diffs) if len(diffs) else 30.0
            group_total = base_step * 0.8
            width = group_total / m

            for i, t in enumerate(tickers):
                plot_ax = get_plot_axis(t)
                offset = (i - (m - 1) / 2) * width

                bars = plot_ax.bar(
                    x_num + offset,
                    np.asarray(db[t].values, dtype=float),
                    width=width,
                    color=colors[i],
                    alpha=alpha,
                    label=labels[i],
                    zorder=3,
                )

                bars_data[t] = {"bars": bars}

            self._ax.xaxis_date()
            return bars_data

        if is_numeric:
            x_num = np.asarray(x_index.values, dtype=float)
            diffs = np.diff(np.sort(np.unique(x_num)))
            base_step = np.median(diffs) if len(diffs) else 1.0
            group_total = base_step * 0.8
            width = group_total / m

            for i, t in enumerate(tickers):
                plot_ax = get_plot_axis(t)
                offset = (i - (m - 1) / 2) * width

                bars = plot_ax.bar(
                    x_num + offset,
                    np.asarray(db[t].values, dtype=float),
                    width=width,
                    color=colors[i],
                    alpha=alpha,
                    label=labels[i],
                    zorder=3,
                )

                bars_data[t] = {"bars": bars}

            return bars_data

        x = np.arange(len(db.index), dtype=float)
        width = min(bar_width / m, 0.8 / m)

        for i, t in enumerate(tickers):
            plot_ax = get_plot_axis(t)
            offset = (i - (m - 1) / 2) * width

            bars = plot_ax.bar(
                x + offset,
                np.asarray(db[t].values, dtype=float),
                width=width,
                color=colors[i],
                alpha=alpha,
                label=labels[i],
                zorder=3,
            )

            bars_data[t] = {"bars": bars}

        left_ax.set_xticks(x)
        x_font = x_axis.get("fontsize", 8)
        left_ax.set_xticklabels(
            [str(v) for v in db.index],
            fontsize=x_font,
        )

        return bars_data


    def _split_positive_negative(self, values):
        y = np.asarray(values, dtype=float)

        y_pos = np.where(
            np.isnan(y),
            0.0,
            np.where(y > 0, y, 0.0),
        )

        y_neg = np.where(
            np.isnan(y),
            0.0,
            np.where(y < 0, y, 0.0),
        )

        return y_pos, y_neg


    def _plot_time_stacked_bars(self, context: dict) -> dict:
        db = context["db"]
        tickers = context["tickers"]
        labels = context["labels"]
        colors = context["colors"]
        bar_width = context["bar_width"]
        alpha = context["alpha"]
        get_plot_axis = context["get_plot_axis"]

        bars_data = {}
        stack_axis = get_plot_axis(tickers[0])

        if self._x_axis_mode == "bbg":
            x_plot = self._x_vals
            bottom_pos = np.zeros(len(self._x_vals), dtype=float)
            bottom_neg = np.zeros(len(self._x_vals), dtype=float)

            for i, t in enumerate(tickers):
                serie = db[[t]].copy().reindex(self._x_axis_fechas)[t]
                y_pos, y_neg = self._split_positive_negative(serie.values)

                bars_pos = None
                bars_neg = None

                if np.any(y_pos != 0):
                    bars_pos = stack_axis.bar(
                        x_plot,
                        y_pos,
                        width=min(bar_width, 0.85),
                        bottom=bottom_pos,
                        color=colors[i],
                        alpha=alpha,
                        label=labels[i],
                        zorder=3,
                    )
                    bottom_pos = bottom_pos + y_pos

                if np.any(y_neg != 0):
                    bars_neg = stack_axis.bar(
                        x_plot,
                        y_neg,
                        width=min(bar_width, 0.85),
                        bottom=bottom_neg,
                        color=colors[i],
                        alpha=alpha,
                        zorder=3,
                    )
                    bottom_neg = bottom_neg + y_neg

                bars_data[t] = {
                    "bars": {
                        "pos": bars_pos,
                        "neg": bars_neg,
                    }
                }

            return bars_data

        x_plot = db.index
        bottom_pos = np.zeros(len(db.index), dtype=float)
        bottom_neg = np.zeros(len(db.index), dtype=float)

        for i, t in enumerate(tickers):
            y_pos, y_neg = self._split_positive_negative(db[t].values)

            bars_pos = None
            bars_neg = None

            if np.any(y_pos != 0):
                bars_pos = stack_axis.bar(
                    x_plot,
                    y_pos,
                    width=min(bar_width, 0.85),
                    bottom=bottom_pos,
                    color=colors[i],
                    alpha=alpha,
                    label=labels[i],
                    zorder=3,
                )
                bottom_pos = bottom_pos + y_pos

            if np.any(y_neg != 0):
                bars_neg = stack_axis.bar(
                    x_plot,
                    y_neg,
                    width=min(bar_width, 0.85),
                    bottom=bottom_neg,
                    color=colors[i],
                    alpha=alpha,
                    zorder=3,
                )
                bottom_neg = bottom_neg + y_neg

            bars_data[t] = {
                "bars": {
                    "pos": bars_pos,
                    "neg": bars_neg,
                }
            }

        return bars_data


    def _plot_last_bars(self, context: dict) -> dict:
        db = context["db"]
        state = context["state"]
        tickers = context["tickers"]
        labels = context["labels"]
        colors = context["colors"]
        grouped = context["grouped"]
        stacked = context["stacked"]
        bar_width = context["bar_width"]
        alpha = context["alpha"]
        left_ax = context["left_ax"]
        x_axis = context["x_axis"]
        get_plot_axis = context["get_plot_axis"]

        db = db[tickers].copy()
        context["db"] = db

        state.bars_x_reference = list(db.index)

        x = np.arange(len(db.index), dtype=float)
        cats = [str(v) for v in db.index]
        m = len(tickers)

        vals_matrix = np.column_stack([
            np.asarray(db[t].values, dtype=float)
            for t in tickers
        ])

        self._x_axis_mode = "categorical"
        self._x_axis_fechas = None
        self._x_vals = x

        bars_data = {}

        if grouped and not stacked:
            width = min(bar_width / max(m, 1), 0.8 / max(m, 1))

            for i, t in enumerate(tickers):
                plot_ax = get_plot_axis(t)
                offset = (i - (m - 1) / 2) * width
                y = vals_matrix[:, i]

                bars = plot_ax.bar(
                    x + offset,
                    y,
                    width=width,
                    color=colors[i],
                    alpha=alpha,
                    label=labels[i],
                    zorder=3,
                )

                bars_data[t] = {"bars": bars}

            return bars_data

        if stacked:
            stack_axis = get_plot_axis(tickers[0])
            bottom_pos = np.zeros(len(x), dtype=float)
            bottom_neg = np.zeros(len(x), dtype=float)

            for i, t in enumerate(tickers):
                y_pos, y_neg = self._split_positive_negative(vals_matrix[:, i])

                bars_pos = None
                bars_neg = None

                if np.any(y_pos != 0):
                    bars_pos = stack_axis.bar(
                        x,
                        y_pos,
                        width=min(bar_width, 0.85),
                        bottom=bottom_pos,
                        color=colors[i],
                        alpha=alpha,
                        label=labels[i],
                        zorder=3,
                    )
                    bottom_pos = bottom_pos + y_pos

                if np.any(y_neg != 0):
                    bars_neg = stack_axis.bar(
                        x,
                        y_neg,
                        width=min(bar_width, 0.85),
                        bottom=bottom_neg,
                        color=colors[i],
                        alpha=alpha,
                        zorder=3,
                    )
                    bottom_neg = bottom_neg + y_neg

                bars_data[t] = {
                    "bars": {
                        "pos": bars_pos,
                        "neg": bars_neg,
                    }
                }

            return bars_data

        t = tickers[0]
        plot_ax = get_plot_axis(t)
        y = vals_matrix[:, 0]

        bars = plot_ax.bar(
            x,
            y,
            width=min(bar_width, 0.85),
            color=colors[0],
            alpha=alpha,
            label=labels[0],
            zorder=3,
        )

        bars_data[t] = {"bars": bars}

        left_ax.set_xticks(x)
        x_font = x_axis.get("fontsize", 8)
        left_ax.set_xticklabels(cats, fontsize=x_font)

        return bars_data


    def _finalize_bar_metadata(self, context: dict, bars_data: dict):
        state = context["state"]

        state.bars_data = bars_data
        state.bar_stacked = context["stacked"]
        state.bar_grouped = context["grouped"]

        return context


    def _finalize_bar_axes(self, context: dict):
        left_ax = context["left_ax"]
        right_ax = context["right_ax"]
        y_axis = context["y_axis"]
        y_axis["side"] = "left"
        y_axis_right = context["y_axis_right"]
        y_axis_right["side"] = "right"
        right_axis = context["right_axis"]
        hlines = context["hlines"]
        show_hguide = context["show_hguide"]

        self.config_yaxis(
            **y_axis,
        )

        if right_ax is not None:
            right_y_axis = right_axis.copy()
            right_y_axis.update(y_axis_right)

            self.config_yaxis(
                **right_y_axis,
            )

        self._ax = left_ax

        if hlines:
            self.horizontal_lines(
                side="left",
                **hlines,
            )

        if show_hguide:
            self.horizontal_guides(
                side="both" if right_ax is not None else "left",
                mostrar_cero=False,
            )

        return context


    def _finalize_bar_legend(self, context: dict):
        left_ax = context["left_ax"]
        right_ax = context["right_ax"]
        legend = context["legend"]

        self.add_combined_legend(
            ax=left_ax,
            include_right_axis=right_ax is not None,
            **legend,
        )

        self._ax = left_ax

        return context


    def _apply_bar_labels(self, context: dict):
        bar_labels = context["bar_labels"]
        axis_map = context["axis_map"]
        left_ax = context["left_ax"]
        right_ax = context["right_ax"]

        if not bar_labels:
            return context

        bar_labels_left = {}
        bar_labels_right = {}

        for control_name, control in bar_labels.items():
            ticker = control.get("ticker")

            if ticker is None:
                bar_labels_left[control_name] = control
                continue

            if axis_map.get(ticker, "left") == "right":
                bar_labels_right[control_name] = control
            else:
                bar_labels_left[control_name] = control

        if bar_labels_left:
            self._ax = left_ax
            self._bar_value_label_generate_dict(
                label_dict=bar_labels_left,
            )

        if bar_labels_right:
            if right_ax is None:
                raise RuntimeError(
                    "Right axis was not initialized for right-side bar labels."
                )

            self._ax = right_ax
            self._bar_value_label_generate_dict(
                label_dict=bar_labels_right,
            )

        self._ax = left_ax

        return context


    def graph_bar(
        self,
        figsize: tuple[float, float] = (6.00, 5.00),
        title: dict | FigureTitle | None = None,
        subtitle: dict | FigureSubtitle | None = None,
        source: dict | FigureSource | None = None,
        df_index: int = 0,
        tickers: list[str] | str = "all",
        labels: list[str] | str | dict[str, str] | None = None,
        colors: list[str] | str | dict[str, str] = PALETA_COLORES,
        x_axis: dict | XAxisConfig | None = None,
        y_axis: dict | YAxisConfig | None = None,
        axis_side: str | list[str] | dict[str, str] | None = None,
        y_axis_right: dict | YAxisConfig | None = None,
        right_axis: dict | None = None,
        bar_mode: Literal["auto", "time", "last"] = "auto",
        stacked: bool = False,
        grouped: bool = False,
        bar_width: float = 0.8,
        alpha: float = 0.95,
        bar_labels: dict | None = None,
        legend: dict | LegendConfig | None = None,
        hlines: dict | None = None,
        show_hguide: bool = False,
    ) -> Self:
        context = self._prepare_bar_context(
            df_index=df_index,
            tickers=tickers,
            labels=labels,
            colors=colors,
            axis_side=axis_side,
            stacked=stacked,
            grouped=grouped,
            bar_mode=bar_mode,
            x_axis=x_axis,
            y_axis=y_axis,
            y_axis_right=y_axis_right,
            right_axis=right_axis,
            title=title,
            subtitle=subtitle,
            source=source,
            legend=legend,
            hlines=hlines,
            bar_labels=bar_labels,
        )

        context["bar_width"] = bar_width
        context["alpha"] = alpha
        context["show_hguide"] = show_hguide

        context = self._ensure_bar_figure(
            context=context,
            figsize=figsize,
        )

        self._apply_bar_layout(context)

        if context["bar_mode"] == "time":
            bars_data = self._plot_time_bars(context)
        elif context["bar_mode"] == "last":
            bars_data = self._plot_last_bars(context)
        else:
            raise ValueError("bar_mode must be one of: 'auto', 'time', 'last'")

        self._finalize_bar_metadata(context, bars_data)
        self._finalize_bar_axes(context)
        self._finalize_bar_legend(context)
        self._apply_bar_labels(context)

        return self
