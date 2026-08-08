# MtpltGraph/config_models/axis.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class XAxisConfig:
    bbg_format: bool = False
    tick_step: int = 6
    fmt: str | None = None
    year_y_offset: float = -0.08
    lim: tuple[Any, Any] | None = None
    fontsize: float = 8
    return_dataframe: bool = True

    tick_values: list[Any] | tuple[Any, ...] | Any | None = None
    tick_labels: list[str] | tuple[str, ...] | None = None
    tick_label_map: dict[Any, str] = field(default_factory=dict)

    rotation: float = 0
    ha: str = "center"
    label_color: str | None = None
    show_years: bool = True


@dataclass(slots=True)
class YAxisConfig:
    lim: tuple[float, float] | None = None
    fmt: str | None = None
    fontsize: float = 7
    tick_step: int | None = None

    label: str | None = None
    label_fontsize: float | None = None
    label_color: str | None = None
    tick_color: str | None = None
    spine_color: str | None = None

    margins_x: float | None = 0.01
    side: str | None = None

    # Keep this here because prep_y_axis supports explicit axis injection.
    # In most user-facing calls you will not pass it.
    ax: Any = None