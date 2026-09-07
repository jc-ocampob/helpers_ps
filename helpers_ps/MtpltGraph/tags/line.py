from __future__ import annotations

from typing import Any

import pandas as pd

from ..models import LineSeriesDict


class LineTags:
    """
    Provide annotation helpers for line-chart series.

    Each line series may contain a list of tag configurations.
    Every configuration defines the x-axis values to annotate,
    whether to display a tag, a dot, or both, and their styling.

    The ticker, default color, label, and axis are inherited from
    the parent line-series configuration.
    """

    def _apply_line_tags(
        self,
        dataframe: pd.DataFrame,
        series_config: list[LineSeriesDict],
        left_ax,
        right_ax,
    ) -> None:
        """
        Apply configured annotations to all line series.

        Annotations are rendered on the same axis as their parent
        series. Each tag configuration can target one or multiple
        x-axis values, including the special value `"last"`.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            DataFrame containing the plotted series.

        series_config : list[LineSeriesDict]
            Normalized line-series configurations.

        left_ax : matplotlib.axes.Axes
            Primary y-axis.

        right_ax : matplotlib.axes.Axes or None
            Secondary y-axis.

        Returns
        -------
        None
            Annotations are added directly to the corresponding axes.
        """

        original_ax = self._ax

        try:
            for item in series_config:
                tag_configs = item.get("tags")

                if not tag_configs:
                    continue

                selected_side = item["axis_side"]

                target_ax = (
                    right_ax
                    if selected_side == "right"
                    else left_ax
                )

                if target_ax is None:
                    raise RuntimeError(
                        f"Axis '{selected_side}' is not available "
                        f"for ticker '{item['ticker']}'."
                    )

                self._ax = target_ax

                for tag_config in tag_configs:
                    self._apply_line_tag_config(
                        dataframe=dataframe,
                        series_item=item,
                        tag_config=tag_config,
                    )

        finally:
            self._ax = original_ax

    def _apply_line_tag_config(
        self,
        dataframe: pd.DataFrame,
        series_item: LineSeriesDict,
        tag_config: dict[str, Any],
    ) -> None:
        """
        Apply one annotation configuration to a line series.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            DataFrame containing the line series.

        series_item : LineSeriesDict
            Normalized configuration of the parent series.

        tag_config : dict[str, Any]
            Annotation configuration containing `x_values`,
            display mode, template, and styling options.

        Returns
        -------
        None
            Tags and dots are added directly to the active axis.
        """

        ticker = series_item["ticker"]
        default_color = series_item["color"]

        x_values = tag_config["x_values"]
        show = tag_config.get("show", "tag_dot")

        template = tag_config.get(
            "template",
            "{ticker}\n{x_value:%b-%Y}: {y_value:,.2f}",
        )

        tag_style = dict(
            tag_config.get("tag") or {}
        )

        dot_style = dict(
            tag_config.get("dot") or {}
        )

        legend_label = tag_config.get("legend_label")

        if not isinstance(x_values, (list, tuple, set)):
            x_values = [x_values]

        points: list[tuple[Any, Any]] = []

        series_data = dataframe[ticker]

        for x_value in x_values:
            if isinstance(x_value, str) and x_value == "last":
                valid_series = series_data.dropna()

                if valid_series.empty:
                    continue

                resolved_x = valid_series.index[-1]
                resolved_y = valid_series.iloc[-1]

            else:
                resolved_x = x_value

                if resolved_x not in dataframe.index:
                    try:
                        resolved_x = pd.to_datetime(resolved_x)
                    except Exception:
                        pass

                if resolved_x not in dataframe.index:
                    raise KeyError(
                        f"X-axis value {x_value!r} was not found "
                        f"for ticker '{ticker}'."
                    )

                resolved_y = dataframe.loc[
                    resolved_x,
                    ticker,
                ]

                if isinstance(resolved_y, pd.Series):
                    resolved_y = resolved_y.iloc[-1]

                if pd.isna(resolved_y):
                    continue

            points.append(
                (resolved_x, resolved_y)
            )

        if legend_label is not None:
            self.add_legend_point(
                label=legend_label,
                color=dot_style.get(
                    "color",
                    default_color,
                ),
                marker=dot_style.get(
                    "marker",
                    "o",
                ),
                markersize=dot_style.get(
                    "markersize",
                    6,
                ),
            )

        for x_value, y_value in points:
            if "tag" in show:
                final_tag_style = tag_style.copy()

                final_tag_style.setdefault(
                    "font_color",
                    default_color,
                )

                self.tag(
                    x_value=x_value,
                    y_value=y_value,
                    label=template.format(
                        ticker=ticker,
                        label=series_item["label"],
                        x_value=x_value,
                        y_value=y_value,
                    ),
                    **final_tag_style,
                )

            if "dot" in show:
                final_dot_style = dot_style.copy()

                final_dot_style.pop("marker", None)
                final_dot_style.pop("markersize", None)

                final_dot_style.setdefault(
                    "color",
                    default_color,
                )

                self.dot(
                    x_value=x_value,
                    y_value=y_value,
                    **final_dot_style,
                )