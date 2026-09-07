from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import (
    Any,
    Literal,
    TypeAlias,
    TypedDict,
)

import numpy as np
import pandas as pd


BoxTagMode: TypeAlias = Literal[
    "observation",
    "statistic",
]

BoxTagStatistic: TypeAlias = Literal[
    "low",
    "high",
    "mean",
    "median",
    "q1",
    "q3",
]

BoxTagXValue: TypeAlias = (
    str
    | int
    | float
    | date
    | datetime
    | pd.Timestamp
    | np.datetime64
)

BoxTagXValues: TypeAlias = (
    Literal["all", "last"]
    | BoxTagXValue
    | list[BoxTagXValue]
    | tuple[BoxTagXValue, ...]
    | set[BoxTagXValue]
)

BoxHorizontalAlignment: TypeAlias = Literal[
    "left",
    "center",
    "right",
]

BoxVerticalAlignment: TypeAlias = Literal[
    "top",
    "center",
    "bottom",
    "baseline",
    "center_baseline",
]


class BoxTagLabelDict(TypedDict, total=False):
    """
    Controls passed directly to ``self.tag()``.

    The label supports these template fields:

    - ``{ticker}``
    - ``{label}``
    - ``{x_value}``
    - ``{y_value}``
    - ``{value}``
    - ``{statistic}``
    """

    label: str

    ubic_etq: tuple[float, float]

    label_h_align: BoxHorizontalAlignment

    label_v_align: BoxVerticalAlignment

    fontsize: float

    fontweight: str | int

    font_color: str

    fontstyle: Literal[
        "normal",
        "italic",
        "oblique",
    ]

    rotation: float

    bg_color: str

    bg_alpha: float

    edge_color: str

    edge_width: float

    show_bbox: bool

    arrowprops: dict[str, Any] | None

    zorder: float

    clip_on: bool


class BoxTagDotDict(TypedDict, total=False):
    """
    Controls passed directly to ``self.dot()``.

    Exclude ``x_value`` and ``y_value`` because those coordinates are
    resolved automatically from the box series and reference point.
    """

    marker: str

    markersize: float

    marker_color: str

    marker_edgecolor: str

    marker_edgewidth: float

    alpha: float

    zorder: float

    clip_on: bool


class BoxTagDict(TypedDict, total=False):
    """
    Configuration for one box-chart reference.

    ``x_values`` selects observations from the original DataFrame
    index. Alternatively, ``statistic`` selects a calculated box
    statistic.

    ``tag`` contains controls for ``self.tag()`` and ``dot`` contains
    controls for ``self.dot()``. Set either entry to None to omit that
    visual element.
    """

    mode: BoxTagMode

    x_values: BoxTagXValues

    statistic: BoxTagStatistic

    tag: BoxTagLabelDict | None

    dot: BoxTagDotDict | None


class BoxSeriesDict(TypedDict):
    """
    Normalized dictionary representation of one box series.
    """

    ticker: str

    label: str | None

    color: str | None

    tag: list[BoxTagDict] | None


@dataclass(slots=True)
class BoxSeriesConfig:
    """
    Configuration for one box-and-whisker series.

    Parameters
    ----------
    ticker:
        DataFrame column used to construct the box.

    label:
        Display label used by the X-axis and legend. If None, the
        ticker is used.

    color:
        Box face color. If None, a palette color is assigned
        automatically.

    tag:
        Reference configurations associated with the series. Each
        reference can independently draw a label through ``self.tag()``
        and a marker through ``self.dot()``.
    """

    ticker: str

    label: str | None = None

    color: str | None = None

    tag: list[BoxTagDict] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.ticker, str):
            raise TypeError(
                "'ticker' must be a string."
            )

        if not self.ticker.strip():
            raise ValueError(
                "'ticker' cannot be empty."
            )

        if (
            self.label is not None
            and not isinstance(self.label, str)
        ):
            raise TypeError(
                "'label' must be a string or None."
            )

        if (
            self.color is not None
            and not isinstance(self.color, str)
        ):
            raise TypeError(
                "'color' must be a string or None."
            )

        if self.tag is None:
            return

        if not isinstance(self.tag, list):
            raise TypeError(
                "'tag' must be a list of dictionaries "
                "or None."
            )

        valid_modes = {
            "observation",
            "statistic",
        }

        valid_statistics = {
            "low",
            "high",
            "mean",
            "median",
            "q1",
            "q3",
        }

        for position, reference in enumerate(
            self.tag
        ):
            if not isinstance(reference, dict):
                raise TypeError(
                    "Each item inside 'tag' must be a "
                    "dictionary. Invalid item at position "
                    f"{position}."
                )

            mode = reference.get(
                "mode",
                (
                    "statistic"
                    if "statistic" in reference
                    else "observation"
                ),
            )

            if mode not in valid_modes:
                raise ValueError(
                    "'mode' must be 'observation' or "
                    f"'statistic'. Invalid item at position "
                    f"{position}."
                )

            statistic = reference.get(
                "statistic"
            )

            if (
                statistic is not None
                and statistic not in valid_statistics
            ):
                raise ValueError(
                    "'statistic' must be one of: "
                    "'low', 'high', 'mean', 'median', "
                    "'q1', or 'q3'. Invalid item at "
                    f"position {position}."
                )

            if (
                mode == "statistic"
                and statistic is None
            ):
                raise ValueError(
                    "A reference with mode='statistic' "
                    "must define 'statistic'. Invalid item "
                    f"at position {position}."
                )

            tag_config = reference.get("tag")

            if (
                tag_config is not None
                and not isinstance(tag_config, dict)
            ):
                raise TypeError(
                    "'tag' inside a box reference must be "
                    "a dictionary or None. Invalid item at "
                    f"position {position}."
                )

            dot_config = reference.get("dot")

            if (
                dot_config is not None
                and not isinstance(dot_config, dict)
            ):
                raise TypeError(
                    "'dot' inside a box reference must be "
                    "a dictionary or None. Invalid item at "
                    f"position {position}."
                )


BoxSeriesLike: TypeAlias = (
    BoxSeriesConfig
    | BoxSeriesDict
)