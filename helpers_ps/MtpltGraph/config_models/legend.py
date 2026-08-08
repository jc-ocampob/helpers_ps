# MtpltGraph/config_models/legend.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LegendConfig:
    show: bool = False
    loc: str = "upper left"
    bbox_to_anchor: tuple[float, float] | tuple[float, float, float, float] | None = None
    ncol: int = 1
    fontsize: int = 7
    frameon: bool = True
    edgecolor: str = "white"
    facecolor: str = "white"
    framealpha: float = 0.6