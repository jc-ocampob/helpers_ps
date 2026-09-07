from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias, TypedDict


BarAxisSide: TypeAlias = Literal[
    "left",
    "right",
]

BarTagMode: TypeAlias = Literal[
    "value_label",
    "bar_tag",
    "stack_total",
]

BarTagXValue: TypeAlias = (
    str
    | int
    | float
)

BarTagXValues: TypeAlias = (
    Literal["all", "last"]
    | BarTagXValue
    | list[BarTagXValue]
    | tuple[BarTagXValue, ...]
    | set[BarTagXValue]
)


class BarTagDict(TypedDict, total=False):
    """
    Configuration for a bar-series tag.

    All fields are optional. When omitted:

    - ``show`` defaults to ``"value_label"``.
    - ``x_values`` defaults to ``"last"``.
    - ``template`` defaults to ``"{y_value:,.2f}"``.
    """

    show: BarTagMode

    x_values: BarTagXValues

    template: str

    ubic_etq: tuple[float, float] | None

    label_v_align: Literal[
        "top",
        "center",
        "bottom",
        "baseline",
        "center_baseline",
    ]

    label_h_align: Literal[
        "left",
        "center",
        "right",
    ]

    fontsize: float

    color: str

    fontweight: str | int

    fontstyle: Literal[
        "normal",
        "italic",
        "oblique",
    ]

    rotation: float

    alpha: float

    bbox: dict[str, object]

    arrowprops: dict[str, object]

    zorder: float

    clip_on: bool


@dataclass(slots=True)
class BarSeriesConfig:
    """
    Configuration for a single bar-chart series.

    Parameters
    ----------
    ticker:
        DataFrame column plotted by the series.

    label:
        Display label used by the legend and tags. If None, the
        ticker is used as the default label.

    color:
        Color assigned to the bar series. If None, a color is
        assigned automatically from PALETA_COLORES.

    axis_side:
        Y-axis used by the series.

    tag:
        Tag configurations applied to the bar series. Each item can
        generate value labels, tags centered inside bars, or stacked
        bar totals.
    """

    ticker: str

    label: str | None = None

    color: str | None = None

    axis_side: BarAxisSide = "left"

    tag: list[BarTagDict] | None = None

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

        if self.axis_side not in {
            "left",
            "right",
        }:
            raise ValueError(
                "'axis_side' must be either "
                "'left' or 'right'."
            )

        if self.tag is None:
            return

        if not isinstance(self.tag, list):
            raise TypeError(
                "'tag' must be a list of dictionaries "
                "or None."
            )

        valid_tag_modes = {
            "value_label",
            "bar_tag",
            "stack_total",
        }

        for position, tag_config in enumerate(
            self.tag
        ):
            if not isinstance(tag_config, dict):
                raise TypeError(
                    "Each item in 'tag' must be a "
                    "dictionary. Invalid item at "
                    f"position {position}."
                )

            show = tag_config.get(
                "show",
                "value_label",
            )

            if show not in valid_tag_modes:
                raise ValueError(
                    "'show' in tag configuration must "
                    "be one of: 'value_label', "
                    "'bar_tag', or 'stack_total'. "
                    f"Invalid item at position {position}."
                )

            template = tag_config.get("template")

            if (
                template is not None
                and not isinstance(template, str)
            ):
                raise TypeError(
                    "'template' in tag configuration "
                    "must be a string. Invalid item at "
                    f"position {position}."
                )

            offset = tag_config.get("ubic_etq")

            if offset is not None:
                if (
                    not isinstance(offset, tuple)
                    or len(offset) != 2
                    or not all(
                        isinstance(value, (int, float))
                        for value in offset
                    )
                ):
                    raise TypeError(
                        "'ubic_etq' must be a tuple with "
                        "two numeric values. Invalid item "
                        f"at position {position}."
                    )


class BarSeriesDict(TypedDict):
    """
    Normalized dictionary representation of a bar series.
    """

    ticker: str

    label: str | None

    color: str | None

    axis_side: BarAxisSide

    tag: list[BarTagDict] | None


BarSeriesLike: TypeAlias = (
    BarSeriesConfig
    | BarSeriesDict
)