from __future__ import annotations

from typing import Self

import numpy as np
import pandas as pd
import matplotlib.patheffects as path_effects

from ..models import (
    LegendConfig,
    FigureTitle,
    FigureSubtitle,
    FigureSource,
    coerce_configs,
    config_to_dict
)
from ..tags._colors import PALETA_COLORES


class PieChartMixin:


    def _resolve_pie_value_column(
        self,
        dataframe: pd.DataFrame,
        tickers: list[str] | tuple[str, ...] | set[str] | str,
    ) -> str:
        if isinstance(tickers, str):
            if tickers == "all":
                if len(dataframe.columns) != 1:
                    raise ValueError(
                        "`graph_pie()` requires exactly one value column. "
                        "Pass `tickers='column_name'` or provide a one-column DataFrame."
                    )
                return dataframe.columns[0]

            return tickers

        if isinstance(tickers, (list, tuple, set)):
            tickers_list = list(tickers)

            if len(tickers_list) != 1:
                raise ValueError(
                    "`graph_pie()` only supports one value column. "
                    "Pass a single column name in `tickers`."
                )

            return tickers_list[0]

        raise TypeError(
            "`tickers` must be 'all', a string column name, or a one-item list."
        )


    def _build_pie_series(
        self,
        dataframe: pd.DataFrame,
        value_column: str,
        sort_values: bool,
    ) -> pd.Series:
        if value_column not in dataframe.columns:
            raise ValueError(f"Column not found in dataframe: {value_column}")

        serie = pd.to_numeric(
            dataframe[value_column],
            errors="coerce",
        )

        serie = serie.replace([np.inf, -np.inf], np.nan).dropna()

        if serie.empty:
            raise ValueError(
                f"The selected column `{value_column}` has no numeric values to plot."
            )

        if serie.index.has_duplicates:
            raise ValueError(
                "`graph_pie()` requires a unique DataFrame index because the index "
                "is used as pie categories and metadata keys."
            )

        if sort_values:
            serie = serie.sort_values(ascending=False)

        return serie


    def _resolve_pie_labels(
        self,
        categories: list,
        labels: list[str] | tuple[str, ...] | dict | None,
    ) -> list[str]:
        if labels is None:
            return [str(category) for category in categories]

        if isinstance(labels, dict):
            return [
                labels.get(
                    category,
                    labels.get(str(category), str(category)),
                )
                for category in categories
            ]

        if isinstance(labels, (list, tuple)):
            label_list = list(labels)

            if len(label_list) < len(categories):
                return label_list + [
                    str(category)
                    for category in categories[len(label_list):]
                ]

            return label_list[:len(categories)]

        raise TypeError(
            "`labels` must be None, a list, a tuple, or a dictionary keyed by index category."
        )


    def _resolve_pie_colors(
        self,
        categories: list,
        colors: list[str] | tuple[str, ...] | str | dict,
    ) -> list[str]:
        if isinstance(colors, str):
            return [
                colors
                for _ in categories
            ]

        if isinstance(colors, dict):
            return [
                colors.get(
                    category,
                    colors.get(
                        str(category),
                        PALETA_COLORES[i % len(PALETA_COLORES)],
                    ),
                )
                for i, category in enumerate(categories)
            ]

        if isinstance(colors, (list, tuple)):
            color_list = list(colors)

            return [
                color_list[i]
                if i < len(color_list)
                else PALETA_COLORES[i % len(PALETA_COLORES)]
                for i in range(len(categories))
            ]

        return [
            PALETA_COLORES[i % len(PALETA_COLORES)]
            for i in range(len(categories))
        ]


    def _prepare_pie_context(
        self,
        *,
        df_index: int,
        tickers,
        labels,
        colors,
        title,
        subtitle,
        source,
        legend,
        sort_values: bool,
        textprops,
        wedgeprops,
        donut_width,
    ):
        db = self._select_df(df_idx=df_index)
        state = self._ensure_active_state()

        if db is None or not isinstance(db, pd.DataFrame):
            raise TypeError("`dataframe` must be a pandas DataFrame.")

        if db.empty:
            raise ValueError("Cannot create a pie chart from an empty DataFrame.")

        value_column = self._resolve_pie_value_column(
            dataframe=db,
            tickers=tickers,
        )

        serie = self._build_pie_series(
            dataframe=db,
            value_column=value_column,
            sort_values=sort_values,
        )

        plot_categories = serie.index.tolist()
        plot_keys = [
            str(category)
            for category in plot_categories
        ]

        plot_labels = self._resolve_pie_labels(
            categories=plot_categories,
            labels=labels,
        )

        plot_colors = self._resolve_pie_colors(
            categories=plot_categories,
            colors=colors,
        )

        configs = coerce_configs(
            title=(title, FigureTitle),
            subtitle=(subtitle, FigureSubtitle),
            source=(source, FigureSource),
            legend=(legend, LegendConfig),
        )

        title = config_to_dict(configs["title"])
        subtitle = config_to_dict(configs["subtitle"])
        source = config_to_dict(configs["source"])
        legend = config_to_dict(configs["legend"])

        textprops = textprops if textprops is not None else {}
        wedgeprops = wedgeprops if wedgeprops is not None else {}

        if donut_width is not None:
            wedgeprops["width"] = donut_width

        return {
            "db": db,
            "state": state,
            "value_column": value_column,
            "serie": serie,
            "plot_categories": plot_categories,
            "plot_keys": plot_keys,
            "plot_labels": plot_labels,
            "plot_colors": plot_colors,
            "title": title,
            "subtitle": subtitle,
            "source": source,
            "legend": legend,
            "textprops": textprops,
            "wedgeprops": wedgeprops,
        }


    def _store_pie_axis_metadata(self, context: dict) -> dict:
        state = context["state"]
        value_column = context["value_column"]
        plot_keys = context["plot_keys"]
        plot_labels = context["plot_labels"]
        plot_colors = context["plot_colors"]
        plot_categories = context["plot_categories"]

        state.series_config = [
            {
                "ticker": value_column,
                "label": str(value_column),
                "color": plot_colors[0] if plot_colors else None,
                "axis_side": "left",
            }
        ]

        state.axis_map = {
            value_column: "left",
        }

        state.ticker_label_color = [
            (plot_keys[i], plot_labels[i], plot_colors[i])
            for i in range(len(plot_keys))
        ]

        state.x_axis_mode = "categorical"
        state.x_axis_fechas = None
        state.x_vals = np.arange(len(plot_categories), dtype=float)

        state.x_axis_metadata = {
            "mode": "categorical",
            "chart_type": "pie",
            "value_column": value_column,
            "categories": plot_categories,
            "labels": plot_labels,
        }

        return context


    def _ensure_pie_figure(
        self,
        context: dict,
        figsize: tuple[float, float],
    ) -> dict:
        if not hasattr(self, "_ax") or self._ax is None:
            self.plot(figsize=figsize)

        self._ax.clear()

        return context


    def _apply_pie_layout(self, context: dict) -> dict:
        self.add_title(**context["title"])
        self.add_subtitle(**context["subtitle"])
        self.add_source(**context["source"])

        return context


    def _draw_pie(
        self,
        context: dict,
        *,
        startangle: float,
        counterclock: bool,
        autopct: str | None,
        pctdistance: float,
        labeldistance: float,
        normalize: bool,
    ):
        pie_out = self._ax.pie(
            context["serie"].values,
            labels=context["plot_labels"],
            colors=context["plot_colors"],
            startangle=startangle,
            counterclock=counterclock,
            autopct=autopct,
            pctdistance=pctdistance,
            labeldistance=labeldistance,
            textprops=context["textprops"],
            wedgeprops=context["wedgeprops"],
            normalize=normalize,
        )

        context["pie_out"] = pie_out

        return context


    def _store_pie_data(self, context: dict) -> dict:
        state = context["state"]
        serie = context["serie"]
        plot_keys = context["plot_keys"]
        plot_categories = context["plot_categories"]
        plot_labels = context["plot_labels"]
        plot_colors = context["plot_colors"]
        value_column = context["value_column"]
        pie_out = context["pie_out"]

        total = serie.sum()

        state.pie_data = {
            plot_keys[i]: {
                "category": plot_categories[i],
                "label": plot_labels[i],
                "color": plot_colors[i],
                "column": value_column,
                "wedge": pie_out[0][i],
                "value": serie.iloc[i],
                "pct": (serie.iloc[i] / total * 100.0) if total else 0.0,
            }
            for i in range(len(plot_keys))
        }

        return context


    def _style_pie_texts(
        self,
        context: dict,
        *,
        label_color: str,
        autopct_color: str,
        text_edge_color: str | None,
        text_edge_width: float,
    ) -> dict:
        pie_out = context["pie_out"]

        if len(pie_out) > 1:
            for txt in pie_out[1]:
                txt.set_color(label_color)

        if len(pie_out) > 2:
            for txt in pie_out[2]:
                txt.set_color(autopct_color)
                txt.set_fontweight("bold")

        self._ax.axis("equal")

        if text_edge_color is not None and text_edge_width and text_edge_width > 0:
            path_effect = [
                path_effects.withStroke(
                    linewidth=text_edge_width,
                    foreground=text_edge_color,
                )
            ]

            if len(pie_out) > 1:
                for txt in pie_out[1]:
                    txt.set_path_effects(path_effect)

            if len(pie_out) > 2:
                for txt in pie_out[2]:
                    txt.set_path_effects(path_effect)

        return context


    def _finalize_pie_legend(self, context: dict) -> dict:
        legend = context["legend"]
        pie_out = context["pie_out"]
        plot_labels = context["plot_labels"]

        if legend.get("show", False):
            legend_config = legend.copy()
            legend_config.pop("show", None)

            legend_config.setdefault("loc", "center left")
            legend_config.setdefault("bbox_to_anchor", (1.02, 0.5))

            self._ax.legend(
                pie_out[0],
                plot_labels,
                **legend_config,
            )

        return context


    def _finalize_pie_layout(self, context: dict) -> dict:
        self._fig.subplots_adjust(
            left=0.08,
            right=0.88,
            top=0.80,
            bottom=0.18,
        )

        return context


    def graph_pie(
        self,
        figsize: tuple[float, float] = (6.00, 5.00),
        title: dict | FigureTitle | None = None,
        subtitle: dict | FigureSubtitle | None = None,
        source: dict | FigureSource | None = None,
        df_index: int = 0,
        tickers: list[str] | str = "all",
        labels: list[str] | tuple[str, ...] | dict | None = None,
        colors: list[str] | tuple[str, ...] | str | dict = PALETA_COLORES,
        donut_width: float | None = None,
        startangle: float = 90,
        counterclock: bool = False,
        autopct: str | None = "%1.1f%%",
        pctdistance: float = 0.72,
        labeldistance: float = 1.05,
        textprops: dict | None = None,
        wedgeprops: dict | None = None,
        legend: dict | LegendConfig | None = None,
        sort_values: bool = False,
        normalize: bool = True,
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
        label_color: str = "black",
        autopct_color: str = "white",
    ) -> Self:
        context = self._prepare_pie_context(
            df_index=df_index,
            tickers=tickers,
            labels=labels,
            colors=colors,
            title=title,
            subtitle=subtitle,
            source=source,
            legend=legend,
            sort_values=sort_values,
            textprops=textprops,
            wedgeprops=wedgeprops,
            donut_width=donut_width,
        )

        self._store_pie_axis_metadata(context)

        self._ensure_pie_figure(
            context=context,
            figsize=figsize,
        )

        self._apply_pie_layout(context)

        self._draw_pie(
            context,
            startangle=startangle,
            counterclock=counterclock,
            autopct=autopct,
            pctdistance=pctdistance,
            labeldistance=labeldistance,
            normalize=normalize,
        )

        self._store_pie_data(context)

        self._style_pie_texts(
            context,
            label_color=label_color,
            autopct_color=autopct_color,
            text_edge_color=text_edge_color,
            text_edge_width=text_edge_width,
        )

        self._finalize_pie_legend(context)
        self._finalize_pie_layout(context)

        return self