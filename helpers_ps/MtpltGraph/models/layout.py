# MtpltGraph/config_models/layout.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FigureTitle:
    text: str = ""
    x: float = 0.02
    y: float = 0.93
    fontsize: int = 12
    color: str = "#000000"
    fontweight: str = "bold"
    ha: str = "left"
    va: str = "top"

@dataclass(slots=True)
class FigureSubtitle:
    text: str = ""
    x: float = 0.02
    y: float = 0.88
    fontsize: int = 9
    color: str = "#333333"
    fontweight: str = "normal"
    ha: str = "left"
    va: str = "top"

@dataclass(slots=True)
class FigureSource:
    text: str | list[str] | None = None
    x: float = 0.02
    y: float = 0.022
    fontsize: float = 6
    color: str = "#606060"
    line_spacing: float = 0.022


@dataclass(slots=True)
class FigureConfig:
    figsize: tuple[float, float] = (6.00, 4.80)
    color: str = "#D5D5D5"
    researchtype: bool = True
    lw: float = 0.8

    nrows: int = 1
    ncols: int = 1
    sharex: bool = False
    sharey: bool = False
    dpi: int | None = None

    height_ratios: list[float] | None = None
    width_ratios: list[float] | None = None
    hspace: float | None = None
    wspace: float | None = None