from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd


class BarTags:
    """
    Provides tag-generation logic for bar charts.

    Bar tags are configured inside each BarSeriesConfig through the
    ``tag`` field and are applied automatically by graph_bar().
    """

    def _normalize_bar_x_key(self, value):
        """Normalize an X-axis value for consistent matching."""
        if isinstance(value, (pd.Timestamp, np.datetime64)):
            return pd.Timestamp(value)

        return value

    def _resolve_bar_x_indices(
        self,
        *,
        ticker: str,
        x_values,
        bars_data: dict[str, dict[str, Any]],
        x_reference: Sequence,
    ) -> list[int]:
        """Resolve configured X-axis values into positional indices."""
        if len(x_reference) == 0:
            return []

        if ticker not in bars_data:
            raise KeyError(
                f"Ticker '{ticker}' was not found in bars_data."
            )

        if x_values is None:
            x_values = "last"

        if isinstance(x_values, str):
            if x_values == "all":
                return list(range(len(x_reference)))

            if x_values == "last":
                bars_entry = bars_data[ticker]

                for index in range(
                    len(x_reference) - 1,
                    -1,
                    -1,
                ):
                    rectangle, _ = self._get_bar_rectangle(
                        bars_entry=bars_entry,
                        index=index,
                    )

                    if rectangle is None:
                        continue

                    height = rectangle.get_height()

                    if (
                        height is not None
                        and np.isfinite(height)
                        and abs(height) > 0
                    ):
                        return [index]

                return []

            requested_values = [x_values]

        elif isinstance(x_values, (list, tuple, set)):
            requested_values = list(x_values)

        else:
            requested_values = [x_values]

        normalized_reference = [
            self._normalize_bar_x_key(value)
            for value in x_reference
        ]

        normalized_requested = {
            self._normalize_bar_x_key(value)
            for value in requested_values
        }

        return [
            index
            for index, value in enumerate(normalized_reference)
            if value in normalized_requested
        ]

    def _get_bar_rectangle(
        self,
        *,
        bars_entry: dict[str, Any],
        index: int,
    ):
        """Return the bar rectangle associated with an X-axis index."""
        bars_object = bars_entry["bars"]

        if isinstance(bars_object, dict):
            positive_bars = bars_object.get("pos")
            negative_bars = bars_object.get("neg")

            positive_rectangle = None
            negative_rectangle = None

            if (
                positive_bars is not None
                and index < len(positive_bars)
            ):
                positive_rectangle = positive_bars[index]

            if (
                negative_bars is not None
                and index < len(negative_bars)
            ):
                negative_rectangle = negative_bars[index]

            if positive_rectangle is not None:
                height = positive_rectangle.get_height()

                if (
                    height is not None
                    and np.isfinite(height)
                    and abs(height) > 0
                ):
                    return positive_rectangle, "stacked"

            if negative_rectangle is not None:
                height = negative_rectangle.get_height()

                if (
                    height is not None
                    and np.isfinite(height)
                    and abs(height) > 0
                ):
                    return negative_rectangle, "stacked"

            return None, "stacked"

        if index < len(bars_object):
            return bars_object[index], "bar"

        return None, "bar"

    def _get_bar_stack_total_anchor(
        self,
        *,
        index: int,
        reference_ticker: str,
        bars_data: dict[str, dict[str, Any]],
    ):
        """Return the anchor and total value for a stacked bar."""
        reference_entry = bars_data.get(reference_ticker)

        if reference_entry is None:
            return None, None, None, None

        reference_rectangle, mode = self._get_bar_rectangle(
            bars_entry=reference_entry,
            index=index,
        )

        if reference_rectangle is None:
            return None, None, None, None

        if mode != "stacked":
            raise ValueError(
                "'stack_total' can only be used with stacked bars."
            )

        x_position = (
            reference_rectangle.get_x()
            + reference_rectangle.get_width() / 2
        )

        total_value = 0.0
        positive_anchor = 0.0
        negative_anchor = 0.0

        for entry in bars_data.values():
            bars_object = entry["bars"]

            if not isinstance(bars_object, dict):
                continue

            positive_bars = bars_object.get("pos")
            negative_bars = bars_object.get("neg")

            if (
                positive_bars is not None
                and index < len(positive_bars)
            ):
                rectangle = positive_bars[index]
                height = rectangle.get_height()

                if height is not None and np.isfinite(height):
                    total_value += height
                    positive_anchor = max(
                        positive_anchor,
                        rectangle.get_y() + height,
                    )

            if (
                negative_bars is not None
                and index < len(negative_bars)
            ):
                rectangle = negative_bars[index]
                height = rectangle.get_height()

                if height is not None and np.isfinite(height):
                    total_value += height
                    negative_anchor = min(
                        negative_anchor,
                        rectangle.get_y() + height,
                    )

        if total_value >= 0:
            return (
                x_position,
                positive_anchor,
                total_value,
                "positive",
            )

        return (
            x_position,
            negative_anchor,
            total_value,
            "negative",
        )

    def _format_bar_tag(
        self,
        *,
        template: str,
        ticker: str,
        label: str,
        x_value,
        y_value: float | None = None,
        total_value: float | None = None,
    ) -> str:
        """Format the text displayed by a bar tag."""
        try:
            return template.format(
                ticker=ticker,
                label=label,
                x_value=x_value,
                y_value=y_value,
                total_value=total_value,
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid bar-tag template for ticker "
                f"'{ticker}': {template!r}."
            ) from exc

    def _draw_bar_tag(
        self,
        *,
        ax,
        x_position: float,
        y_position: float,
        text: str,
        tag_config: dict[str, Any],
        default_offset: tuple[float, float],
        default_h_align: str,
        default_v_align: str,
    ) -> None:
        """Draw a bar tag directly on the selected Matplotlib axis."""
        config = tag_config.copy()

        offset = config.pop("ubic_etq", default_offset)

        if offset is None:
            offset = default_offset

        if (
            not isinstance(offset, tuple)
            or len(offset) != 2
            or not all(
                isinstance(value, (int, float))
                for value in offset
            )
        ):
            raise TypeError(
                "'ubic_etq' must be a tuple containing "
                "two numeric values."
            )

        horizontal_alignment = config.pop(
            "label_h_align",
            default_h_align,
        )

        vertical_alignment = config.pop(
            "label_v_align",
            default_v_align,
        )

        fontsize = config.pop("fontsize", 8)
        color = config.pop("color", "#262626")
        fontweight = config.pop("fontweight", "normal")
        fontstyle = config.pop("fontstyle", "normal")
        rotation = config.pop("rotation", 0)
        alpha = config.pop("alpha", 1.0)
        bbox = config.pop("bbox", None)
        arrowprops = config.pop("arrowprops", None)
        zorder = config.pop("zorder", 5)
        clip_on = config.pop("clip_on", False)

        annotation = ax.annotate(
            text=text,
            xy=(x_position, y_position),
            xytext=offset,
            textcoords="offset points",
            ha=horizontal_alignment,
            va=vertical_alignment,
            fontsize=fontsize,
            color=color,
            fontweight=fontweight,
            fontstyle=fontstyle,
            rotation=rotation,
            alpha=alpha,
            bbox=bbox,
            arrowprops=arrowprops,
            zorder=zorder,
            clip_on=clip_on,
            annotation_clip=False,
            **config,
        )

        annotation.set_in_layout(False)

    def _apply_single_bar_tag(
        self,
        *,
        ax,
        ticker: str,
        label: str,
        tag_config: dict[str, Any],
        bars_data: dict[str, dict[str, Any]],
        x_reference: Sequence,
    ) -> None:
        """Apply one tag configuration to one bar series."""
        base_config = tag_config.copy()

        show = base_config.pop("show", "value_label")
        x_values = base_config.pop("x_values", "last")
        template = base_config.pop(
            "template",
            "{y_value:,.2f}",
        )

        valid_show_values = {
            "value_label",
            "bar_tag",
            "stack_total",
        }

        if show not in valid_show_values:
            raise ValueError(
                "'show' must be one of: "
                "'value_label', 'bar_tag', or 'stack_total'."
            )

        indices = self._resolve_bar_x_indices(
            ticker=ticker,
            x_values=x_values,
            bars_data=bars_data,
            x_reference=x_reference,
        )

        for index in indices:
            if index >= len(x_reference):
                continue

            x_value = x_reference[index]
            config = base_config.copy()

            if show == "stack_total":
                (
                    x_position,
                    y_position,
                    total_value,
                    sign,
                ) = self._get_bar_stack_total_anchor(
                    index=index,
                    reference_ticker=ticker,
                    bars_data=bars_data,
                )

                if x_position is None:
                    continue

                text = self._format_bar_tag(
                    template=template,
                    ticker=ticker,
                    label=label,
                    x_value=x_value,
                    total_value=total_value,
                )

                default_offset = (
                    (0, 5)
                    if sign == "positive"
                    else (0, -5)
                )

                configured_offset = config.pop(
                    "ubic_etq",
                    default_offset,
                )

                if configured_offset is None:
                    configured_offset = default_offset

                if sign == "positive":
                    configured_offset = (
                        configured_offset[0],
                        abs(configured_offset[1]),
                    )
                    default_v_align = "bottom"
                else:
                    configured_offset = (
                        configured_offset[0],
                        -abs(configured_offset[1]),
                    )
                    default_v_align = "top"

                self._draw_bar_tag(
                    ax=ax,
                    x_position=x_position,
                    y_position=y_position,
                    text=text,
                    tag_config={
                        **config,
                        "ubic_etq": configured_offset,
                    },
                    default_offset=default_offset,
                    default_h_align="center",
                    default_v_align=default_v_align,
                )

                continue

            rectangle, mode = self._get_bar_rectangle(
                bars_entry=bars_data[ticker],
                index=index,
            )

            if rectangle is None:
                continue

            height = rectangle.get_height()

            if (
                height is None
                or not np.isfinite(height)
                or abs(height) == 0
            ):
                continue

            x_position = (
                rectangle.get_x()
                + rectangle.get_width() / 2
            )

            y_start = rectangle.get_y()
            y_end = y_start + height
            y_center = y_start + height / 2

            text = self._format_bar_tag(
                template=template,
                ticker=ticker,
                label=label,
                x_value=x_value,
                y_value=height,
            )

            if show == "bar_tag":
                self._draw_bar_tag(
                    ax=ax,
                    x_position=x_position,
                    y_position=y_center,
                    text=text,
                    tag_config=config,
                    default_offset=(0, 0),
                    default_h_align="center",
                    default_v_align="center",
                )

                continue

            if mode == "stacked":
                self._draw_bar_tag(
                    ax=ax,
                    x_position=x_position,
                    y_position=y_center,
                    text=text,
                    tag_config=config,
                    default_offset=(0, 0),
                    default_h_align="center",
                    default_v_align="center",
                )

                continue

            default_offset = (
                (0, 3)
                if height >= 0
                else (0, -3)
            )

            configured_offset = config.pop(
                "ubic_etq",
                default_offset,
            )

            if configured_offset is None:
                configured_offset = default_offset

            if height >= 0:
                configured_offset = (
                    configured_offset[0],
                    abs(configured_offset[1]),
                )
                default_v_align = "bottom"
            else:
                configured_offset = (
                    configured_offset[0],
                    -abs(configured_offset[1]),
                )
                default_v_align = "top"

            self._draw_bar_tag(
                ax=ax,
                x_position=x_position,
                y_position=y_end,
                text=text,
                tag_config={
                    **config,
                    "ubic_etq": configured_offset,
                },
                default_offset=default_offset,
                default_h_align="center",
                default_v_align=default_v_align,
            )

    def _apply_bar_tags(
        self,
        *,
        series_config: list[dict[str, Any]],
        bars_data: dict[str, dict[str, Any]],
        x_reference: Sequence,
        left_ax,
        right_ax,
    ) -> None:
        """Apply tags declared inside each bar-series configuration."""
        for item in series_config:
            ticker = item["ticker"]
            label = item["label"]
            axis_side = item["axis_side"]
            tag_configs = item.get("tag")

            if not tag_configs:
                continue

            if isinstance(tag_configs, dict):
                tag_configs = [tag_configs]

            if not isinstance(tag_configs, (list, tuple)):
                raise TypeError(
                    f"'tag' for ticker '{ticker}' must be "
                    "a dictionary, a list of dictionaries, "
                    "or None."
                )

            plot_ax = (
                right_ax
                if axis_side == "right"
                else left_ax
            )

            if plot_ax is None:
                raise RuntimeError(
                    f"Axis '{axis_side}' was not initialized "
                    f"for ticker '{ticker}'."
                )

            for position, tag_config in enumerate(tag_configs):
                if not isinstance(tag_config, dict):
                    raise TypeError(
                        "Each item inside 'tag' must be a "
                        "dictionary. Invalid item at position "
                        f"{position} for ticker '{ticker}'."
                    )

                self._apply_single_bar_tag(
                    ax=plot_ax,
                    ticker=ticker,
                    label=label,
                    tag_config=tag_config,
                    bars_data=bars_data,
                    x_reference=x_reference,
                )

        self._ax = left_ax
