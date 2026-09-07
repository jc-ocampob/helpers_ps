from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import TypeAlias
from typing import Any, Literal, TypeAlias, TypedDict


LineStyle: TypeAlias = str | tuple

LineTagDisplay: TypeAlias = Literal[
    "tag",
    "dot",
    "tag_dot",
]


class LineTagStyleDict(TypedDict, total=False):
    """
    Styling options passed to the `tag()` annotation method.
    """

    label_h_align: str
    label_v_align: str
    ubic_etq: tuple
    fontsize: int
    fontweight: str
    font_color: str
    bg_color: str
    bg_alpha: float
    edge_color: str
    show_bbox: bool
    text_edge_color: str | None
    text_edge_width: float
    zorder: int


class LineDotStyleDict(TypedDict, total=False):
    """
    Styling options passed to the `dot()` annotation method.
    """

    color: str
    size: float
    zorder: int


class LineTagConfigDict(TypedDict, total=False):
    """
    Configuration for one group of line annotations.

    Each configuration can contain one or more x-axis values.
    The corresponding y-axis values are obtained automatically
    from the series owned by `LineSeriesConfig`.
    """

    x_values: list[str | float | int | pd.Timestamp] | str | float | int | pd.Timestamp
    show: LineTagDisplay
    template: str
    tag: LineTagStyleDict
    dot: LineDotStyleDict
    legend_label: str


class LineSeriesDict(TypedDict, total=False):
    """
    Dictionary representation of a line series.

    Used to provide IDE autocomplete when users prefer
    dictionary syntax instead of dataclass instances.
    """

    ticker: str
    label: str
    color: str
    axis_side: str
    lw: float
    linestyle: LineStyle
    tags: list[LineTagConfigDict]


@dataclass(slots=True)
class LineSeriesConfig:
    """
    Configuration for a single line series.

    Parameters
    ----------
    ticker:
        DataFrame column associated with the series.

    label:
        Label displayed in the legend. If None, ticker is used.

    color:
        Line color. If None, a color is assigned automatically.

    axis_side:
        Axis where the series is plotted. Must be
        "left" or "right".

    lw:
        Series-specific line width. If None, the
        default line width defined in graph_line
        is used.

    linestyle:
        Matplotlib line style.
    """

    ticker: str
    label: str | None = None
    color: str | None = None
    axis_side: str = "left"
    lw: float | None = None
    linestyle: LineStyle = "-"
    tags: list[LineTagConfigDict] | None = None

    def __post_init__(self) -> None:
        self._validate_ticker()
        self._set_default_label()
        self._validate_axis_side()
        self._validate_line_width()
        self._validate_linestyle()
        self._validate_tags()

    def _validate_ticker(self) -> None:
        if not isinstance(self.ticker, str):
            raise TypeError(
                "'ticker' must be a string."
            )

        self.ticker = self.ticker.strip()

        if not self.ticker:
            raise ValueError(
                "'ticker' must be a non-empty string."
            )

    def _set_default_label(self) -> None:
        if self.label is None:
            self.label = self.ticker
            return

        if not isinstance(self.label, str):
            raise TypeError(
                "'label' must be a string or None."
            )

    def _validate_axis_side(self) -> None:
        valid_sides = {"left", "right"}

        if self.axis_side not in valid_sides:
            raise ValueError(
                "'axis_side' must be either 'left' or 'right'. "
                f"Received: {self.axis_side!r}."
            )

    def _validate_line_width(self) -> None:
        if self.lw is None:
            return

        if not isinstance(self.lw, (int, float)):
            raise TypeError(
                "'lw' must be numeric or None."
            )

        if self.lw <= 0:
            raise ValueError(
                "'lw' must be greater than zero."
            )

        self.lw = float(self.lw)

    def _validate_linestyle(self) -> None:
        if isinstance(self.linestyle, tuple):
            return

        if not isinstance(self.linestyle, str):
            raise TypeError(
                "'linestyle' must be a string or a Matplotlib "
                "dash-pattern tuple."
            )

        valid_linestyles = {
            "-",
            "--",
            "-.",
            ":",
            "solid",
            "dashed",
            "dashdot",
            "dotted",
        }

        if self.linestyle not in valid_linestyles:
            raise ValueError(
                "Invalid 'linestyle'. Expected one of "
                f"{sorted(valid_linestyles)} or a dash-pattern tuple. "
                f"Received: {self.linestyle!r}."
            )

    def _validate_tags(self) -> None:
        """
        Validate annotation configurations associated with the series.
        """

        if self.tags is None:
            return

        if not isinstance(self.tags, list):
            raise TypeError(
                "'tags' must be a list of dictionaries or None."
            )

        valid_show_values = {
            "tag",
            "dot",
            "tag_dot",
        }

        for position, tag_config in enumerate(self.tags):
            if not isinstance(tag_config, dict):
                raise TypeError(
                    "Each item in 'tags' must be a dictionary. "
                    f"Invalid item at position {position}."
                )

            x_values = tag_config.get("x_values")

            if x_values is None:
                raise ValueError(
                    "Each tag configuration must define 'x_values'. "
                    f"Missing at position {position}."
                )

            show = tag_config.get("show", "tag_dot")

            if show not in valid_show_values:
                raise ValueError(
                    "'show' must be 'tag', 'dot', or 'tag_dot'. "
                    f"Received {show!r} at position {position}."
                )


LineSeriesLike: TypeAlias = (
    LineSeriesConfig |
    LineSeriesDict
)