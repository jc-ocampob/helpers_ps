from __future__ import annotations

from ._coerce import coerce_config, config_to_dict, clean_none, coerce_configs
from .axes import (
    XAxisConfig,
    XAxisDict,
    XAxisLike,
    XAxisLimit,
    XAxisTickValues,
    XAxisTickLabels,
    XAxisHorizontalAlignment,
    XAxisVerticalAlignment,
)

from .linesseries import LineSeriesLike, LineSeriesConfig, LineSeriesDict

from .layout import (
    FigureTitle,
    FigureConfig,
    FigureSource,
    FigureSubtitle
)

from .boxseries import (
    BoxTagMode,
    BoxTagStatistic,
    BoxTagXValue,
    BoxTagXValues,
    BoxHorizontalAlignment,
    BoxVerticalAlignment,
    BoxTagLabelDict,
    BoxTagDotDict,
    BoxTagDict,
    BoxSeriesConfig,
    BoxSeriesDict,
    BoxSeriesLike,
)

from .barseries import (
    BarAxisSide,
    BarTagMode,
    BarTagXValue,
    BarTagXValues,
    BarTagDict,
    BarSeriesConfig,
    BarSeriesDict,
    BarSeriesLike,
)

__all__ = [
    "coerce_configs",
    "coerce_config",
    "config_to_dict",
    "clean_none",

    # X Axis configs
    "XAxisConfig",
    "XAxisDict",
    "XAxisLike",
    "XAxisLimit",
    "XAxisTickValues",
    "XAxisTickLabels",
    "XAxisHorizontalAlignment",
    "XAxisVerticalAlignment",

    # Figure level configs
    "FigureTitle",
    "FigureConfig",
    "FigureSource",
    "FigureSubtitle",

    # Line Series configs
    "LineSeriesLike",
    "LineSeriesConfig",
    "LineSeriesDict",

    # Bar series configs
    "BarAxisSide",
    "BarTagMode",
    "BarTagXValue",
    "BarTagXValues",
    "BarTagDict",
    "BarSeriesConfig",
    "BarSeriesDict",
    "BarSeriesLike",

    # BoxW series configs
    "BoxTagMode",
    "BoxTagStatistic",
    "BoxTagXValue",
    "BoxTagXValues",
    "BoxHorizontalAlignment",
    "BoxVerticalAlignment",
    "BoxTagLabelDict",
    "BoxTagDotDict",
    "BoxTagDict",
    "BoxSeriesConfig",
    "BoxSeriesDict",
    "BoxSeriesLike",

]