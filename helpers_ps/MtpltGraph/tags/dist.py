from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ..models import DistSeriesDict
from ..models.distseries import parse_dist_show


class DistTags:
    """
    Provide reference highlighting for distribution charts.

    Each series may contain a list of reference configurations (the
    ``tag`` field of ``DistSeriesConfig``). A reference can draw a
    vertical line, a tag and/or a dot on the distribution, in the same
    spirit as the line-chart tags:

    - ``mode="observation"``: highlight the value that the series takes
      at ``x_values`` (``"last"``, ``"first"`` or any index label).
    - ``mode="value"``: highlight a literal value on the X axis.
    - ``mode="statistic"``: highlight ``mean``, ``median``, ``q1``,
      ``q3``, ``min``, ``max`` or a percentile such as ``p5`` / ``p95``.
    """

    _DEFAULT_TEMPLATE = "{value:,.4g}\nP{percentile:.0f}"

    # ------------------------------------------------------------------
    # Public entry point (called by graph_dist)
    # ------------------------------------------------------------------
    def _apply_dist_tags(
        self,
        *,
        series_config: list[DistSeriesDict],
        dist_data: dict[str, dict[str, Any]],
    ) -> None:
        """Apply the references declared inside every series."""
        for item in series_config:
            tag_configs = item.get("tag")
            if not tag_configs:
                continue
            for position, tag_config in enumerate(tag_configs):
                if not isinstance(tag_config, dict):
                    raise TypeError(
                        "Each item inside 'tag' must be a "
                        f"dictionary. Invalid item at position "
                        f"{position} for ticker '{item['ticker']}'."
                    )
                self._apply_single_dist_tag(
                    series_item=item,
                    series_data=dist_data[item["ticker"]],
                    tag_config=tag_config,
                )

    # ------------------------------------------------------------------
    # Reference resolution
    # ------------------------------------------------------------------
    def _resolve_dist_references(
        self,
        *,
        series_data: dict[str, Any],
        tag_config: dict[str, Any],
        ticker: str,
    ) -> list[dict[str, Any]]:
        """
        Translate a reference configuration into points on the X axis.

        Returns a list of dictionaries with ``value`` (position on the
        distribution axis), ``x_value`` (observation label or the value
        itself) and ``statistic``.
        """
        series: pd.Series = series_data["series"]
        values: np.ndarray = series_data["values"]
        mode = tag_config.get(
            "mode",
            (
                "statistic" if "statistic" in tag_config
                else "value" if "value" in tag_config
                else "observation"
            ),
        )
        references: list[dict[str, Any]] = []

        if mode == "value":
            raw = tag_config["value"]
            raw_values = (
                list(raw) if isinstance(raw, (list, tuple, set)) else [raw]
            )
            for value in raw_values:
                references.append(
                    {
                        "value": float(value),
                        "x_value": float(value),
                        "statistic": None,
                    }
                )
            return references

        if mode == "statistic":
            raw = tag_config["statistic"]
            statistics = (
                list(raw) if isinstance(raw, (list, tuple)) else [raw]
            )
            for statistic in statistics:
                key = statistic.lower()
                if key == "mean":
                    value = float(np.mean(values))
                elif key == "median":
                    value = float(np.median(values))
                elif key == "q1":
                    value = float(np.percentile(values, 25))
                elif key == "q3":
                    value = float(np.percentile(values, 75))
                elif key == "min":
                    value = float(np.min(values))
                elif key == "max":
                    value = float(np.max(values))
                else:
                    value = float(np.percentile(values, float(key[1:])))
                references.append(
                    {
                        "value": value,
                        "x_value": value,
                        "statistic": key,
                    }
                )
            return references

        # mode == "observation"
        x_values = tag_config.get("x_values", "last")
        if not isinstance(x_values, (list, tuple, set)):
            x_values = [x_values]
        for x_value in x_values:
            if isinstance(x_value, str) and x_value == "last":
                label, value = series.index[-1], series.iloc[-1]
            elif isinstance(x_value, str) and x_value == "first":
                label, value = series.index[0], series.iloc[0]
            else:
                label = x_value
                if (
                    isinstance(series.index, pd.DatetimeIndex)
                    or label not in series.index
                ):
                    try:
                        label = pd.to_datetime(label)
                    except Exception:
                        pass
                if label not in series.index:
                    raise KeyError(
                        f"X-axis value {x_value!r} was not found "
                        f"for ticker '{ticker}'."
                    )
                value = series.loc[label]
                if isinstance(value, pd.Series):
                    value = value.iloc[-1]
            references.append(
                {
                    "value": float(value),
                    "x_value": label,
                    "statistic": None,
                }
            )
        return references

    def _dist_height_at(
        self,
        *,
        value: float,
        series_data: dict[str, Any],
        y_from: str,
    ) -> float:
        """
        Height of the distribution at ``value`` (used to anchor dots,
        tags and the end of the vertical line).
        """
        curves = series_data["curves"]
        heights = series_data["heights"]
        use_curve = (
            y_from == "curve"
            or (y_from == "auto" and bool(curves))
            or (y_from == "hist" and heights is None)
        )
        if use_curve:
            if not curves:
                raise ValueError(
                    "y_from='curve' requires at least one curve."
                )
            curve = curves[0]
            return float(np.interp(value, curve["x"], curve["y"]))
        if heights is None:
            raise ValueError(
                "y_from='hist' requires the histogram to be drawn."
            )
        edges = series_data["edges"]
        if value < edges[0] or value > edges[-1]:
            return 0.0
        index = int(np.searchsorted(edges, value, side="right")) - 1
        index = int(np.clip(index, 0, len(heights) - 1))
        return float(heights[index])

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _apply_single_dist_tag(
        self,
        *,
        series_item: DistSeriesDict,
        series_data: dict[str, Any],
        tag_config: dict[str, Any],
    ) -> None:
        """Draw one reference configuration of one series."""
        ticker = series_item["ticker"]
        label = series_item["label"]
        color = series_item["color"]
        values: np.ndarray = series_data["values"]
        ax = self._ax

        show = parse_dist_show(tag_config.get("show", "line_tag"))
        template = tag_config.get("template", self._DEFAULT_TEMPLATE)
        legend_label = tag_config.get("legend_label")
        y_from = tag_config.get("y_from", "auto")
        line_style = dict(tag_config.get("line") or {})
        tag_style = dict(tag_config.get("tag") or {})
        dot_style = dict(tag_config.get("dot") or {})

        references = self._resolve_dist_references(
            series_data=series_data,
            tag_config=tag_config,
            ticker=ticker,
        )

        std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        mean = float(np.mean(values))

        legend_used = False
        for reference in references:
            value = reference["value"]
            height = self._dist_height_at(
                value=value,
                series_data=series_data,
                y_from=y_from,
            )
            fields = {
                "ticker": ticker,
                "label": label,
                "x_value": reference["x_value"],
                "value": value,
                "y_value": value,
                "statistic": reference["statistic"],
                "percentile": 100.0 * float(np.mean(values <= value)),
                "zscore": (value - mean) / std if std > 0 else np.nan,
                "density": height,
            }

            def _format(text: str, what: str) -> str:
                try:
                    return text.format(**fields)
                except (KeyError, ValueError, TypeError, IndexError) as exc:
                    raise ValueError(
                        f"Invalid distribution-{what} template for "
                        f"ticker '{ticker}': {text!r}."
                    ) from exc

            if "line" in show:
                style = line_style.copy()
                extent = style.pop("extent", "curve")
                if extent not in {"curve", "top"}:
                    raise ValueError(
                        "'extent' must be 'curve' or 'top'."
                    )
                if extent == "curve" and (
                    not np.isfinite(height) or height <= 0
                ):
                    extent = "top"
                style.setdefault("color", color)
                style.setdefault("linestyle", "--")
                style.setdefault("linewidth", 1.2)
                style.setdefault("alpha", 1.0)
                style.setdefault("zorder", 4)
                line_label = (
                    _format(legend_label, "legend_label")
                    if legend_label is not None and not legend_used
                    else None
                )
                if extent == "top":
                    ax.axvline(
                        value,
                        ymin=0.0,
                        ymax=1.0,
                        label=line_label,
                        **style,
                    )
                else:
                    ax.vlines(
                        value,
                        0.0,
                        height,
                        label=line_label,
                        **style,
                    )
                legend_used = legend_used or line_label is not None

            if "dot" in show:
                final_dot = dot_style.copy()
                final_dot.setdefault("color", color)
                final_dot.setdefault("size", 40)
                final_dot.setdefault("marker_edgecolor", "white")
                final_dot.setdefault("marker_edgewidth", 0.8)
                final_dot.setdefault("zorder", 6)
                self.dot(
                    x_value=value,
                    y_value=height,
                    **final_dot,
                )

            if "tag" in show:
                final_tag = tag_style.copy()
                final_tag.setdefault("font_color", color)
                final_tag.setdefault("label_v_align", "bottom")
                final_tag.setdefault("ubic_etq", (0, 6))
                self.tag(
                    x_value=value,
                    y_value=height,
                    label=_format(template, "tag"),
                    **final_tag,
                )
