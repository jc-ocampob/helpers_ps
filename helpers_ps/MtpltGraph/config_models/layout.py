# MtpltGraph/config_models/layout.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TitleConfig:
    title: str | None = None
    title_font_size: int = 12
    subtitle: str | None = None
    subtitle_font_size: int = 9


@dataclass(slots=True)
class SourceConfig:
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