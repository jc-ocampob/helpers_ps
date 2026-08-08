# MtpltGraph/config_models/series.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AxisSide = Literal["left", "right"]


@dataclass(slots=True)
class SeriesSpec:
    ticker: str
    label: str
    color: str
    axis_side: AxisSide = "left"


def series_to_legacy_ticker_label_color(
    series: list[SeriesSpec],
) -> list[tuple[str, str, str]]:
    """
    Convert SeriesSpec list into existing legacy metadata format.

    Existing tag helpers still read:
        self._ticker_label_color = [(ticker, label, color), ...]
    """
    return [
        (item.ticker, item.label, item.color)
        for item in series
    ]


def series_to_axis_map(
    series: list[SeriesSpec],
) -> dict[str, AxisSide]:
    """
    Convert SeriesSpec list into existing axis map format.
    """
    return {
        item.ticker: item.axis_side
        for item in series
    }


def series_to_dicts(
    series: list[SeriesSpec],
) -> list[dict[str, str]]:
    """
    Convert SeriesSpec into current list-of-dicts structure used in charts.py.
    """
    return [
        {
            "ticker": item.ticker,
            "label": item.label,
            "color": item.color,
            "axis_side": item.axis_side,
        }
        for item in series
    ]