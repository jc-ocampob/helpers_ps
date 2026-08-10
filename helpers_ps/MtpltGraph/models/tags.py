# MtpltGraph/config_models/tags.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TagStyle:
    label_h_align: str = "center"
    label_v_align: str = "center"
    ubic_etq: tuple[float, float] = (0, 17)
    fontsize: int = 7
    fontweight: str = "normal"
    font_color: str = "black"
    bg_color: str = "#ECEFF1"
    bg_alpha: float = 1.0
    edge_color: str = "none"
    show_bbox: bool = True
    text_edge_color: str | None = None
    text_edge_width: float = 0.0
    zorder: int = 6


@dataclass(slots=True)
class DotStyle:
    color: str = "red"
    size: float = 30
    zorder: int = 5


@dataclass(slots=True)
class LineTagConfig:
    ticker: str
    x_values: list[Any] | str = "last"
    show: str = "dot"
    template: str = "{ticker}\n{x_value:%B-%Y}: {y_value:,.2f}"
    tag: TagStyle | dict[str, Any] | None = None
    dot: DotStyle | dict[str, Any] | None = None
    legend_label: str | None = None