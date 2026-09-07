from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from numbers import Real
from typing import Literal, TypeAlias

import pandas as pd
from pandas import DataFrame

from pandas.io.formats.style import Styler

StylerLike: TypeAlias = DataFrame | Styler

Label: TypeAlias = Hashable
Labels: TypeAlias = Hashable | Iterable[Hashable]
LabelCollection: TypeAlias = Iterable[Hashable]

CSSProperties: TypeAlias = Mapping[str, str]
OptionalCSSProperties: TypeAlias = Mapping[str, str] | None

BorderPosition: TypeAlias = Literal[
    "top",
    "bottom",
    "left",
    "right",
]

RowBorderPosition: TypeAlias = Literal[
    "top",
    "bottom",
]

ColumnBorderPosition: TypeAlias = Literal[
    "left",
    "right",
]

BorderLineStyle: TypeAlias = Literal[
    "none",
    "hidden",
    "dotted",
    "dashed",
    "solid",
    "double",
    "groove",
    "ridge",
    "inset",
    "outset",
]

ColorRanges: TypeAlias = Mapping[tuple[Real, Real], str]