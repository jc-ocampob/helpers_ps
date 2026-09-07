from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeAlias, TypedDict

import numpy as np
import pandas as pd


XAxisHorizontalAlignment: TypeAlias = Literal[
    "left",
    "center",
    "right",
]

XAxisVerticalAlignment: TypeAlias = Literal[
    "top",
    "center",
    "bottom",
    "baseline",
    "center_baseline",
]

XAxisLimit: TypeAlias = tuple[Any | None, Any | None]

XAxisTickValues: TypeAlias = (
    list[Any]
    | tuple[Any, ...]
    | pd.Index
    | np.ndarray
)

XAxisTickLabels: TypeAlias = (
    list[str]
    | tuple[str, ...]
)

XAxisTickLabelMap: TypeAlias = dict[Any, str]


class XAxisDict(TypedDict, total=False):
    """
    Dictionary configuration accepted by ``prep_x_axis``.

    All fields are optional because ``XAxisConfig`` defines their
    default values.
    """

    bbg_format: bool

    tick_step: int

    fmt: str | None

    year_y_offset: float

    lim: XAxisLimit | None

    fontsize: float

    tick_values: XAxisTickValues | None

    tick_labels: XAxisTickLabels | None

    tick_label_map: XAxisTickLabelMap | None

    rotation: float

    ha: XAxisHorizontalAlignment

    va: XAxisVerticalAlignment

    label_color: str | None

    show_years: bool


@dataclass(slots=True)
class XAxisConfig:
    """
    Configuration used by ``prep_x_axis``.

    Parameters
    ----------
    bbg_format:
        Whether to use Bloomberg-style datetime formatting.

    tick_step:
        Frequency used when selecting visible ticks.

    fmt:
        Format string used for datetime or numeric labels.

    year_y_offset:
        Vertical offset used for Bloomberg-style year labels.

    lim:
        Optional lower and upper X-axis limits.

    fontsize:
        Font size applied to X-axis labels.

    tick_values:
        Explicit values used as visible ticks.

    tick_labels:
        Explicit labels assigned to visible ticks.

    tick_label_map:
        Mapping used to replace selected tick labels.

    rotation:
        Rotation applied to X-axis labels.

    ha:
        Horizontal alignment of X-axis labels.

    va:
        Vertical alignment of X-axis labels.

    label_color:
        Color applied to X-axis labels.

    show_years:
        Whether Bloomberg-style year labels are displayed.
    """

    bbg_format: bool = False

    tick_step: int = 6

    fmt: str | None = None

    year_y_offset: float = -0.08

    lim: XAxisLimit | None = None

    fontsize: float = 8

    tick_values: XAxisTickValues | None = None

    tick_labels: XAxisTickLabels | None = None

    tick_label_map: XAxisTickLabelMap | None = None

    rotation: float = 0

    ha: XAxisHorizontalAlignment = "center"

    va: XAxisVerticalAlignment = "top"

    label_color: str | None = None

    show_years: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.bbg_format, bool):
            raise TypeError(
                "'bbg_format' must be a boolean."
            )

        if not isinstance(self.tick_step, int):
            raise TypeError(
                "'tick_step' must be an integer."
            )

        if self.tick_step <= 0:
            raise ValueError(
                "'tick_step' must be greater than zero."
            )

        if (
            self.fmt is not None
            and not isinstance(self.fmt, str)
        ):
            raise TypeError(
                "'fmt' must be a string or None."
            )

        if not isinstance(
            self.year_y_offset,
            (int, float),
        ):
            raise TypeError(
                "'year_y_offset' must be numeric."
            )

        if self.lim is not None:
            if (
                not isinstance(self.lim, tuple)
                or len(self.lim) != 2
            ):
                raise TypeError(
                    "'lim' must be a tuple containing "
                    "exactly two values or None."
                )

        if not isinstance(
            self.fontsize,
            (int, float),
        ):
            raise TypeError(
                "'fontsize' must be numeric."
            )

        if self.fontsize <= 0:
            raise ValueError(
                "'fontsize' must be greater than zero."
            )

        if (
            self.tick_values is not None
            and not isinstance(
                self.tick_values,
                (
                    list,
                    tuple,
                    pd.Index,
                    np.ndarray,
                ),
            )
        ):
            raise TypeError(
                "'tick_values' must be a list, tuple, "
                "pandas Index, NumPy array, or None."
            )

        if (
            self.tick_labels is not None
            and not isinstance(
                self.tick_labels,
                (list, tuple),
            )
        ):
            raise TypeError(
                "'tick_labels' must be a list, tuple, "
                "or None."
            )

        if (
            self.tick_values is not None
            and self.tick_labels is not None
            and len(self.tick_values)
            != len(self.tick_labels)
        ):
            raise ValueError(
                "'tick_values' and 'tick_labels' must "
                "have the same length."
            )

        if (
            self.tick_label_map is not None
            and not isinstance(
                self.tick_label_map,
                dict,
            )
        ):
            raise TypeError(
                "'tick_label_map' must be a dictionary "
                "or None."
            )

        if not isinstance(
            self.rotation,
            (int, float),
        ):
            raise TypeError(
                "'rotation' must be numeric."
            )

        if self.ha not in {
            "left",
            "center",
            "right",
        }:
            raise ValueError(
                "'ha' must be 'left', 'center', "
                "or 'right'."
            )

        if self.va not in {
            "top",
            "center",
            "bottom",
            "baseline",
            "center_baseline",
        }:
            raise ValueError(
                "'va' contains an unsupported vertical "
                "alignment."
            )

        if (
            self.label_color is not None
            and not isinstance(
                self.label_color,
                str,
            )
        ):
            raise TypeError(
                "'label_color' must be a string or None."
            )

        if not isinstance(self.show_years, bool):
            raise TypeError(
                "'show_years' must be a boolean."
            )


XAxisLike: TypeAlias = (
    XAxisConfig
    | XAxisDict
)