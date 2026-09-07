from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from typing import Any, Self

import numpy as np
import pandas as pd

from ..models import (
    BoxSeriesConfig,
    BoxSeriesDict,
    BoxSeriesLike,
    XAxisConfig,
    XAxisLike,
    coerce_configs,
    config_to_dict,
)
from ..tags._colors import PALETA_COLORES


class BoxWChartMixin:
    """
    Provides box-and-whisker chart construction logic for GraphMtplt.
    """

    def _normalize_box_series(
        self,
        dataframe: pd.DataFrame,
        series: Sequence[BoxSeriesLike] | None = None,
    ) -> list[BoxSeriesDict]:
        """
        Normalize and validate box-series configurations.

        If series is None, all DataFrame columns are included using
        their default configuration.
        """
        if series is None:
            series = [
                BoxSeriesConfig(
                    ticker=str(column),
                )
                for column in dataframe.columns
            ]

        if not series:
            raise ValueError(
                "'series' cannot be empty. "
                "Use None to plot all DataFrame columns."
            )

        normalized: list[BoxSeriesConfig] = []

        for position, item in enumerate(series):
            if isinstance(item, BoxSeriesConfig):
                config = item

            elif isinstance(item, dict):
                try:
                    config = BoxSeriesConfig(**item)

                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "Invalid box-series configuration "
                        f"at position {position}: {item}."
                    ) from exc

            else:
                raise TypeError(
                    "Each item in 'series' must be a "
                    "dictionary or a BoxSeriesConfig instance."
                )

            if config.ticker not in dataframe.columns:
                raise KeyError(
                    f"Ticker '{config.ticker}' was not found "
                    "in the selected DataFrame."
                )

            numeric_values = pd.to_numeric(
                dataframe[config.ticker],
                errors="coerce",
            )

            numeric_values = numeric_values.replace(
                [np.inf, -np.inf],
                np.nan,
            ).dropna()

            if numeric_values.empty:
                raise ValueError(
                    f"Ticker '{config.ticker}' contains no "
                    "finite numeric observations."
                )

            normalized.append(config)

        tickers = [
            config.ticker
            for config in normalized
        ]

        if len(tickers) != len(set(tickers)):
            raise ValueError(
                "Duplicated tickers are not allowed in "
                "'series'."
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
            BoxSeriesDict(**asdict(config))
            for config in normalized
        ]

    def _default_box_config(
        self,
    ) -> dict[str, Any]:
        """
        Return the default Matplotlib boxplot configuration.
        """
        return {
            "whis": (0, 100),
            "showfliers": False,
            "showmeans": False,
            "meanline": False,
            "widths": 0.6,
            "notch": False,
            "vert": True,
        }

    def _default_box_style(
        self,
    ) -> dict[str, Any]:
        """
        Return default box-border properties.
        """
        return {
            "color": "#6E6E6E",
            "linewidth": 0.5,
        }

    def _default_median_style(
        self,
    ) -> dict[str, Any]:
        """
        Return default median-line properties.
        """
        return {
            "color": "#222222",
            "linewidth": 1.5,
        }

    def _default_whisker_style(
        self,
    ) -> dict[str, Any]:
        """
        Return default whisker properties.
        """
        return {
            "color": "#6E6E6E",
            "linewidth": 0.5,
        }

    def _default_cap_style(
        self,
    ) -> dict[str, Any]:
        """
        Return default cap properties.
        """
        return {
            "color": "#6E6E6E",
            "linewidth": 0.5,
        }

    def _default_flier_style(
        self,
    ) -> dict[str, Any]:
        """
        Return default outlier-marker properties.
        """
        return {
            "marker": "o",
            "markersize": 3.5,
            "markerfacecolor": "#999999",
            "markeredgecolor": "#999999",
            "alpha": 0.85,
        }

    def _default_mean_style(
        self,
    ) -> dict[str, Any]:
        """
        Return default mean-line or mean-marker properties.
        """
        return {
            "color": "#404040",
            "linewidth": 0.5,
            "linestyle": "--",
        }

    def _merge_box_style(
        self,
        default: dict[str, Any],
        override: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Merge user styling over default styling.
        """
        resolved = default.copy()

        if override is not None:
            resolved.update(override)

        return resolved

    def _build_box_data(
        self,
        dataframe: pd.DataFrame,
        series_config: list[BoxSeriesDict],
    ) -> list[np.ndarray]:
        """
        Build finite numeric arrays for each box series.
        """
        output = []

        for item in series_config:
            values = pd.to_numeric(
                dataframe[item["ticker"]],
                errors="coerce",
            )

            values = values.replace(
                [np.inf, -np.inf],
                np.nan,
            ).dropna()

            output.append(
                values.to_numpy(dtype=float)
            )

        return output

    def _resolve_box_labels(
        self,
        series_config: list[BoxSeriesDict],
        x_axis_config: dict[str, Any],
    ) -> list[str]:
        """
        Resolve box labels using the shared X-axis configuration.
        """
        labels = [
            str(item["label"])
            for item in series_config
        ]

        tick_labels = x_axis_config.get(
            "tick_labels"
        )

        tick_label_map = (
            x_axis_config.get("tick_label_map")
            or {}
        )

        if tick_labels is not None:
            resolved_labels = list(tick_labels)

            if len(resolved_labels) != len(labels):
                raise ValueError(
                    "'x_axis.tick_labels' must have the "
                    "same length as the selected box series."
                )

            return [
                str(label)
                for label in resolved_labels
            ]

        return [
            str(
                tick_label_map.get(
                    label,
                    label,
                )
            )
            for label in labels
        ]

    def _apply_box_xaxis(
        self,
        *,
        series_config: list[BoxSeriesDict],
        x_axis_config: dict[str, Any],
        vertical: bool,
    ) -> None:
        """
        Apply categorical labels and store box-axis metadata.
        """
        labels = self._resolve_box_labels(
            series_config=series_config,
            x_axis_config=x_axis_config,
        )

        positions = np.arange(
            1,
            len(labels) + 1,
            dtype=float,
        )

        fontsize = x_axis_config.get(
            "fontsize",
            8,
        )

        rotation = x_axis_config.get(
            "rotation",
            0,
        )

        horizontal_alignment = (
            x_axis_config.get(
                "ha",
                "center",
            )
        )

        vertical_alignment = (
            x_axis_config.get(
                "va",
                "top",
            )
        )

        label_color = x_axis_config.get(
            "label_color"
        )

        if vertical:
            self._ax.set_xticks(positions)

            self._ax.set_xticklabels(
                labels,
                fontsize=fontsize,
                rotation=rotation,
                ha=horizontal_alignment,
                va=vertical_alignment,
            )

            if label_color is not None:
                for tick_label in (
                    self._ax.get_xticklabels()
                ):
                    tick_label.set_color(
                        label_color
                    )

        else:
            self._ax.set_yticks(positions)

            self._ax.set_yticklabels(
                labels,
                fontsize=fontsize,
                rotation=rotation,
                ha=horizontal_alignment,
                va=vertical_alignment,
            )

            if label_color is not None:
                for tick_label in (
                    self._ax.get_yticklabels()
                ):
                    tick_label.set_color(
                        label_color
                    )

        self._x_axis_mode = "categorical"
        self._x_axis_fechas = None
        self._x_vals = positions

        self._x_axis_metadata = {
            "mode": "categorical",
            "chart_type": "box_whiskers",
            "orientation": (
                "vertical"
                if vertical
                else "horizontal"
            ),
            "tickers": [
                item["ticker"]
                for item in series_config
            ],
            "labels": labels,
            "x_vals": positions,
            "tick_labels": (
                x_axis_config.get("tick_labels")
            ),
            "tick_label_map": (
                x_axis_config.get(
                    "tick_label_map"
                )
            ),
            "fontsize": fontsize,
            "rotation": rotation,
            "ha": horizontal_alignment,
            "va": vertical_alignment,
            "label_color": label_color,
        }

    def _store_box_metadata(
        self,
        *,
        dataframe: pd.DataFrame,
        df_index: int,
        series_config: list[BoxSeriesDict],
    ) -> None:
        """
        Store reusable box-chart metadata in the active chart state.
        """
        state = self._ensure_active_state()

        axis_map = {
            item["ticker"]: "left"
            for item in series_config
        }

        state.dataframe_idx = df_index
        state.dataframe = dataframe
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

        state.x_axis_mode = self._x_axis_mode
        state.x_axis_fechas = self._x_axis_fechas
        state.x_vals = self._x_vals
        state.x_axis_metadata = self._x_axis_metadata

        self._df = dataframe
        self._ticker_label_color = (
            state.ticker_label_color
        )

    def graph_box_whiskers(
        self,
        series: Sequence[BoxSeriesLike] | None = None,
        df_index: int = 0,
        box_config: dict[str, Any] | None = None,
        box_style: dict[str, Any] | None = None,
        median_style: dict[str, Any] | None = None,
        whisker_style: dict[str, Any] | None = None,
        cap_style: dict[str, Any] | None = None,
        flier_style: dict[str, Any] | None = None,
        mean_style: dict[str, Any] | None = None,
        box_face_alpha: float = 0.50,
        x_axis: XAxisLike | None = None,
    ) -> Self:
        """
        Add a box-and-whisker chart to the active figure.

        This method handles only box-specific behavior. Figure
        creation, titles, subtitles, sources, legends, general axis
        formatting, guides, and reference lines are handled through
        their standalone methods.

        If series is None, all numeric DataFrame columns are plotted
        using automatic labels and palette colors.

        Parameters
        ----------
        series:
            Box-series configurations. Each item can be a dictionary
            or BoxSeriesConfig instance.

        df_index:
            Position of the DataFrame stored in the graph object.

        box_config:
            General keyword arguments passed to Matplotlib boxplot.

        box_style:
            Properties applied to box borders.

        median_style:
            Properties applied to median lines.

        whisker_style:
            Properties applied to whiskers.

        cap_style:
            Properties applied to whisker caps.

        flier_style:
            Properties applied to outlier markers.

        mean_style:
            Properties applied to mean lines or markers.

        box_face_alpha:
            Opacity applied to box face colors.

        x_axis:
            Shared X-axis configuration used to format box labels.

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
            box_face_alpha,
            (int, float),
        ):
            raise TypeError(
                "'box_face_alpha' must be numeric."
            )

        if not 0 <= box_face_alpha <= 1:
            raise ValueError(
                "'box_face_alpha' must be between "
                "zero and one."
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
                "Cannot create a box plot from an "
                "empty DataFrame."
            )

        series_config = (
            self._normalize_box_series(
                dataframe=dataframe,
                series=series,
            )
        )

        tickers = [
            item["ticker"]
            for item in series_config
        ]

        selected_dataframe = dataframe.loc[
            :,
            tickers,
        ].copy()

        configs = coerce_configs(
            x_axis=(x_axis, XAxisConfig),
        )

        x_axis_config = config_to_dict(
            configs["x_axis"]
        )

        resolved_box_config = (
            self._merge_box_style(
                self._default_box_config(),
                box_config,
            )
        )

        resolved_box_style = (
            self._merge_box_style(
                self._default_box_style(),
                box_style,
            )
        )

        resolved_median_style = (
            self._merge_box_style(
                self._default_median_style(),
                median_style,
            )
        )

        resolved_whisker_style = (
            self._merge_box_style(
                self._default_whisker_style(),
                whisker_style,
            )
        )

        resolved_cap_style = (
            self._merge_box_style(
                self._default_cap_style(),
                cap_style,
            )
        )

        resolved_flier_style = (
            self._merge_box_style(
                self._default_flier_style(),
                flier_style,
            )
        )

        resolved_mean_style = (
            self._merge_box_style(
                self._default_mean_style(),
                mean_style,
            )
        )

        vertical = resolved_box_config.get(
            "vert",
            True,
        )

        if not isinstance(vertical, bool):
            raise TypeError(
                "'box_config.vert' must be a boolean."
            )

        if not hasattr(self, "_ax") or self._ax is None:
            self.plot()

        box_data = self._build_box_data(
            dataframe=selected_dataframe,
            series_config=series_config,
        )

        labels = [
            str(item["label"])
            for item in series_config
        ]

        boxplot_result = self._ax.boxplot(
            box_data,
            labels=labels,
            patch_artist=True,
            boxprops=resolved_box_style,
            medianprops=resolved_median_style,
            whiskerprops=resolved_whisker_style,
            capprops=resolved_cap_style,
            flierprops=resolved_flier_style,
            meanprops=resolved_mean_style,
            **resolved_box_config,
        )

        for position, patch in enumerate(
            boxplot_result["boxes"]
        ):
            patch.set_facecolor(
                series_config[position]["color"]
            )

            patch.set_alpha(
                float(box_face_alpha)
            )

            patch.set_label(
                str(
                    series_config[position][
                        "label"
                    ]
                )
            )

        self._apply_box_xaxis(
            series_config=series_config,
            x_axis_config=x_axis_config,
            vertical=vertical,
        )

        self._store_box_metadata(
            dataframe=selected_dataframe,
            df_index=df_index,
            series_config=series_config,
        )

        self._apply_box_tags(
            dataframe=selected_dataframe,
            series_config=series_config,
            vertical=vertical,
            whis=resolved_box_config.get(
                "whis",
                1.5,
            ),
            ax=self._ax,
        )

        return self