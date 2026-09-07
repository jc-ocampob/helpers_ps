from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self

import matplotlib.patheffects as path_effects
import numpy as np
import pandas as pd

from ..tags._colors import PALETA_COLORES


class PieChartMixin:
    """
    Provides pie-chart construction logic for GraphMtplt.
    """

    def _resolve_pie_value_column(
        self,
        dataframe: pd.DataFrame,
        ticker: str | None,
    ) -> str:
        """
        Resolve and validate the DataFrame column used by the pie chart.

        If ticker is None, the DataFrame must contain exactly one
        column.
        """
        if ticker is None:
            if len(dataframe.columns) != 1:
                raise ValueError(
                    "When 'ticker' is None, graph_pie() requires "
                    "a DataFrame containing exactly one column."
                )

            return str(dataframe.columns[0])

        if not isinstance(ticker, str):
            raise TypeError(
                "'ticker' must be a string or None."
            )

        if not ticker.strip():
            raise ValueError(
                "'ticker' cannot be empty."
            )

        if ticker not in dataframe.columns:
            raise KeyError(
                f"Ticker '{ticker}' was not found in the "
                "selected DataFrame."
            )

        return ticker

    def _build_pie_series(
        self,
        dataframe: pd.DataFrame,
        value_column: str,
        sort_values: bool,
    ) -> pd.Series:
        """
        Build and validate the numeric series plotted by the pie chart.
        """
        series = pd.to_numeric(
            dataframe[value_column],
            errors="coerce",
        )

        series = (
            series
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .dropna()
        )

        if series.empty:
            raise ValueError(
                f"Ticker '{value_column}' contains no "
                "numeric values to plot."
            )

        if series.index.has_duplicates:
            raise ValueError(
                "graph_pie() requires a unique DataFrame index "
                "because index values identify pie categories."
            )

        if (series < 0).any():
            negative_categories = [
                str(category)
                for category in series.index[
                    series < 0
                ]
            ]

            raise ValueError(
                "Pie-chart values cannot be negative. "
                "Negative values were found for: "
                f"{negative_categories}."
            )

        if not np.any(series.to_numpy(dtype=float) > 0):
            raise ValueError(
                "graph_pie() requires at least one value "
                "greater than zero."
            )

        if sort_values:
            series = series.sort_values(
                ascending=False
            )

        return series

    def _resolve_pie_labels(
        self,
        categories: Sequence,
        labels: Sequence[str] | dict[Any, str] | None,
    ) -> list[str]:
        """
        Resolve display labels for pie categories.
        """
        if labels is None:
            return [
                str(category)
                for category in categories
            ]

        if isinstance(labels, dict):
            return [
                str(
                    labels.get(
                        category,
                        labels.get(
                            str(category),
                            category,
                        ),
                    )
                )
                for category in categories
            ]

        if isinstance(labels, (list, tuple)):
            resolved_labels = list(labels)

            if len(resolved_labels) != len(categories):
                raise ValueError(
                    "'labels' must have the same length as "
                    "the number of plotted categories."
                )

            if not all(
                isinstance(label, str)
                for label in resolved_labels
            ):
                raise TypeError(
                    "Every item in 'labels' must be a string."
                )

            return resolved_labels

        raise TypeError(
            "'labels' must be a list, tuple, dictionary, "
            "or None."
        )

    def _resolve_pie_colors(
        self,
        categories: Sequence,
        colors: (
            Sequence[str]
            | dict[Any, str]
            | str
            | None
        ),
    ) -> list[str]:
        """
        Resolve colors for pie categories.
        """
        if not PALETA_COLORES:
            raise ValueError(
                "PALETA_COLORES cannot be empty."
            )

        if colors is None:
            return [
                PALETA_COLORES[
                    position % len(PALETA_COLORES)
                ]
                for position in range(len(categories))
            ]

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
                        PALETA_COLORES[
                            position
                            % len(PALETA_COLORES)
                        ],
                    ),
                )
                for position, category
                in enumerate(categories)
            ]

        if isinstance(colors, (list, tuple)):
            resolved_colors = list(colors)

            if not resolved_colors:
                raise ValueError(
                    "'colors' cannot be an empty sequence."
                )

            if not all(
                isinstance(color, str)
                for color in resolved_colors
            ):
                raise TypeError(
                    "Every item in 'colors' must be a string."
                )

            return [
                resolved_colors[
                    position % len(resolved_colors)
                ]
                for position in range(len(categories))
            ]

        raise TypeError(
            "'colors' must be a string, list, tuple, "
            "dictionary, or None."
        )

    def _resolve_pie_explode(
        self,
        categories: Sequence,
        explode: (
            Sequence[float]
            | dict[Any, float]
            | float
            | None
        ),
    ) -> list[float] | None:
        """
        Resolve explode values for pie categories.
        """
        if explode is None:
            return None

        if isinstance(explode, (int, float)):
            if explode < 0:
                raise ValueError(
                    "'explode' cannot contain negative values."
                )

            return [
                float(explode)
                for _ in categories
            ]

        if isinstance(explode, dict):
            resolved_explode = [
                float(
                    explode.get(
                        category,
                        explode.get(
                            str(category),
                            0.0,
                        ),
                    )
                )
                for category in categories
            ]

        elif isinstance(explode, (list, tuple)):
            resolved_explode = [
                float(value)
                for value in explode
            ]

            if len(resolved_explode) != len(categories):
                raise ValueError(
                    "'explode' must have the same length as "
                    "the number of plotted categories."
                )

        else:
            raise TypeError(
                "'explode' must be numeric, a list, tuple, "
                "dictionary, or None."
            )

        if any(
            value < 0
            for value in resolved_explode
        ):
            raise ValueError(
                "'explode' cannot contain negative values."
            )

        return resolved_explode

    def _build_pie_wedgeprops(
        self,
        wedgeprops: dict[str, Any] | None,
        donut_width: float | None,
    ) -> dict[str, Any]:
        """
        Build wedge properties, including optional donut width.
        """
        resolved_wedgeprops = dict(
            wedgeprops or {}
        )

        if donut_width is None:
            return resolved_wedgeprops

        if not isinstance(
            donut_width,
            (int, float),
        ):
            raise TypeError(
                "'donut_width' must be numeric or None."
            )

        if not 0 < donut_width <= 1:
            raise ValueError(
                "'donut_width' must be greater than zero "
                "and less than or equal to one."
            )

        resolved_wedgeprops["width"] = float(
            donut_width
        )

        return resolved_wedgeprops

    def _style_pie_texts(
        self,
        *,
        label_texts,
        percentage_texts,
        label_color: str,
        autopct_color: str,
        autopct_fontweight: str | int,
        text_edge_color: str | None,
        text_edge_width: float,
    ) -> None:
        """
        Apply pie-specific text formatting.
        """
        for text in label_texts:
            text.set_color(label_color)

        for text in percentage_texts:
            text.set_color(autopct_color)
            text.set_fontweight(
                autopct_fontweight
            )

        if (
            text_edge_color is None
            or text_edge_width <= 0
        ):
            return

        effects = [
            path_effects.withStroke(
                linewidth=text_edge_width,
                foreground=text_edge_color,
            )
        ]

        for text in label_texts:
            text.set_path_effects(effects)

        for text in percentage_texts:
            text.set_path_effects(effects)

    def _store_pie_metadata(
        self,
        *,
        value_column: str,
        series: pd.Series,
        categories: list,
        labels: list[str],
        colors: list[str],
        wedges,
        label_texts,
        percentage_texts,
    ) -> None:
        """
        Store pie-chart metadata in the active chart state.
        """
        state = self._ensure_active_state()

        category_keys = [
            str(category)
            for category in categories
        ]

        total = float(series.sum())

        state.series_config = [
            {
                "ticker": value_column,
                "label": value_column,
                "color": (
                    colors[0]
                    if colors
                    else None
                ),
                "axis_side": "left",
            }
        ]

        state.axis_map = {
            value_column: "left",
        }

        state.ticker_label_color = [
            (
                category_keys[position],
                labels[position],
                colors[position],
            )
            for position in range(
                len(category_keys)
            )
        ]

        state.x_axis_mode = "categorical"
        state.x_axis_fechas = None

        state.x_vals = np.arange(
            len(categories),
            dtype=float,
        )

        state.x_axis_metadata = {
            "mode": "categorical",
            "chart_type": "pie",
            "value_column": value_column,
            "categories": categories,
            "labels": labels,
        }

        state.pie_data = {
            category_keys[position]: {
                "category": categories[position],
                "label": labels[position],
                "color": colors[position],
                "column": value_column,
                "wedge": wedges[position],
                "label_text": label_texts[position],
                "percentage_text": (
                    percentage_texts[position]
                    if position
                    < len(percentage_texts)
                    else None
                ),
                "value": float(
                    series.iloc[position]
                ),
                "pct": (
                    float(
                        series.iloc[position]
                        / total
                        * 100
                    )
                    if total
                    else 0.0
                ),
            }
            for position in range(
                len(category_keys)
            )
        }

        self._x_axis_mode = "categorical"
        self._x_axis_fechas = None

        self._x_vals = np.arange(
            len(categories),
            dtype=float,
        )

        self._x_axis_metadata = {
            "mode": "categorical",
            "chart_type": "pie",
            "value_column": value_column,
            "categories": categories,
            "labels": labels,
        }

    def graph_pie(
        self,
        ticker: str | None = None,
        df_index: int = 0,
        labels: (
            Sequence[str]
            | dict[Any, str]
            | None
        ) = None,
        colors: (
            Sequence[str]
            | dict[Any, str]
            | str
            | None
        ) = None,
        explode: (
            Sequence[float]
            | dict[Any, float]
            | float
            | None
        ) = None,
        donut_width: float | None = None,
        startangle: float = 90,
        counterclock: bool = False,
        autopct: str | None = "%1.1f%%",
        pctdistance: float = 0.72,
        labeldistance: float | None = 1.05,
        normalize: bool = True,
        sort_values: bool = False,
        textprops: dict[str, Any] | None = None,
        wedgeprops: dict[str, Any] | None = None,
        label_color: str = "black",
        autopct_color: str = "white",
        autopct_fontweight: str | int = "bold",
        text_edge_color: str | None = None,
        text_edge_width: float = 0.0,
    ) -> Self:
        """
        Add a pie chart to the active figure.

        This method handles only pie-specific behavior. Figure
        creation, titles, subtitles, sources, legends, and general
        layout are handled through their standalone methods.

        Parameters
        ----------
        ticker:
            DataFrame column plotted by the pie chart. If None, the
            selected DataFrame must contain exactly one column.

        df_index:
            Position of the DataFrame stored in the graph object.

        labels:
            Display labels assigned to pie categories.

        colors:
            Colors assigned to pie categories.

        explode:
            Offset applied to one or more pie wedges.

        donut_width:
            Width of the wedges when creating a donut chart.

        startangle:
            Starting angle of the first wedge.

        counterclock:
            Whether wedges are plotted counterclockwise.

        autopct:
            Format used for percentage labels. Use None to hide
            percentage values.

        pctdistance:
            Radial distance of percentage labels.

        labeldistance:
            Radial distance of category labels. Use None to omit
            category labels from the chart while preserving metadata.

        normalize:
            Whether Matplotlib normalizes values to a complete pie.

        sort_values:
            Whether categories are sorted from largest to smallest.

        textprops:
            Matplotlib text properties applied to pie labels.

        wedgeprops:
            Matplotlib properties applied to pie wedges.

        label_color:
            Color applied to category labels.

        autopct_color:
            Color applied to percentage labels.

        autopct_fontweight:
            Font weight applied to percentage labels.

        text_edge_color:
            Optional stroke color applied to pie text.

        text_edge_width:
            Width of the optional text stroke.

        Returns
        -------
        Self
            The current graph instance.
        """
        if not isinstance(df_index, int):
            raise TypeError(
                "'df_index' must be an integer."
            )

        if not isinstance(
            startangle,
            (int, float),
        ):
            raise TypeError(
                "'startangle' must be numeric."
            )

        if not isinstance(counterclock, bool):
            raise TypeError(
                "'counterclock' must be a boolean."
            )

        if (
            autopct is not None
            and not isinstance(autopct, str)
            and not callable(autopct)
        ):
            raise TypeError(
                "'autopct' must be a string, callable, "
                "or None."
            )

        if not isinstance(
            pctdistance,
            (int, float),
        ):
            raise TypeError(
                "'pctdistance' must be numeric."
            )

        if (
            labeldistance is not None
            and not isinstance(
                labeldistance,
                (int, float),
            )
        ):
            raise TypeError(
                "'labeldistance' must be numeric or None."
            )

        if not isinstance(normalize, bool):
            raise TypeError(
                "'normalize' must be a boolean."
            )

        if not isinstance(sort_values, bool):
            raise TypeError(
                "'sort_values' must be a boolean."
            )

        if not isinstance(
            text_edge_width,
            (int, float),
        ):
            raise TypeError(
                "'text_edge_width' must be numeric."
            )

        if text_edge_width < 0:
            raise ValueError(
                "'text_edge_width' cannot be negative."
            )

        dataframe = self._select_df(
            df_idx=df_index,
        )

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):
            raise TypeError(
                "The selected object must be a "
                "pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "Cannot create a pie chart from an "
                "empty DataFrame."
            )

        value_column = (
            self._resolve_pie_value_column(
                dataframe=dataframe,
                ticker=ticker,
            )
        )

        series = self._build_pie_series(
            dataframe=dataframe,
            value_column=value_column,
            sort_values=sort_values,
        )

        categories = series.index.tolist()

        plot_labels = self._resolve_pie_labels(
            categories=categories,
            labels=labels,
        )

        plot_colors = self._resolve_pie_colors(
            categories=categories,
            colors=colors,
        )

        plot_explode = self._resolve_pie_explode(
            categories=categories,
            explode=explode,
        )

        resolved_textprops = dict(
            textprops or {}
        )

        resolved_wedgeprops = (
            self._build_pie_wedgeprops(
                wedgeprops=wedgeprops,
                donut_width=donut_width,
            )
        )

        if not hasattr(self, "_ax") or self._ax is None:
            self.plot()

        pie_output = self._ax.pie(
            series.to_numpy(dtype=float),
            labels=(
                plot_labels
                if labeldistance is not None
                else None
            ),
            colors=plot_colors,
            explode=plot_explode,
            startangle=float(startangle),
            counterclock=counterclock,
            autopct=autopct,
            pctdistance=float(pctdistance),
            labeldistance=labeldistance,
            textprops=resolved_textprops,
            wedgeprops=resolved_wedgeprops,
            normalize=normalize,
        )

        wedges = pie_output[0]

        if labeldistance is not None:
            label_texts = list(
                pie_output[1]
            )
        else:
            label_texts = []

        if autopct is not None:
            percentage_texts = list(
                pie_output[2]
            )
        else:
            percentage_texts = []

        self._style_pie_texts(
            label_texts=label_texts,
            percentage_texts=percentage_texts,
            label_color=label_color,
            autopct_color=autopct_color,
            autopct_fontweight=(
                autopct_fontweight
            ),
            text_edge_color=text_edge_color,
            text_edge_width=float(
                text_edge_width
            ),
        )

        self._ax.axis("equal")

        metadata_label_texts = [
            (
                label_texts[position]
                if position < len(label_texts)
                else None
            )
            for position in range(
                len(categories)
            )
        ]

        self._store_pie_metadata(
            value_column=value_column,
            series=series,
            categories=categories,
            labels=plot_labels,
            colors=plot_colors,
            wedges=wedges,
            label_texts=metadata_label_texts,
            percentage_texts=percentage_texts,
        )

        return self