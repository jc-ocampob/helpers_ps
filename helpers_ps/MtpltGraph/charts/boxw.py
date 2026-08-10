from __future__ import annotations

from typing import Self

import numpy as np
import pandas as pd

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


class BoxWChartMixin:
    """
    Provides box-and-whisker chart construction logic for GraphMtplt.

    This mixin follows the same architecture used by the other chart mixins:
    prepare context, ensure figure, draw chart, store metadata, apply labels,
    configure axes, and finalize legend.
    """

    # ---------------------------------------------------------------------
    # Context preparation
    # ---------------------------------------------------------------------
    def _prepare_box_context(
        self,
        *,
        df_index: int,
        tickers,
        labels,
        colors,
        title,
        subtitle,
        source,
        titles,
        legend,
        x_axis,
        y_axis,
        box_config,
        box_style,
        median_style,
        whisker_style,
        cap_style,
        flier_style,
        mean_style,
        range_tag_high,
        range_tag_low,
        mean_tag,
        tag_dot,
        hlines,
        box_face_alpha: float,
    ) -> dict:
        db_original = self._select_df(df_idx=df_index)

        series_config = self._normalize_series_config(
            dataframe=db_original,
            tickers=tickers,
            labels=labels,
            colors=colors,
            axis_side=None,
        )

        tickers = [item["ticker"] for item in series_config]
        labels = [item["label"] for item in series_config]
        colors = [item["color"] for item in series_config]

        db = db_original[tickers].copy()

        # Important:
        # For boxplots, the active dataframe should be the selected columns only.
        # BoxWTags depends on self._df and self._ticker_label_color.
        state = self._ensure_active_state()
        state.dataframe_idx = df_index
        state.dataframe = db
        state.series_config = series_config
        state.axis_map = {item["ticker"]: "left" for item in series_config}
        state.ticker_label_color = [
            (item["ticker"], item["label"], item["color"])
            for item in series_config
        ]

        # Backward-compatible metadata access through GraphMetaData.
        self._df = db
        self._ticker_label_color = state.ticker_label_color

        # Legacy support:
        # If older code passes titles={...}, use it as title unless the new
        # title/subtitle arguments were explicitly provided.
        if titles is not None:
            if title is None:
                if isinstance(titles, dict) and "title" in titles:
                    title = titles.get("title")
                else:
                    title = titles

            if subtitle is None and isinstance(titles, dict) and "subtitle" in titles:
                subtitle = titles.get("subtitle")

        configs = coerce_configs(
            x_axis=(x_axis, XAxisConfig),
            y_axis=(y_axis, YAxisConfig),
            title=(title, FigureTitle),
            subtitle=(subtitle, FigureSubtitle),
            source=(source, FigureSource),
            legend=(legend, LegendConfig),
        )

        x_axis = config_to_dict(configs["x_axis"])
        y_axis = config_to_dict(configs["y_axis"])
        title = config_to_dict(configs["title"])
        subtitle = config_to_dict(configs["subtitle"])
        source = config_to_dict(configs["source"])
        legend = config_to_dict(configs["legend"])

        return {
            "db": db,
            "state": state,
            "series_config": series_config,
            "tickers": tickers,
            "labels": labels,
            "colors": colors,
            "title": title,
            "subtitle": subtitle,
            "source": source,
            "legend": legend,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "box_config": box_config,
            "box_style": box_style,
            "median_style": median_style,
            "whisker_style": whisker_style,
            "cap_style": cap_style,
            "flier_style": flier_style,
            "mean_style": mean_style,
            "range_tag_high": range_tag_high,
            "range_tag_low": range_tag_low,
            "mean_tag": mean_tag,
            "tag_dot": tag_dot,
            "hlines": hlines if hlines is not None else {},
            "box_face_alpha": box_face_alpha,
        }

    # ---------------------------------------------------------------------
    # Figure and layout
    # ---------------------------------------------------------------------
    def _ensure_box_figure(
        self,
        context: dict,
        figsize: tuple[float, float],
    ) -> dict:
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        return context

    def _apply_box_layout(self, context: dict) -> dict:
        self.add_title(**context["title"])
        self.add_subtitle(**context["subtitle"])
        self.add_source(**context["source"])
        return context

    # ---------------------------------------------------------------------
    # Defaults and style resolution
    # ---------------------------------------------------------------------
    def _default_box_config(self) -> dict:
        return {
            "whis": (0, 100),
            "showfliers": False,
            "showmeans": False,
            "meanline": False,
            "widths": 0.6,
            "notch": False,
            "vert": True,
        }

    def _default_box_style(self) -> dict:
        return {
            "color": "#6E6E6E",
            "lw": 0.5,
        }

    def _default_median_style(self) -> dict:
        return {
            "color": "#222222",
            "lw": 1.5,
        }

    def _default_whisker_style(self) -> dict:
        return {
            "color": "#6E6E6E",
            "lw": 0.5,
        }

    def _default_cap_style(self) -> dict:
        return {
            "color": "#6E6E6E",
            "lw": 0.5,
        }

    def _default_flier_style(self) -> dict:
        return {
            "marker": "o",
            "markersize": 3.5,
            "markerfacecolor": "#999999",
            "markeredgecolor": "#999999",
            "alpha": 0.85,
        }

    def _default_mean_style(self) -> dict:
        return {
            "color": "#404040",
            "lw": 0.5,
            "linestyle": "--",
        }

    def _merge_style(
        self,
        default: dict,
        override: dict | None,
    ) -> dict:
        output = default.copy()
        if override is not None:
            output.update(override)
        return output

    def _resolve_box_styles(self, context: dict) -> dict:
        context["box_config"] = self._merge_style(
            self._default_box_config(),
            context["box_config"],
        )
        context["box_style"] = self._merge_style(
            self._default_box_style(),
            context["box_style"],
        )
        context["median_style"] = self._merge_style(
            self._default_median_style(),
            context["median_style"],
        )
        context["whisker_style"] = self._merge_style(
            self._default_whisker_style(),
            context["whisker_style"],
        )
        context["cap_style"] = self._merge_style(
            self._default_cap_style(),
            context["cap_style"],
        )
        context["flier_style"] = self._merge_style(
            self._default_flier_style(),
            context["flier_style"],
        )
        context["mean_style"] = self._merge_style(
            self._default_mean_style(),
            context["mean_style"],
        )

        return context

    # ---------------------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------------------
    def _build_boxplot_data(self, context: dict) -> dict:
        db = context["db"]
        tickers = context["tickers"]

        context["data_plot"] = [
            db[ticker].dropna().values
            for ticker in tickers
        ]

        return context

    def _draw_boxplot(self, context: dict) -> dict:
        box_config = context["box_config"]

        bp = self._ax.boxplot(
            context["data_plot"],
            labels=context["labels"],
            patch_artist=True,
            boxprops=context["box_style"],
            medianprops=context["median_style"],
            whiskerprops=context["whisker_style"],
            capprops=context["cap_style"],
            flierprops=context["flier_style"],
            meanprops=context["mean_style"],
            **box_config,
        )

        context["boxplot_result"] = bp
        context["vert"] = box_config.get("vert", True)

        return context

    def _apply_box_colors(self, context: dict) -> dict:
        bp = context["boxplot_result"]
        colors = context["colors"]
        box_face_alpha = context["box_face_alpha"]

        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(colors[i])
            patch.set_alpha(box_face_alpha)

        return context

    # ---------------------------------------------------------------------
    # X-axis metadata and formatting
    # ---------------------------------------------------------------------
    def _resolve_box_x_labels(self, context: dict) -> list[str]:
        labels = [str(label) for label in context["labels"]]
        x_axis = context["x_axis"]

        tick_labels = x_axis.get("tick_labels")
        tick_label_map = x_axis.get("tick_label_map") or {}

        if tick_labels is not None:
            tick_labels = list(tick_labels)
            if len(tick_labels) < len(labels):
                tick_labels = tick_labels + labels[len(tick_labels):]
            return tick_labels[:len(labels)]

        return [
            tick_label_map.get(label, label)
            for label in labels
        ]

    def _apply_box_xaxis(self, context: dict) -> dict:
        x_axis = context["x_axis"]
        labels = self._resolve_box_x_labels(context)
        tick_positions = np.arange(1, len(labels) + 1)

        fontsize = x_axis.get("fontsize", 8)
        rotation = x_axis.get("rotation", 0)
        ha = x_axis.get("ha", "center")
        va = x_axis.get("va", "center")
        label_color = x_axis.get("label_color")

        # Boxplot categories live on the x-axis for the supported/default mode.
        self._ax.set_xticks(tick_positions)
        self._ax.set_xticklabels(
            labels,
            fontsize=fontsize,
            rotation=rotation,
            ha=ha,
            va=va,
        )

        if label_color is not None:
            for label in self._ax.get_xticklabels():
                label.set_color(label_color)

        self._x_axis_mode = "categorical"
        self._x_axis_fechas = None
        self._x_vals = tick_positions.astype(float)
        self._x_axis_metadata = {
            "mode": "categorical",
            "chart_type": "box_whiskers",
            "tickers": context["tickers"],
            "labels": labels,
            "x_vals": self._x_vals,
            "tick_labels": x_axis.get("tick_labels"),
            "tick_label_map": x_axis.get("tick_label_map"),
            "fontsize": fontsize,
            "rotation": rotation,
            "ha": ha,
            "va": va,
            "label_color": label_color,
        }

        return context

    # ---------------------------------------------------------------------
    # Statistic tags
    # ---------------------------------------------------------------------
    def _default_box_stat_tag(self) -> dict:
        return {
            "label_h_align": "center",
            "label_v_align": "center",
            "ubic_etq": (0, 10),
            "fontsize": 8,
            "fontweight": "bold",
            "font_color": "black",
            "bg_color": "None",
            "bg_alpha": 1.0,
            "edge_color": "None",
            "show_bbox": True,
            "zorder": 20,
            "fmt": ",.1f",
            "show": True,
        }

    def _resolve_box_stat_tag(
        self,
        config: dict | None,
        *,
        default_offset: tuple[float, float],
    ) -> tuple[dict, bool, str]:

        tag_config = self._default_box_stat_tag()

        if config is not None:
            tag_config.update(config)

        show = tag_config.pop("show", False)
        fmt = tag_config.pop("fmt", ",.2f")

        if tag_config.get("ubic_etq") == (0, 10):
            tag_config["ubic_etq"] = default_offset

        return tag_config, show, fmt

    def _apply_box_stat_tags(
        self,
        context: dict,
    ) -> dict:

        range_tag_high, range_high_show, range_high_fmt = (
            self._resolve_box_stat_tag(
                context["range_tag_high"],
                default_offset=(0, 10),
            )
        )

        range_tag_low, range_low_show, range_low_fmt = (
            self._resolve_box_stat_tag(
                context["range_tag_low"],
                default_offset=(0, -10),
            )
        )

        mean_tag, mean_show, mean_fmt = (
            self._resolve_box_stat_tag(
                context["mean_tag"],
                default_offset=(0, 0),
            )
        )

        if not (
            range_high_show
            or range_low_show
            or mean_show
        ):
            return context

        bp = context["boxplot_result"]
        db = context["db"]
        tickers = context["tickers"]
        vert = context["vert"]

        for i, ticker in enumerate(tickers):

            low_whisker = bp["whiskers"][2 * i]
            high_whisker = bp["whiskers"][2 * i + 1]

            series = db[ticker].dropna()

            if series.empty:
                continue

            mean_value = float(series.mean())

            if vert:

                x_low = float(
                    np.mean(
                        low_whisker.get_xdata()
                    )
                )

                y_low = float(
                    np.min(
                        low_whisker.get_ydata()
                    )
                )

                x_high = float(
                    np.mean(
                        high_whisker.get_xdata()
                    )
                )

                y_high = float(
                    np.max(
                        high_whisker.get_ydata()
                    )
                )

                x_mean = i + 1
                y_mean = mean_value

                low_label_value = y_low
                high_label_value = y_high

            else:

                y_low = float(
                    np.mean(
                        low_whisker.get_ydata()
                    )
                )

                x_low = float(
                    np.min(
                        low_whisker.get_xdata()
                    )
                )

                y_high = float(
                    np.mean(
                        high_whisker.get_ydata()
                    )
                )

                x_high = float(
                    np.max(
                        high_whisker.get_xdata()
                    )
                )

                x_mean = mean_value
                y_mean = i + 1

                low_label_value = x_low
                high_label_value = x_high

            if range_low_show:

                self.tag(
                    x_value=x_low,
                    y_value=y_low,
                    label=f"{low_label_value:{range_low_fmt}}",
                    **range_tag_low,
                )

            if range_high_show:

                self.tag(
                    x_value=x_high,
                    y_value=y_high,
                    label=f"{high_label_value:{range_high_fmt}}",
                    **range_tag_high,
                )

            if mean_show:

                self.tag(
                    x_value=x_mean,
                    y_value=y_mean,
                    label=f"{mean_value:{mean_fmt}}",
                    **mean_tag,
                )

        return context

    # ---------------------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------------------
    def _store_box_metadata(
        self,
        context: dict,
    ) -> dict:

        state = context["state"]

        state.x_axis_mode = self._x_axis_mode
        state.x_axis_fechas = self._x_axis_fechas
        state.x_vals = self._x_vals
        state.x_axis_metadata = self._x_axis_metadata

        state.series_config = (
            context["series_config"]
        )

        state.axis_map = {
            ticker: "left"
            for ticker in context["tickers"]
        }

        state.ticker_label_color = [
            (
                context["tickers"][i],
                context["labels"][i],
                context["colors"][i],
            )
            for i in range(
                len(
                    context["tickers"]
                )
            )
        ]

        return context

    # ---------------------------------------------------------------------
    # Finalization
    # ---------------------------------------------------------------------
    def _apply_box_tag_dot(
        self,
        context: dict,
    ) -> dict:

        tag_dot = context["tag_dot"]

        if tag_dot:

            self._box_whiskers_label_generate(
                control_dict=tag_dot,
            )

        return context

    def _finalize_box_axes(
        self,
        context: dict,
        *,
        show_hguide: bool,
    ) -> dict:

        y_axis = context["y_axis"]
        hlines = context["hlines"]

        if hlines:

            self.horizontal_lines(
                **hlines
            )

        if show_hguide:

            self.horizontal_guides(
                mostrar_cero=False,
            )

        self.config_yaxis(
            **y_axis
        )

        return context

    def _finalize_box_legend(
        self,
        context: dict,
    ) -> dict:

        legend = context["legend"]

        self.add_legend(
            **legend
        )

        return context

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def graph_box_whiskers(
        self,
        figsize: tuple[float, float] = (6.00, 5.00),

        # -----------------------------------------------------------------
        # Data selection
        # -----------------------------------------------------------------
        df_index: int = 0,
        tickers: list[str] | str = "all",
        labels: list[str] | tuple[str, ...] | dict[str, str] | None = None,
        colors: list[str] | tuple[str, ...] | str | dict[str, str] | None = None,

        # -----------------------------------------------------------------
        # Layout
        # -----------------------------------------------------------------
        title=None,
        subtitle=None,
        source=None,
        titles=None,

        # -----------------------------------------------------------------
        # Axis config
        # -----------------------------------------------------------------
        x_axis=None,
        y_axis=None,

        # -----------------------------------------------------------------
        # Boxplot config
        # -----------------------------------------------------------------
        box_config: dict | None = None,
        box_style: dict | None = None,
        median_style: dict | None = None,
        whisker_style: dict | None = None,
        cap_style: dict | None = None,
        flier_style: dict | None = None,
        mean_style: dict | None = None,

        box_face_alpha: float = 0.50,

        # -----------------------------------------------------------------
        # Statistic labels
        # -----------------------------------------------------------------
        range_tag_high: dict | None = None,
        range_tag_low: dict | None = None,
        mean_tag: dict | None = None,

        # -----------------------------------------------------------------
        # Additional annotations
        # -----------------------------------------------------------------
        tag_dot: dict | None = None,

        # -----------------------------------------------------------------
        # Reference lines / guides
        # -----------------------------------------------------------------
        hlines: dict | None = None,
        show_hguide: bool = False,

        # -----------------------------------------------------------------
        # Legend
        # -----------------------------------------------------------------
        legend=None,

    ) -> Self:

        """
        Create a box-and-whisker chart.

        Parameters
        ----------
        df_index
            DataFrame index when multiple DataFrames were passed to the graph.

        tickers
            Columns to plot.

        labels
            Display labels for each box.

        colors
            Box colors.

        title, subtitle, source
            Figure-level metadata.

        x_axis, y_axis
            Axis configuration.

        tag_dot
            Controls passed to BoxWTags.

        Returns
        -------
        Self
        """

        # -------------------------------------------------------------
        # 1. Context
        # -------------------------------------------------------------
        context = self._prepare_box_context(
            df_index=df_index,
            tickers=tickers,
            labels=labels,
            colors=colors,
            title=title,
            subtitle=subtitle,
            source=source,
            titles=titles,
            legend=legend,
            x_axis=x_axis,
            y_axis=y_axis,
            box_config=box_config,
            box_style=box_style,
            median_style=median_style,
            whisker_style=whisker_style,
            cap_style=cap_style,
            flier_style=flier_style,
            mean_style=mean_style,
            range_tag_high=range_tag_high,
            range_tag_low=range_tag_low,
            mean_tag=mean_tag,
            tag_dot=tag_dot,
            hlines=hlines,
            box_face_alpha=box_face_alpha,
        )

        # -------------------------------------------------------------
        # 2. Figure
        # -------------------------------------------------------------
        context = self._ensure_box_figure(
            context=context,
            figsize=figsize,
        )

        # -------------------------------------------------------------
        # 3. Figure layout
        # -------------------------------------------------------------
        context = self._apply_box_layout(
            context=context,
        )

        # -------------------------------------------------------------
        # 4. Resolve styles
        # -------------------------------------------------------------
        context = self._resolve_box_styles(
            context=context,
        )

        # -------------------------------------------------------------
        # 5. Build plotting arrays
        # -------------------------------------------------------------
        context = self._build_boxplot_data(
            context=context,
        )

        # -------------------------------------------------------------
        # 6. Draw
        # -------------------------------------------------------------
        context = self._draw_boxplot(
            context=context,
        )

        # -------------------------------------------------------------
        # 7. Colors
        # -------------------------------------------------------------
        context = self._apply_box_colors(
            context=context,
        )

        # -------------------------------------------------------------
        # 8. X-axis metadata
        # -------------------------------------------------------------
        context = self._apply_box_xaxis(
            context=context,
        )

        # -------------------------------------------------------------
        # 9. Metadata
        # -------------------------------------------------------------
        context = self._store_box_metadata(
            context=context,
        )

        # -------------------------------------------------------------
        # 10. High / low / mean labels
        # -------------------------------------------------------------
        context = self._apply_box_stat_tags(
            context=context,
        )

        # -------------------------------------------------------------
        # 11. User tags
        # -------------------------------------------------------------
        context = self._apply_box_tag_dot(
            context=context,
        )

        # -------------------------------------------------------------
        # 12. Guides & axis formatting
        # -------------------------------------------------------------
        context = self._finalize_box_axes(
            context=context,
            show_hguide=show_hguide,
        )

        # -------------------------------------------------------------
        # 13. Legend
        # -------------------------------------------------------------
        context = self._finalize_box_legend(
            context=context,
        )

        return self